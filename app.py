import streamlit as st
import json
import config
from utils.embeddings import JobMatcher
from utils.claude_helper import ClaudeAssistant


def clear_embeddings_cache():
    """Clear old embeddings when model changes (run once!)"""
    import os
    index_file = "data/jobs_index.faiss"
    embeddings_file = "data/job_embeddings.npy"
    
    if os.path.exists(index_file):
        os.remove(index_file)
        st.write("✅ Removed old FAISS index")
        print("✅ Removed old FAISS index")
    
    if os.path.exists(embeddings_file):
        os.remove(embeddings_file)
        st.write("✅ Removed old embeddings")
        print("✅ Removed old embeddings")
    
    st.write("🔄 New embeddings will be created with BERT model...")

# Page config
st.set_page_config(
    page_title=config.APP_TITLE,
    page_icon=config.APP_ICON,
    layout="wide"
)

# Initialize session state
if 'job_matcher' not in st.session_state:
    st.session_state.job_matcher = None
if 'claude_assistant' not in st.session_state:
    try:
        st.session_state.claude_assistant = ClaudeAssistant()
    except ValueError as e:
        st.session_state.claude_assistant = None
        st.session_state.api_error = str(e)
if 'matches' not in st.session_state:
    st.session_state.matches = None
if 'resume_text' not in st.session_state:
    st.session_state.resume_text = None
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

# NEW - Role selection flow
if 'selected_roles' not in st.session_state:
    st.session_state.selected_roles = []
if 'current_step' not in st.session_state:
    st.session_state.current_step = 1  # 1=Select Roles, 2=Upload Resume, 3=Results
if 'parsed_resume_data' not in st.session_state:
    st.session_state.parsed_resume_data = None

# Load jobs
@st.cache_data
def load_jobs():
    with open(config.JOBS_FILE, 'r') as f:
        return json.load(f)

# Initialize job matcher with DEBUG
@st.cache_resource
def initialize_matcher(jobs):
    """Initialize matcher and show DEBUG info"""
    with st.spinner("🤖 Loading BERT model and creating embeddings..."):
        matcher = JobMatcher()
        matcher.build_job_index(jobs)
        
        # DEBUG: Show model info
        st.success(f"🔍 DEBUG: Model loaded = {config.EMBEDDING_MODEL}")
        print(f"🔍 DEBUG: Model = {config.EMBEDDING_MODEL}")
        
        # DEBUG: Show embedding dimensions
        if matcher.index:
            dims = matcher.index.d
            st.success(f"🔍 DEBUG: Embedding dimensions = {dims} (768 = BERT, 384 = old model)")
            print(f"🔍 DEBUG: Dimensions = {dims}")
            
            if dims == 768:
                st.success("✅ BERT MODEL IS RUNNING! (768 dimensions)")
            else:
                st.warning("⚠️ Old model still cached! (384 dimensions)")
        
        return matcher

def load_css():
    """Load external CSS file"""
    with open('static/styles.css') as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

def main():
    # Load CSS
    load_css()
    
    # Your existing title and content
    st.title("🎯 JobRight AI - Smart Job Matching")
    st.markdown("*AI-Powered Resume Optimization & ML-Based Job Matching*")
    st.markdown("---")
    
    # ... rest of your code

def main():
    # CRITICAL: Clear cache ONCE to switch to BERT
    # Uncomment next 3 lines, run ONCE, then comment out again!
    
    with st.sidebar:
       clear_embeddings_cache()
    
    st.title("🎯 JobRight AI - Smart Job Matching")
    st.markdown("*AI-Powered Resume Optimization & ML-Based Job Matching*")
    st.markdown("---")
    
    # Sidebar with navigation
    with st.sidebar:
        st.header("⚙️ Navigation")
        
        # Show current step
        if st.session_state.current_step == 1:
            st.info("📍 Step 1: Select Roles")
        elif st.session_state.current_step == 2:
            st.info("📍 Step 2: Upload Resume")
        elif st.session_state.current_step == 3:
            st.info("📍 Step 3: View Results")
        
        st.markdown("---")
        
        # Reset button
        if st.button("🔄 Start Over", use_container_width=True):
            st.session_state.current_step = 1
            st.session_state.selected_roles = []
            st.session_state.matches = None
            st.session_state.resume_text = None
            st.session_state.parsed_resume_data = None
            st.rerun()
        
        st.markdown("---")
        
        # API Status
        if st.session_state.claude_assistant:
            st.success("✅ Claude AI: Connected")
        else:
            st.error("❌ Claude AI: Not configured")
            if hasattr(st.session_state, 'api_error'):
                st.caption(st.session_state.api_error)
        
        st.markdown("---")
        st.caption("💡 AI used only for resume optimization")
        st.caption("🤖 ML used for job matching")
    
    # Route to correct page based on current step
    if st.session_state.current_step == 1:
        show_role_selection()
    elif st.session_state.current_step == 2:
        show_resume_upload()
    elif st.session_state.current_step == 3:
        show_job_results()

def show_role_selection():
    """Phase 1: Role Selection with Search"""
    
    st.header("🎯 Step 1: What roles are you interested in?")
    st.markdown("Select or search for job roles you want to match against your resume.")
    
    # Search box
    search_query = st.text_input(
        "🔍 Search roles",
        placeholder="Type to search (e.g., 'machine', 'software', 'data')...",
        help="Start typing to filter roles"
    )
    
    # Filter roles based on search
    if search_query:
        filtered_roles = [
            role for role in config.JOB_ROLES 
            if search_query.lower() in role.lower()
        ]
    else:
        filtered_roles = config.JOB_ROLES
    
    st.markdown("---")
    
    # Display available roles
    if filtered_roles:
        st.subheader("📋 Available Roles")
        st.caption(f"Showing {len(filtered_roles)} role(s)")
        
        # Create columns for better layout
        cols = st.columns(2)
        
        for idx, role in enumerate(filtered_roles):
            with cols[idx % 2]:
                # Check if role is already selected
                is_selected = role in st.session_state.selected_roles
                
                # Checkbox for each role
                if st.checkbox(
                    role,
                    value=is_selected,
                    key=f"role_{role}"
                ):
                    # Add to selected if checked
                    if role not in st.session_state.selected_roles:
                        st.session_state.selected_roles.append(role)
                else:
                    # Remove from selected if unchecked
                    if role in st.session_state.selected_roles:
                        st.session_state.selected_roles.remove(role)
    else:
        st.warning("No roles found matching your search. Try different keywords!")
    
    st.markdown("---")
    
    # Show selected roles
    if st.session_state.selected_roles:
        st.success(f"✅ Selected {len(st.session_state.selected_roles)} role(s):")
        
        # Display selected roles as pills/badges
        selected_html = ""
        for role in st.session_state.selected_roles:
            selected_html += f"""
            <span style="
                display: inline-block;
                background-color: #1f77b4;
                color: white;
                padding: 5px 15px;
                margin: 5px;
                border-radius: 20px;
                font-size: 14px;
            ">{role}</span>
            """
        st.markdown(selected_html, unsafe_allow_html=True)
        
        st.markdown("")
        
        # Continue button
        if st.button("📄 Continue to Upload Resume →", type="primary", use_container_width=True):
            st.session_state.current_step = 2
            st.rerun()
    else:
        st.info("👆 Please select at least one role to continue")

def show_resume_upload():
    """Phase 2: Resume Upload and Parsing (NO AI)"""
    
    st.header("📄 Step 2: Upload Your Resume")
    st.markdown("Upload your resume to match against selected roles using ML-powered semantic search.")
    
    # Show selected roles as reminder
    st.info(f"🎯 Searching for: {', '.join(st.session_state.selected_roles)}")
    
    st.markdown("---")
    
    # File uploader
    uploaded_file = st.file_uploader(
        "Choose your resume file",
        type=['pdf', 'docx', 'txt'],
        help="Supported formats: PDF, DOCX, TXT"
    )
    
    if uploaded_file:
        st.success(f"✅ File uploaded: **{uploaded_file.name}**")
        
        # Check if already parsed
        if st.session_state.parsed_resume_data is None:
            # Parse button (only show if not yet parsed)
            col1, col2 = st.columns([3, 1])
            
            with col1:
                if st.button("🤖 Parse & Analyze Resume (ML)", type="primary", use_container_width=True):
                    
                    from utils.resume_parser import ResumeParser
                    from utils.resume_analyzer import ResumeAnalyzer
                    
                    with st.spinner("📖 Parsing resume using pattern matching (no AI)..."):
                        try:
                            # Step 1: Extract text from file
                            resume_text = ResumeParser.parse_resume(uploaded_file)
                            st.session_state.resume_text = resume_text
                            
                            # Step 2: Analyze with ML patterns (NO AI)
                            analyzer = ResumeAnalyzer()
                            parsed_data = analyzer.parse_resume(resume_text)
                            st.session_state.parsed_resume_data = parsed_data
                            
                            st.success("✅ Resume parsed successfully!")
                            st.rerun()  # Rerun to show the parsed data
                        
                        except Exception as e:
                            st.error(f"❌ Error parsing resume: {str(e)}")
            
            with col2:
                st.caption("Uses regex & ML patterns")
        
        else:
            # Already parsed - show summary
            parsed_data = st.session_state.parsed_resume_data
            
            st.markdown("---")
            st.subheader("📊 Parsing Summary")
            
            col_a, col_b, col_c, col_d = st.columns(4)
            
            with col_a:
                st.metric("Skills Found", len(parsed_data['skills']))
            
            with col_b:
                st.metric("Experience", f"{parsed_data['years_of_experience']} yrs")
            
            with col_c:
                edu_text = parsed_data['education'].get('level', 'Found')
                st.metric("Education", edu_text)
            
            with col_d:
                st.metric("Projects", len(parsed_data['projects']))
            
            # Detailed view
            with st.expander("🔍 View Extracted Data", expanded=True):
                st.markdown("**🛠️ Skills:**")
                if parsed_data['skills']:
                    # Display as pills
                    skills_html = ""
                    for skill in parsed_data['skills'][:20]:  # Show top 20
                        skills_html += f'<span style="background-color: #28a745; color: white; padding: 3px 10px; margin: 3px; border-radius: 12px; font-size: 12px; display: inline-block;">{skill}</span>'
                    st.markdown(skills_html, unsafe_allow_html=True)
                else:
                    st.caption("No skills detected")
                
                st.markdown("")
                st.markdown(f"**🎓 Education:** {parsed_data['education']['summary']}")
                
                st.markdown("")
                st.markdown(f"**💼 Experience:** {parsed_data['years_of_experience']} years")
                
                st.markdown("")
                st.markdown("**📋 Projects:**")
                if parsed_data['projects']:
                    for i, project in enumerate(parsed_data['projects'][:5], 1):
                        st.markdown(f"{i}. **{project['title']}**")
                        st.caption(project['description'])
                else:
                    st.caption("No projects detected")
            
            st.markdown("---")
            
            # Continue button (ALWAYS VISIBLE after parsing)
            col_btn1, col_btn2 = st.columns([2, 1])
            
            with col_btn1:
                if st.button("🚀 Find Matching Jobs →", type="primary", use_container_width=True):
                    st.session_state.current_step = 3
                    st.rerun()
            
            with col_btn2:
                if st.button("🔄 Re-parse Resume"):
                    st.session_state.parsed_resume_data = None
                    st.session_state.resume_text = None
                    st.rerun()
    
    else:
        st.info("👆 Please upload your resume to continue")
    
    st.markdown("---")
    
    # Back button
    if st.button("← Back to Role Selection"):
        st.session_state.current_step = 1
        st.rerun()

def show_job_results():
    """Phase 3: Filtered Job Results with ML Matching"""
    
    st.header("✨ Your Matched Jobs")
    st.markdown(f"🎯 Filtered for: **{', '.join(st.session_state.selected_roles)}**")
    st.markdown("🤖 Powered by ML: Sentence Transformers + Vector Similarity")
    
    # Load jobs
    jobs = load_jobs()
    
    # Initialize job matcher
    if st.session_state.job_matcher is None:
        st.session_state.job_matcher = initialize_matcher(jobs)
    
    # Filter jobs by selected roles
    with st.spinner("🔍 Filtering jobs by your selected roles..."):
        filtered_jobs = []
        for job in jobs:
            # Check if job title matches any selected role
            for role in st.session_state.selected_roles:
                if role.lower() in job['title'].lower():
                    filtered_jobs.append(job)
                    break
    
    if not filtered_jobs:
        st.warning("😕 No jobs found matching your selected roles. Try selecting different roles!")
        if st.button("← Back to Role Selection"):
            st.session_state.current_step = 1
            st.rerun()
        return
    
    # ML Matching
    with st.spinner("🤖 ML is analyzing your resume against jobs..."):
        from utils.resume_analyzer import ResumeAnalyzer
        
        analyzer = ResumeAnalyzer()
        resume_data = st.session_state.parsed_resume_data
        
        # Create matches with SMART SCORING
        matches = []
        for job in filtered_jobs:
            # Step 1: Get ML semantic similarity from embeddings
            profile = {
                "title": " ".join(st.session_state.selected_roles),
                "skills": " ".join(resume_data.get('skills', [])),
                "experience": resume_data.get('full_text', '')
            }
            
            ml_matches = st.session_state.job_matcher.find_matching_jobs(profile, top_k=len(filtered_jobs))
            
            # Find this job's ML semantic score
            ml_semantic_score = 0.5  # default
            for matched_job, score in ml_matches:
                if matched_job['id'] == job['id']:
                    ml_semantic_score = score
                    break
            
            # Step 2: Calculate SMART SCORE (hybrid ML + rules)
            smart_score_result = analyzer.calculate_smart_score(resume_data, job, ml_semantic_score)
            final_score = smart_score_result['final_score']
            
            # Step 3: Calculate detailed breakdown for UI
            breakdown = analyzer.calculate_detailed_breakdown(resume_data, job)
            
            # Add smart score info to breakdown
            breakdown['smart_score'] = smart_score_result
            breakdown['overall'] = final_score  # Override with smart score
            
            matches.append((job, final_score, breakdown))
        
        # Sort by SMART SCORE (not just ML score!)
        matches.sort(key=lambda x: x[1], reverse=True)  # x[1] is the final_score
    
    st.success(f"✅ Found **{len(matches)}** matching jobs!")
    st.markdown("---")
    
    # Display results
    for i, (job, ml_score, breakdown) in enumerate(matches, 1):
        overall_score = breakdown['overall']
        
        # Color coding
        if overall_score >= 0.75:
            badge = "🟢"
            strength = "STRONG"
        elif overall_score >= 0.60:
            badge = "🟡"
            strength = "GOOD"
        elif overall_score >= 0.45:
            badge = "🟠"
            strength = "MODERATE"
        else:
            badge = "🔴"
            strength = "NEEDS WORK"
        
        # Job card
        with st.container():
            col_main, col_score = st.columns([4, 1])
            
            with col_main:
                st.markdown(f"### {badge} #{i} - {job['title']}")
                st.caption(f"**{job['company']}** • {job['location']} • {job['salary']}")
            
            with col_score:
                st.metric("Match", f"{overall_score*100:.0f}%")
                st.caption(strength)
            
            # Buttons
            col_btn1, col_btn2, col_btn3 = st.columns(3)
            
            with col_btn1:
                if st.button(f"📊 View Breakdown", key=f"view_{job['id']}", use_container_width=True):
                    st.session_state[f"show_modal_{job['id']}"] = True
                    st.session_state[f"show_optimize_{job['id']}"] = False
                    st.session_state[f"show_details_{job['id']}"] = False
            
            with col_btn2:
                if st.button(f"📄 Job Details", key=f"details_{job['id']}", use_container_width=True):
                    st.session_state[f"show_details_{job['id']}"] = True
                    st.session_state[f"show_modal_{job['id']}"] = False
                    st.session_state[f"show_optimize_{job['id']}"] = False
            
            with col_btn3:
                if st.button(f"✨ Optimize Resume", key=f"optimize_btn_{job['id']}", use_container_width=True):
                    st.session_state[f"show_optimize_{job['id']}"] = True
                    st.session_state[f"show_modal_{job['id']}"] = False
                    st.session_state[f"show_details_{job['id']}"] = False
        
        # MODAL 1: Breakdown
        if st.session_state.get(f"show_modal_{job['id']}", False):
            with st.expander("📊 Detailed Breakdown", expanded=True):
                st.markdown(f"### {job['title']} at {job['company']}")
                st.markdown(f"**Overall Match: {overall_score*100:.0f}%**")
                st.markdown("---")
                
                # 4 Category Breakdown
                col_a, col_b, col_c, col_d = st.columns(4)
                
                with col_a:
                    skills_pct = breakdown['skills']['score'] * 100
                    st.metric("🛠️ Skills", f"{skills_pct:.0f}%")
                
                with col_b:
                    edu_pct = breakdown['education']['score'] * 100
                    st.metric("🎓 Education", f"{edu_pct:.0f}%")
                
                with col_c:
                    exp_pct = breakdown['experience']['score'] * 100
                    st.metric("💼 Experience", f"{exp_pct:.0f}%")
                
                with col_d:
                    proj_pct = breakdown['projects']['score'] * 100
                    st.metric("📋 Projects", f"{proj_pct:.0f}%")
                
                st.markdown("---")
                
                # Detailed info for each category
                st.markdown("#### 🛠️ Skills Analysis")
                st.write(f"**Matched:** {breakdown['skills']['matched']} out of {breakdown['skills']['total']} skills")
                if breakdown['skills']['missing']:
                    st.warning(f"**Missing:** {', '.join(breakdown['skills']['missing'][:5])}")
                
                st.markdown("#### 🎓 Education Analysis")
                st.write(f"**You have:** {breakdown['education']['candidate']}")
                st.write(f"**Required:** {breakdown['education']['required']}")
                
                st.markdown("#### 💼 Experience Analysis")
                st.write(f"**You have:** {breakdown['experience']['candidate_years']} years")
                st.write(f"**Required:** {breakdown['experience']['required_years']}+ years")
                if breakdown['experience']['gap'] > 0:
                    st.warning(f"**Gap:** Need {breakdown['experience']['gap']} more years")
                
                st.markdown("#### 📋 Projects Analysis")
                st.write(f"**Detected:** {breakdown['projects']['count']} projects")
                st.write(f"**Preferred:** {breakdown['projects']['required']}")
                
                st.markdown("---")

                # Smart Score Breakdown
                if 'smart_score' in breakdown:
                    st.markdown("---")
                    st.markdown("#### 🧠 Smart Score Breakdown")
                    st.caption("How we calculated your match score using ML + Rules")
                    
                    smart = breakdown['smart_score']
                    
                    col_smart1, col_smart2 = st.columns(2)
                    
                    with col_smart1:
                        st.markdown("**Score Components:**")
                        st.write(f"✓ Exact Skills Match: {smart['breakdown']['exact_skills']*100:.0f}%")
                        st.write(f"✓ Related Skills: {smart['breakdown']['related_skills']*100:.0f}%")
                        st.write(f"✓ Experience Match: {smart['breakdown']['experience']*100:.0f}%")
                    
                    with col_smart2:
                        st.markdown("**Weights Applied:**")
                        st.write(f"• Skills: {smart['weights']['skills_total']*100:.0f}%")
                        st.write(f"• Experience: {smart['weights']['experience']*100:.0f}%")
                        st.write(f"• ML Semantic: {smart['weights']['semantic']*100:.0f}%")
                    
                    st.caption(f"🎯 Final Weighted Score: **{smart['final_score']*100:.0f}%**")
                
                st.markdown("---")
                
                if st.button("❌ Close", key=f"close_{job['id']}"):
                    st.session_state[f"show_modal_{job['id']}"] = False
                    st.rerun()
        
        # MODAL 2: Job Details
        if st.session_state.get(f"show_details_{job['id']}", False):
            with st.expander("📄 Full Job Details", expanded=True):
                st.markdown(f"### {job['title']}")
                st.markdown(f"**{job['company']}**")
                st.markdown("---")
                
                col_det1, col_det2 = st.columns(2)
                
                with col_det1:
                    st.markdown(f"**📍 Location:** {job['location']}")
                    st.markdown(f"**💼 Type:** {job['type']}")
                    st.markdown(f"**💰 Salary:** {job['salary']}")
                
                with col_det2:
                    st.markdown(f"**📊 Experience:** {job['experience']} years")
                    st.markdown(f"**🌍 Visa:** {'✅ Yes' if job.get('visa_sponsorship') else '❌ No'}")
                    st.markdown(f"**🎯 Match:** {overall_score*100:.0f}%")
                
                st.markdown("---")
                st.markdown("**📝 Job Description:**")
                st.write(job['description'])
                
                st.markdown("**✅ Requirements:**")
                st.write(job['requirements'])
                
                st.markdown("**🎓 Education Required:**")
                st.write(job.get('education_required', 'Not specified'))
                
                st.markdown("**📋 Projects/Portfolio:**")
                st.write(job.get('projects_required', 'Not specified'))
                
                st.markdown("---")
                
                if st.button("❌ Close", key=f"close_details_{job['id']}"):
                    st.session_state[f"show_details_{job['id']}"] = False
                    st.rerun()
        
        # MODAL 3: Optimize Resume
        if st.session_state.get(f"show_optimize_{job['id']}", False):
            with st.expander("✨ AI Resume Optimization", expanded=True):
                st.markdown(f"### Optimize Resume for: {job['title']}")
                st.markdown(f"**{job['company']}** • {job['location']}")
                st.markdown("---")
                
                # Check if Claude is available
                if not st.session_state.claude_assistant:
                    st.error("⚠️ Claude AI is not configured. Please add your API key to .env file.")
                    if st.button("❌ Close", key=f"close_opt_error_{job['id']}"):
                        st.session_state[f"show_optimize_{job['id']}"] = False
                        st.rerun()
                else:
                    # Show current breakdown
                    st.markdown("**📊 Current Match Analysis:**")
                    col_x, col_y, col_z, col_w = st.columns(4)
                    with col_x:
                        st.metric("Skills", f"{breakdown['skills']['score']*100:.0f}%")
                    with col_y:
                        st.metric("Education", f"{breakdown['education']['score']*100:.0f}%")
                    with col_z:
                        st.metric("Experience", f"{breakdown['experience']['score']*100:.0f}%")
                    with col_w:
                        st.metric("Projects", f"{breakdown['projects']['score']*100:.0f}%")
                    
                    st.markdown("---")
                    
                    # Check if already optimized
                    if not st.session_state.get(f"optimized_{job['id']}", None):
                        # Generate button
                        if st.button(f"🤖 Generate Optimized Resume with AI", key=f"gen_opt_{job['id']}", type="primary", use_container_width=True):
                            
                            with st.spinner("🤖 AI is optimizing your resume... This may take 10-20 seconds..."):
                                result = st.session_state.claude_assistant.optimize_resume_with_diff(
                                    st.session_state.resume_text,
                                    job,
                                    breakdown
                                )
                            
                            if result['success']:
                                # Store result in session state
                                st.session_state[f"optimized_{job['id']}"] = result
                                st.success("✅ Resume optimized successfully!")
                                st.rerun()
                            else:
                                st.error(f"❌ Error: {result.get('error', 'Unknown error')}")
                    
                    # Show optimized resume if generated
                    if st.session_state.get(f"optimized_{job['id']}", None):
                        result = st.session_state[f"optimized_{job['id']}"]
                        
                        st.success("✅ Optimization Complete!")
                        st.markdown("---")
                        
                        # Show changes made
                        st.markdown("**🔍 Changes Made by AI:**")
                        for i_change, change in enumerate(result['changes'], 1):
                            st.markdown(f"**{i_change}.** {change}")
                        
                        st.markdown("---")
                        
                        # Tabs for before/after
                        tab1, tab2, tab3 = st.tabs(["📄 Optimized Resume", "📋 Original Resume", "🔄 Side-by-Side"])
                        
                        with tab1:
                            st.markdown("**✨ Your optimized resume (AI-enhanced):**")
                            st.text_area(
                                "Optimized Resume",
                                result['optimized_resume'],
                                height=400,
                                label_visibility="collapsed",
                                key=f"opt_text_{job['id']}"
                            )
                            
                            # Download button
                            st.download_button(
                                label="📥 Download Optimized Resume",
                                data=result['optimized_resume'],
                                file_name=f"optimized_resume_{job['company'].replace(' ', '_')}.txt",
                                mime="text/plain",
                                use_container_width=True,
                                key=f"download_{job['id']}"
                            )
                        
                        with tab2:
                            st.markdown("**📋 Your original resume:**")
                            st.text_area(
                                "Original Resume",
                                st.session_state.resume_text,
                                height=400,
                                label_visibility="collapsed",
                                key=f"orig_text_{job['id']}"
                            )
                        
                        with tab3:
                            st.markdown("**🔄 Compare side-by-side:**")
                            
                            col_before, col_after = st.columns(2)
                            
                            with col_before:
                                st.markdown("**📋 Original**")
                                st.text_area(
                                    "Original",
                                    st.session_state.resume_text,
                                    height=350,
                                    label_visibility="collapsed",
                                    key=f"comp_orig_{job['id']}"
                                )
                            
                            with col_after:
                                st.markdown("**✨ Optimized**")
                                st.text_area(
                                    "Optimized",
                                    result['optimized_resume'],
                                    height=350,
                                    label_visibility="collapsed",
                                    key=f"comp_opt_{job['id']}"
                                )
                    
                    st.markdown("---")
                    
                    # Close button
                    col_close_btns = st.columns([3, 1])
                    with col_close_btns[1]:
                        if st.button("❌ Close", key=f"close_optimize_{job['id']}"):
                            st.session_state[f"show_optimize_{job['id']}"] = False
                            st.rerun()
        
        # Separator between jobs
        st.markdown("---")
    
    # Back button
    if st.button("← Back to Resume Upload"):
        st.session_state.current_step = 2
        st.rerun()

if __name__ == "__main__":
    main()
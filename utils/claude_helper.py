from anthropic import Anthropic
from typing import Dict
import config

class ClaudeAssistant:
    """Claude AI integration for job insights"""
    
    def __init__(self):
        if not config.ANTHROPIC_API_KEY:
            raise ValueError("⚠️ ANTHROPIC_API_KEY not found in .env file!")
        
        # Initialize Anthropic client (simplified)
        self.client = Anthropic(
            api_key=config.ANTHROPIC_API_KEY
        )
        self.model = config.CLAUDE_MODEL
    
    def explain_job_fit(self, user_profile: dict, job: dict, match_score: float) -> str:
        """Generate AI explanation of why user fits the job"""
        
        # Build the prompt
        prompt = f"""You are a career advisor AI. Analyze why this candidate matches this job.

CANDIDATE PROFILE:
- Desired Role: {user_profile.get('title', 'Not specified')}
- Skills: {user_profile.get('skills', 'Not specified')}
- Experience: {user_profile.get('experience', 'Not specified')}

JOB POSTING:
- Title: {job['title']}
- Company: {job['company']}
- Requirements: {job['requirements']}
- Description: {job['description']}

AI MATCH SCORE: {match_score*100:.1f}%

Provide a concise analysis (3-4 paragraphs) covering:
1. **Why This is a Good Match**: Key alignments between candidate and role
2. **Strengths to Highlight**: Top 3-4 specific qualifications that stand out
3. **Potential Gaps**: Any areas where the candidate could strengthen their application (be honest but constructive)
4. **Action Items**: 1-2 specific recommendations for the application/interview

Be encouraging but realistic. Use a professional, friendly tone."""

        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=1024,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            return message.content[0].text
            
        except Exception as e:
            return f"⚠️ Error getting AI insights: {str(e)}"
    
    def quick_tip(self, job_title: str) -> str:
        """Get a quick interview tip for a specific role"""
        
        prompt = f"""Give ONE specific, actionable interview tip for someone interviewing for a {job_title} position. 
        
Keep it to 2-3 sentences max. Be practical and specific."""
        
        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=150,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            return message.content[0].text
            
        except Exception as e:
            return "Prepare specific examples of your past work!"
    
    def optimize_resume(self, resume_text: str, job: dict) -> str:
        """Tailor resume to match specific job posting"""
        
        prompt = f"""You are an expert resume optimizer and ATS (Applicant Tracking System) specialist.

Given the following resume and job posting, create an optimized version of the resume that:
1. Highlights relevant skills and experiences that match the job requirements
2. Uses keywords from the job description naturally (ATS-friendly)
3. Improves impact statements with metrics where possible
4. Maintains truthfulness (don't add fake experience)
5. Is well-formatted and professional

ORIGINAL RESUME:
{resume_text}

JOB POSTING:
Title: {job['title']}
Company: {job['company']}
Requirements: {job['requirements']}
Description: {job['description']}

Please provide the optimized resume. Focus on making it highly relevant to this specific role while keeping all information truthful."""

        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=3000,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            return message.content[0].text
            
        except Exception as e:
            return f"⚠️ Error optimizing resume: {str(e)}"
        
    def career_chat(self, user_message: str, conversation_history: list = None) -> str:
        """Interactive career coaching chatbot"""
        
        system_prompt = """You are Orion, an expert AI career coach and advisor. You help job seekers with:

- Resume and cover letter advice
- Interview preparation and tips
- Career planning and job search strategy
- LinkedIn profile optimization
- Salary negotiation
- Networking advice
- Career transitions

Be friendly, supportive, and actionable. Keep responses concise (2-4 paragraphs) unless the user asks for detailed information. Provide specific, practical advice."""

        # Build messages list
        if conversation_history is None:
            conversation_history = []
        
        messages = conversation_history + [{"role": "user", "content": user_message}]
        
        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=1024,
                system=system_prompt,
                messages=messages
            )
            
            return message.content[0].text
            
        except Exception as e:
            return f"⚠️ Error: {str(e)}"
        
    def optimize_resume_with_diff(self, resume_text: str, job: Dict, breakdown: Dict) -> Dict:
        """
        AI-powered resume optimization with change tracking
        Returns both optimized version and list of changes made
        """
        
        # Build context for Claude
        skills_pct = breakdown['skills']['score'] * 100
        edu_pct = breakdown['education']['score'] * 100
        exp_pct = breakdown['experience']['score'] * 100
        proj_pct = breakdown['projects']['score'] * 100
        
        missing_skills = breakdown['skills']['missing']
        
        prompt = f"""You are an expert resume optimizer. Optimize this resume for the specific job below.

CURRENT RESUME:
{resume_text}

TARGET JOB:
Title: {job['title']}
Company: {job['company']}
Requirements: {job['requirements']}
Description: {job['description']}

ANALYSIS:
- Skills Match: {skills_pct:.0f}%
- Education Match: {edu_pct:.0f}%
- Experience Match: {exp_pct:.0f}%
- Projects Match: {proj_pct:.0f}%
- Missing Skills: {', '.join(missing_skills) if missing_skills else 'None'}

INSTRUCTIONS:
1. Keep all information truthful - DO NOT fabricate experience or skills
2. Rewrite and reorder to highlight the most relevant experience for THIS job
3. Add keywords from job requirements naturally (for ATS optimization)
4. Quantify achievements where possible (use numbers/metrics)
5. Emphasize skills that match the job requirements
6. Make it ATS-friendly and professional

IMPORTANT: After the optimized resume, add a section called "### CHANGES MADE:" and list 5-7 specific changes you made in bullet points.

Format:
[OPTIMIZED RESUME TEXT HERE]

### CHANGES MADE:
- Changed X to Y to better highlight...
- Added keyword "Z" for ATS optimization...
- Reordered sections to emphasize...
- etc.

Provide the complete optimized resume followed by the changes list."""

        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            response_text = message.content[0].text
            
            # Split into resume and changes
            if "### CHANGES MADE:" in response_text:
                parts = response_text.split("### CHANGES MADE:")
                optimized_resume = parts[0].strip()
                changes_section = parts[1].strip()
                
                # Extract bullet points from changes
                changes = []
                for line in changes_section.split('\n'):
                    line = line.strip()
                    if line.startswith('-') or line.startswith('•'):
                        changes.append(line[1:].strip())
                    elif line and not line.startswith('#'):
                        changes.append(line)
                
                return {
                    "optimized_resume": optimized_resume,
                    "changes": changes[:7],  # Top 7 changes
                    "success": True
                }
            else:
                # Fallback if format not followed
                return {
                    "optimized_resume": response_text,
                    "changes": ["Resume optimized for this position"],
                    "success": True
                }
            
        except Exception as e:
            return {
                "optimized_resume": "",
                "changes": [],
                "success": False,
                "error": str(e)
            }
        
        
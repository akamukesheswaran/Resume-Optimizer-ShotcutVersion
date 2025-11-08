import re
from typing import Dict, List
import config

class ResumeAnalyzer:
    """Resume analysis using ML and rule-based extraction (NO AI for parsing)"""
    
    def __init__(self):
        # Expanded skill keywords database
        self.skill_keywords = [
            # Programming Languages
            "Python", "Java", "JavaScript", "TypeScript", "C++", "C#", "Ruby", "Go", "Rust", "PHP",
            "Swift", "Kotlin", "R", "Scala", "Perl", "MATLAB", "C", "Objective-C",
            
            # Web Technologies
            "React", "Angular", "Vue", "Vue.js", "Node.js", "Django", "Flask", "Spring", "Express",
            "HTML", "CSS", "SASS", "LESS", "Bootstrap", "Tailwind", "REST", "GraphQL", "WebSocket",
            "Next.js", "Nuxt.js", "jQuery", "Redux", "MobX",
            
            # Databases
            "SQL", "MySQL", "PostgreSQL", "MongoDB", "Redis", "Cassandra", "DynamoDB",
            "Oracle", "SQLite", "ElasticSearch", "Neo4j", "CouchDB", "MariaDB",
            
            # Cloud & DevOps
            "AWS", "Azure", "GCP", "Google Cloud", "Docker", "Kubernetes", "K8s", "Jenkins", 
            "GitLab", "CI/CD", "Terraform", "Ansible", "Chef", "Puppet", "Linux", "Git",
            "GitHub", "Bitbucket", "CircleCI", "Travis CI",
            
            # ML & Data Science
            "Machine Learning", "Deep Learning", "TensorFlow", "PyTorch", "Keras", "scikit-learn",
            "NLP", "Natural Language Processing", "Computer Vision", "Neural Networks", 
            "Data Science", "Pandas", "NumPy", "Spark", "Hadoop", "Tableau", "Power BI",
            "MLOps", "AI", "Artificial Intelligence", "Data Mining", "Statistical Analysis",
            
            # Mobile
            "iOS", "Android", "React Native", "Flutter", "SwiftUI", "UIKit",
            
            # Testing
            "Testing", "Unit Testing", "Integration Testing", "Jest", "Mocha", "Pytest",
            "Selenium", "Cypress", "JUnit", "TestNG",
            
            # Other
            "Agile", "Scrum", "Microservices", "API", "RESTful API", "Serverless",
            "Blockchain", "Solidity", "Web3"
        ]
        
        # Education keywords
        self.education_levels = [
            "PhD", "Ph.D", "Doctorate", "Masters", "Master's", "MS", "M.S", "MBA",
            "Bachelor", "Bachelor's", "BS", "B.S", "BA", "B.A", "Associate", "Diploma"
        ]
        
        # Experience patterns
        self.experience_patterns = [
            r'(\d+)\+?\s*years?(?:\s+of)?\s+(?:experience|exp)',
            r'(\d+)\+?\s*yrs?(?:\s+of)?\s+(?:experience|exp)',
            r'experience[:\s]+(\d+)\+?\s*years?',
            r'(\d+)\+?\s*years?\s+in',
        ]
        
        # Project indicators
        self.project_indicators = [
            "project", "built", "developed", "created", "designed", "implemented",
            "deployed", "launched", "architected", "led"
        ]
    
    def extract_skills(self, resume_text: str) -> List[str]:
        """Extract skills using keyword matching (Traditional ML approach)"""
        found_skills = []
        text_lower = resume_text.lower()
        
        for skill in self.skill_keywords:
            # Use regex for better matching (word boundaries)
            pattern = r'\b' + re.escape(skill.lower()) + r'\b'
            if re.search(pattern, text_lower):
                found_skills.append(skill)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_skills = []
        for skill in found_skills:
            skill_lower = skill.lower()
            if skill_lower not in seen:
                seen.add(skill_lower)
                unique_skills.append(skill)
        
        return unique_skills
    
    def extract_education(self, resume_text: str) -> Dict:
        """Extract education using pattern matching"""
        education_info = {
            "degree": "",
            "field": "",
            "institution": "",
            "level": ""
        }
        
        text_lines = resume_text.split('\n')
        
        # Find education section
        education_section = []
        in_education = False
        
        for line in text_lines:
            line_lower = line.lower()
            
            # Start of education section
            if re.search(r'\b(education|academic|qualifications)\b', line_lower):
                in_education = True
                continue
            
            # End of education section (next major section)
            if in_education and re.search(r'\b(experience|skills|projects|work history)\b', line_lower):
                break
            
            if in_education:
                education_section.append(line)
        
        # Extract degree information
        education_text = ' '.join(education_section) if education_section else resume_text
        
        # Find highest degree
        for level in self.education_levels:
            pattern = r'\b' + re.escape(level) + r'\b'
            match = re.search(pattern, education_text, re.IGNORECASE)
            if match:
                education_info["level"] = level
                education_info["degree"] = level
                
                # Try to extract field (next few words after degree)
                context = education_text[match.start():match.start()+100]
                field_match = re.search(r'in\s+([A-Za-z\s]+)(?:\s+from|\s+at|\s*,|\s*\n|$)', context, re.IGNORECASE)
                if field_match:
                    education_info["field"] = field_match.group(1).strip()
                
                break
        
        # Build summary
        if education_info["degree"]:
            if education_info["field"]:
                education_info["summary"] = f"{education_info['degree']} in {education_info['field']}"
            else:
                education_info["summary"] = education_info["degree"]
        else:
            education_info["summary"] = "Education details from resume"
        
        return education_info
    
    def extract_years_of_experience(self, resume_text: str) -> float:
        """Extract years of experience using regex patterns"""
        years = []
        
        for pattern in self.experience_patterns:
            matches = re.findall(pattern, resume_text, re.IGNORECASE)
            for match in matches:
                try:
                    years.append(float(match))
                except:
                    continue
        
        # Also look for date ranges (e.g., 2018-2023)
        date_pattern = r'(20\d{2})\s*[-–]\s*(20\d{2}|present|current)'
        date_matches = re.findall(date_pattern, resume_text, re.IGNORECASE)
        
        for start, end in date_matches:
            start_year = int(start)
            end_year = 2024 if end.lower() in ['present', 'current'] else int(end)
            years.append(float(end_year - start_year))
        
        # Return the maximum found (most experience mentioned)
        return max(years) if years else 2.0  # Default to 2 if not found
    
    def extract_projects(self, resume_text: str) -> List[Dict]:
        """Extract project information using pattern matching"""
        projects = []
        
        text_lines = resume_text.split('\n')
        
        # Find projects section
        project_section = []
        in_projects = False
        
        for line in text_lines:
            line_lower = line.lower().strip()
            
            # Start of projects section
            if re.search(r'\b(projects?|portfolio|work samples)\b', line_lower):
                in_projects = True
                continue
            
            # End of projects section
            if in_projects and re.search(r'\b(experience|education|skills|work history)\b', line_lower):
                break
            
            if in_projects and line.strip():
                project_section.append(line)
        
        # If no explicit project section, look for project indicators
        if not project_section:
            for line in text_lines:
                line_lower = line.lower()
                for indicator in self.project_indicators:
                    if indicator in line_lower and len(line) > 20:
                        project_section.append(line)
                        break
        
        # Parse projects (simple version - just get project names/descriptions)
        for i, line in enumerate(project_section[:5]):  # Top 5 projects
            line = line.strip()
            if line and len(line) > 10:
                # Extract project title (usually the start of the line)
                title_match = re.match(r'^[•\-\*]?\s*([A-Za-z0-9\s\-:]+?)(?:\s*[-–]|\s*:|\s*\(|$)', line)
                if title_match:
                    title = title_match.group(1).strip()
                    projects.append({
                        "title": title,
                        "description": line[:100] + "..." if len(line) > 100 else line
                    })
        
        return projects
    
    def parse_resume(self, resume_text: str) -> Dict:
        """Full resume parsing without AI - rule-based + pattern matching"""
        
        skills = self.extract_skills(resume_text)
        education = self.extract_education(resume_text)
        years_exp = self.extract_years_of_experience(resume_text)
        projects = self.extract_projects(resume_text)
        
        return {
            "skills": skills,
            "education": education,
            "years_of_experience": years_exp,
            "projects": projects,
            "full_text": resume_text
        }
    
    def identify_missing_skills(self, resume_data: Dict, job: Dict) -> List[str]:
        """Identify missing skills (rule-based, no AI)"""
        
        job_requirements = job['requirements'].lower()
        resume_skills_lower = [s.lower() for s in resume_data.get('skills', [])]
        
        missing = []
        
        # Check each common skill keyword
        for skill in self.skill_keywords:
            skill_lower = skill.lower()
            # If skill is in job requirements but not in resume
            if skill_lower in job_requirements and skill_lower not in ' '.join(resume_skills_lower):
                missing.append(skill)
        
        return missing[:5]  # Top 5 missing skills
    
    def calculate_smart_score(
        self, 
        resume_data: Dict, 
        job: Dict, 
        ml_semantic_score: float
    ) -> Dict:
        """
        Smart Hybrid Scoring System
        Combines ML embeddings with rule-based scoring
        Prioritizes: Skills (40%) + Experience (40%) + Others (20%)
        """
        
        # ============================================
        # 1. EXACT SKILLS MATCH (25% weight)
        # ============================================
        job_requirements_lower = job['requirements'].lower()
        job_requirements_words = set(job_requirements_lower.split())
        
        resume_skills_lower = [s.lower() for s in resume_data.get('skills', [])]
        
        # Count exact keyword matches
        exact_matches = 0
        for skill in resume_skills_lower:
            if skill in job_requirements_lower:
                exact_matches += 1
        
        total_resume_skills = len(resume_skills_lower) if resume_skills_lower else 1
        exact_skills_score = min(exact_matches / max(total_resume_skills * 0.5, 1), 1.0)
        
        # ============================================
        # 2. RELATED SKILLS MATCH (15% weight)
        # ============================================
        # Skills that are related but not exact matches
        skill_synonyms = {
            'python': ['py', 'python3'],
            'javascript': ['js', 'typescript', 'ts'],
            'machine learning': ['ml', 'deep learning', 'dl', 'ai'],
            'react': ['reactjs', 'react.js'],
            'node': ['nodejs', 'node.js'],
            'tensorflow': ['tf'],
            'pytorch': ['torch'],
            'kubernetes': ['k8s'],
        }
        
        related_matches = 0
        for skill in resume_skills_lower:
            for key, synonyms in skill_synonyms.items():
                if skill == key or skill in synonyms:
                    if key in job_requirements_lower:
                        related_matches += 1
                        break
        
        related_skills_score = min(related_matches / max(total_resume_skills * 0.3, 1), 1.0)
        
        # ============================================
        # 3. EXPERIENCE MATCH (40% weight) - PRIORITY!
        # ============================================
        required_exp_str = job.get('experience', '0+')
        required_years = float(re.findall(r'\d+', required_exp_str)[0]) if re.findall(r'\d+', required_exp_str) else 0
        candidate_years = resume_data.get('years_of_experience', 0)
        
        if required_years == 0:
            experience_score = 0.8  # No requirement specified
        elif candidate_years >= required_years:
            # Has enough or more experience
            experience_score = 1.0
        elif candidate_years >= required_years * 0.7:
            # Close to requirement (70%+)
            experience_score = 0.85
        elif candidate_years >= required_years * 0.5:
            # Half the requirement
            experience_score = 0.65
        else:
            # Significantly below requirement
            experience_score = candidate_years / max(required_years, 1)
        
        experience_score = min(experience_score, 1.0)
        
        # ============================================
        # 4. EDUCATION MATCH (10% weight) - CONDITIONAL
        # ============================================
        edu_data = resume_data.get('education', {})
        candidate_edu = edu_data.get('level', '').lower()
        required_edu = job.get('education_required', '').lower()
        
        edu_hierarchy = {
            'phd': 5, 'ph.d': 5, 'doctorate': 5,
            'masters': 4, "master's": 4, 'ms': 4, 'm.s': 4, 'mba': 4,
            'bachelor': 3, "bachelor's": 3, 'bs': 3, 'b.s': 3, 'ba': 3,
            'associate': 2,
            'diploma': 1
        }
        
        candidate_level = 0
        required_level = 0
        
        for key, value in edu_hierarchy.items():
            if key in candidate_edu:
                candidate_level = max(candidate_level, value)
            if key in required_edu:
                required_level = max(required_level, value)
        
        # Only apply education penalty if job explicitly requires it
        if required_level == 0:
            education_score = 0.8  # No requirement
        elif candidate_level >= required_level:
            education_score = 1.0
        elif candidate_level == required_level - 1:
            education_score = 0.85
        else:
            education_score = 0.6
        
        # ============================================
        # 5. PROJECTS MATCH (10% weight) - CONDITIONAL
        # ============================================
        projects = resume_data.get('projects', [])
        projects_required = job.get('projects_required', '').lower()
        
        # Only apply projects if job mentions it
        if 'portfolio' in projects_required or 'projects' in projects_required:
            projects_score = min(len(projects) / 2.0, 1.0) if projects else 0.4
        else:
            projects_score = 0.7  # Not critical, give benefit of doubt
        
        # ============================================
        # 6. ML SEMANTIC SIMILARITY (30% weight)
        # ============================================
        # This is the embedding-based match from FAISS
        semantic_score = ml_semantic_score
        
        # ============================================
        # FINAL WEIGHTED SCORE
        # ============================================
        """
        Weights based on your priorities:
        - Skills: 40% (Exact 25% + Related 15%)
        - Experience: 40% (Most important!)
        - ML Semantic: 30% (Context understanding)
        - Education: 10% (Conditional)
        - Projects: 10% (Conditional)
        
        Total adds up to more than 100% because education and projects
        are conditional - we dynamically weight them
        """
        
        # Base scoring (always applied)
        base_score = (
            exact_skills_score * 0.25 +
            related_skills_score * 0.15 +
            experience_score * 0.40 +
            semantic_score * 0.20
        )
        
        # Conditional scoring (applied if job mentions requirements)
        education_weight = 0.05 if required_level > 0 else 0
        projects_weight = 0.05 if 'portfolio' in projects_required or 'projects' in projects_required else 0
        
        conditional_score = (
            education_score * education_weight +
            projects_score * projects_weight
        )
        
        final_score = min(base_score + conditional_score, 1.0)
        
        return {
            "final_score": final_score,
            "breakdown": {
                "exact_skills": exact_skills_score,
                "related_skills": related_skills_score,
                "experience": experience_score,
                "education": education_score,
                "projects": projects_score,
                "semantic": semantic_score
            },
            "weights": {
                "skills_total": 0.40,  # 25% + 15%
                "experience": 0.40,
                "semantic": 0.20,
                "education": education_weight,
                "projects": projects_weight
            },
            "experience_gap": max(0, required_years - candidate_years),
            "education_sufficient": candidate_level >= required_level if required_level > 0 else True,
            "exact_matches": exact_matches,
            "related_matches": related_matches
        }

    def calculate_detailed_breakdown(self, resume_data: Dict, job: Dict) -> Dict:
        """Calculate 4-category breakdown: Skills, Education, Experience, Projects (NO AI)"""
        
        # 1. SKILLS MATCH
        job_requirements = job['requirements'].lower()
        resume_skills_lower = [s.lower() for s in resume_data.get('skills', [])]
        
        # Count how many resume skills appear in job requirements
        skills_matched = sum(1 for skill in resume_skills_lower if skill in job_requirements)
        total_resume_skills = len(resume_skills_lower) if resume_skills_lower else 1
        
        skills_score = min(skills_matched / max(total_resume_skills * 0.5, 1), 1.0)  # At least 50% should match
        
        # 2. EDUCATION MATCH
        edu_data = resume_data.get('education', {})
        candidate_edu = edu_data.get('level', '').lower()
        required_edu = job.get('education_required', '').lower()
        
        edu_hierarchy = {
            'phd': 5, 'ph.d': 5, 'doctorate': 5,
            'masters': 4, "master's": 4, 'ms': 4, 'm.s': 4, 'mba': 4,
            'bachelor': 3, "bachelor's": 3, 'bs': 3, 'b.s': 3, 'ba': 3,
            'associate': 2,
            'diploma': 1
        }
        
        candidate_level = 0
        required_level = 0
        
        for key, value in edu_hierarchy.items():
            if key in candidate_edu:
                candidate_level = max(candidate_level, value)
            if key in required_edu:
                required_level = max(required_level, value)
        
        if required_level == 0:  # No specific requirement
            education_score = 0.8
        elif candidate_level >= required_level:
            education_score = 1.0
        elif candidate_level == required_level - 1:
            education_score = 0.8  # One level below
        else:
            education_score = 0.5  # Significantly below
        
        # 3. EXPERIENCE MATCH
        required_exp_str = job.get('experience', '0+')
        required_years = float(re.findall(r'\d+', required_exp_str)[0]) if re.findall(r'\d+', required_exp_str) else 0
        candidate_years = resume_data.get('years_of_experience', 0)
        
        if required_years == 0:
            experience_score = 0.8
        elif candidate_years >= required_years:
            experience_score = 1.0
        elif candidate_years >= required_years * 0.7:
            experience_score = 0.8
        else:
            experience_score = candidate_years / max(required_years, 1)
        
        experience_score = min(experience_score, 1.0)
        
        # 4. PROJECTS MATCH
        projects = resume_data.get('projects', [])
        projects_score = min(len(projects) / 2.0, 1.0) if projects else 0.5  # Assume some projects even if not detected
        
        # Overall score (weighted average)
        overall_score = (
            skills_score * 0.40 +      # Skills most important
            education_score * 0.25 +   # Education
            experience_score * 0.25 +  # Experience
            projects_score * 0.10      # Projects least weight
        )
        
        return {
            "overall": overall_score,
            "skills": {
                "score": skills_score,
                "matched": skills_matched,
                "total": total_resume_skills,
                "missing": self.identify_missing_skills(resume_data, job)
            },
            "education": {
                "score": education_score,
                "candidate": edu_data.get('summary', 'Not specified'),
                "required": job.get('education_required', 'Not specified'),
                "candidate_level": candidate_level,
                "required_level": required_level
            },
            "experience": {
                "score": experience_score,
                "candidate_years": candidate_years,
                "required_years": required_years,
                "gap": max(0, required_years - candidate_years)
            },
            "projects": {
                "score": projects_score,
                "count": len(projects),
                "required": job.get('projects_required', 'Portfolio of relevant projects')
            }
        }
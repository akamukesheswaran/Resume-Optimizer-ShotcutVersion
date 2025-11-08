import os
from dotenv import load_dotenv

load_dotenv()

# API Keys
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

# App Settings
APP_TITLE = "Job Resume Screening"
APP_ICON = "🎯"

# Models
EMBEDDING_MODEL = "sentence-transformers/all-mpnet-base-v2"
CLAUDE_MODEL = "claude-sonnet-4-20250514"

# Paths
DATA_DIR = "data"
JOBS_FILE = os.path.join(DATA_DIR, "jobs.json")

# Job roles for filtering (predefined list)
JOB_ROLES = [
    "Machine Learning Engineer",
    "ML Engineer",
    "Software Engineer",
    "Senior Software Engineer",
    "Data Scientist",
    "Senior Data Scientist",
    "Frontend Developer",
    "Backend Developer",
    "Full Stack Developer",
    "DevOps Engineer",
    "Data Engineer",
    "AI/ML Researcher",
    "Product Manager - Tech",
    "Cloud Engineer",
    "Mobile Developer (iOS/Android)"
]
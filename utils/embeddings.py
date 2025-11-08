import numpy as np
from sentence_transformers import SentenceTransformer
import faiss
from typing import List, Dict, Tuple
import config  # ✅ IMPORT CONFIG!

class JobMatcher:
    """Smart job matching using embeddings and FAISS"""
    
    def __init__(self, model_name: str = None):
        # ✅ Use config model by default!
        if model_name is None:
            model_name = config.EMBEDDING_MODEL
        
        print(f"🔄 Loading embedding model: {model_name}")
        self.model = SentenceTransformer(model_name)
        
        # ✅ Get dimension dynamically from the model!
        self.dimension = self.model.get_sentence_embedding_dimension()
        print(f"✅ Model loaded! Embedding dimensions: {self.dimension}")
        
        self.index = None
        self.jobs = []
    
    def create_job_embedding(self, job: Dict) -> np.ndarray:
        """Convert job posting to embedding vector"""
        # Combine all relevant job info into one text
        text = f"{job['title']} {job['company']} {job['description']} {job['requirements']}"
        embedding = self.model.encode(text)
        return embedding
    
    def create_profile_embedding(self, profile: Dict) -> np.ndarray:
        """Convert user profile to embedding vector"""
        # Combine user profile info
        text = f"{profile.get('title', '')} {profile.get('skills', '')} {profile.get('experience', '')}"
        embedding = self.model.encode(text)
        return embedding
    
    def build_job_index(self, jobs: List[Dict]):
        """Build FAISS index from job listings"""
        print(f"🔧 Building FAISS index for {len(jobs)} jobs...")
        print(f"🔍 Using {self.dimension}-dimensional embeddings")
        
        self.jobs = jobs
        
        # Create embeddings for all jobs
        embeddings = []
        for job in jobs:
            emb = self.create_job_embedding(job)
            embeddings.append(emb)
        
        # Convert to numpy array
        embeddings = np.array(embeddings).astype('float32')
        
        # Create FAISS index (L2 distance)
        self.index = faiss.IndexFlatL2(self.dimension)
        self.index.add(embeddings)
        
        print(f"✅ FAISS index built successfully!")
        print(f"   - Total jobs indexed: {self.index.ntotal}")
        print(f"   - Embedding dimensions: {self.index.d}")
        
        return self.index
    
    def find_matching_jobs(self, profile: Dict, top_k: int = 10) -> List[Tuple[Dict, float]]:
        """Find top matching jobs for a user profile"""
        
        if self.index is None or len(self.jobs) == 0:
            raise ValueError("Index not built. Call build_job_index() first.")
        
        # Create profile embedding
        profile_emb = self.create_profile_embedding(profile)
        profile_emb = np.array([profile_emb]).astype('float32')
        
        # Search for similar jobs
        distances, indices = self.index.search(profile_emb, min(top_k, len(self.jobs)))
        
        # Convert distances to similarity scores (0-1)
        # Lower distance = higher similarity
        # Using: score = 1 / (1 + distance)
        results = []
        for idx, distance in zip(indices[0], distances[0]):
            if idx < len(self.jobs):
                similarity_score = 1 / (1 + distance)
                results.append((self.jobs[idx], similarity_score))
        
        return results
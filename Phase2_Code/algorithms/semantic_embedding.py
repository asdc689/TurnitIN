import numpy as np
from sentence_transformers import SentenceTransformer
from typing import List

class SemanticEmbedder:
    def __init__(self):
        # 1. We load the model once into RAM.
        self.model = SentenceTransformer("jinaai/jina-embeddings-v2-base-code", trust_remote_code=True)

    def encode_batch(self, code_snippets: List[str]) -> np.ndarray:
        # 2. We take a list of 50 student codes, and the AI turns them into 50 vectors (matrices).
        if not code_snippets:
            return np.array([])
        embeddings = self.model.encode(code_snippets)
        
        # 3. We normalize them mathematically. (This replaces what FAISS used to do).
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        norms[norms == 0] = 1e-10 
        return embeddings / norms

    def calculate_similarity(self, vector_a: np.ndarray, vector_b: np.ndarray) -> float:
        # 4. We calculate the exact percentage similarity between two files.
        sim = np.dot(vector_a, vector_b)
        return float(np.clip(sim, 0.0, 1.0))
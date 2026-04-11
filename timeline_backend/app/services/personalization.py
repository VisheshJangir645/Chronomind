import numpy as np
from typing import List, Dict

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    SentenceTransformer = None

class PersonalizationEngine:
    """
    A machine learning engine for adapting historical timelines using continuous dense vector embeddings.
    """
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2'):
        # using a lightweight Sentence-BERT model (384 architecture) for fast CPU inference
        if SentenceTransformer:
            self.encoder = SentenceTransformer(model_name)
        else:
            self.encoder = None
    
    def generate_user_embedding(self, explicit_interests: List[str], history_interactions: List[str]) -> np.ndarray:
        """
        Generates a 1D continuous User Profile Vector by combining explicit preferences and implicit click history.
        """
        if not self.encoder:
            raise RuntimeError("SentenceTransformer not installed.")
            
        texts = explicit_interests + history_interactions
        if not texts:
            return np.zeros(self.encoder.get_sentence_embedding_dimension())
        
        # O(N) Complexity: Encode all textual signals into dense space
        embeddings = self.encoder.encode(texts)
        
        # Average pooling creates a singular profile vector in the semantic space
        user_vector = np.mean(embeddings, axis=0)
        return user_vector

    def rank_events(self, user_vector: np.ndarray, events: List[Dict], top_k: int = 5) -> List[Dict]:
        """
        Ranks a chronological timeline by semantic relevance using Cosine Similarity against the User Vector.
        """
        if not self.encoder or np.all(user_vector == 0):
            return events # Fallback to standard timeline
            
        event_descriptions = [e.get('description', '') for e in events]
        event_embeddings = self.encoder.encode(event_descriptions)
        
        norm_u = np.linalg.norm(user_vector)
        similarities = []
        
        for emb in event_embeddings:
            norm_e = np.linalg.norm(emb)
            if norm_u == 0 or norm_e == 0:
                sim = 0.0
            else:
                sim = np.dot(user_vector, emb) / (norm_u * norm_e)
            similarities.append(float(sim))
            
        # Map scores to the original dictionaries
        for idx, event in enumerate(events):
            event['relevance_score'] = similarities[idx]
            
        # O(N log N): Rank events by continuous relevance, then select Top K
        ranked_events = sorted(events, key=lambda x: x['relevance_score'], reverse=True)[:top_k]
        
        # After filtering, re-sort chronologically to maintain the timeline structure
        chronological_timeline = sorted(ranked_events, key=lambda x: x.get('date', ''))
        return chronological_timeline
        
    def generate_adaptive_summary(self, event: Dict, knowledge_level: str) -> str:
        """
        Dynamically adjusts the text complexity.
        In a production pipeline, this string builds an optimal Prompt injected into an LLM API (vLLM/Llama-3).
        """
        base_desc = event.get('description', '')
        actor = event.get('actor', 'Historical Figures')
        
        if knowledge_level == "beginner":
            # Focus: Elimination of jargon, explanation of core concepts.
            return f"Prompt Template -> Rewrite this simply for a middle school student. Explain who {actor} was. Event: {base_desc}"
            
        elif knowledge_level == "advanced":
            # Focus: Geopolitics, economic causality, historiography.
            return f"Prompt Template -> Act as an academic historian. Analyze the socio-political nuance of this event: {base_desc}"
            
        return base_desc

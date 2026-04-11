import numpy as np
from typing import List
import logging

try:
    import faiss
    from sentence_transformers import CrossEncoder
except ImportError:
    faiss, CrossEncoder = None, None

from app.schemas import ChronoEvent
from app.services.embeddings import model_store

logger = logging.getLogger(__name__)

class RAGRetrievalEngine:
    """
    High-Precision Semantic Query Engine.
    Refactored to comply with the new Unified Pipeline. Instead of instantiating its 
    own SentenceTransformer models (which originally bloated memory), it strictly leverages 
    the Global Embedding Singleton and the unified `ChronoEvent` schema.
    """
    def __init__(self, cross_encoder_model='cross-encoder/ms-marco-MiniLM-L-6-v2'):
        # We only load the CrossEncoder here. The Bi-Encoder is handled by the unified ModelStore.
        self.cross_encoder = CrossEncoder(cross_encoder_model) if CrossEncoder else None
        self.index = None
        self.memory_store: List[ChronoEvent] = []
        
    def build_index(self, events: List[ChronoEvent]):
        """
        Ingests the formalized, validated output pipeline.
        """
        if not faiss or not events:
            logger.error("FAISS not loaded or empty array provided.")
            return
            
        self.memory_store = events
        
        # CRITICAL FIX: We do not re-encode text. We just pull the mathematically exact 
        # Float arrays that the Master Pipeline already calculated. Zero duplicated computation.
        try:
            embeddings = np.array([ev.embedding for ev in events], dtype=np.float32)
            faiss.normalize_L2(embeddings)
            
            self.index = faiss.IndexFlatIP(embeddings.shape[1])
            self.index.add(embeddings)
            logger.info("Successfully populated FAISS index.")
        except Exception as e:
            logger.error(f"Failed to build FAISS index: {e}")

    def execute_query(self, query: str, top_k_filter: int = 100, rerank_depth: int = 10) -> List[ChronoEvent]:
        """
        Avoids Keyword extraction. Translates the semantic intent of the query to match historical context.
        """
        if not self.index or self.index.ntotal == 0:
            return []
            
        # 1. Broad Event Filtering (Vector Search)
        # Use the Singleton to encode the specific user query
        query_emb = model_store.get_embedding([query])
        faiss.normalize_L2(query_emb)
        
        distances, indices = self.index.search(query_emb, min(top_k_filter, self.index.ntotal))
        candidates = [self.memory_store[idx] for idx in indices[0] if idx != -1]
        
        if not self.cross_encoder or not candidates:
            return candidates
            
        # 2. Strict Semantic Re-Ranking
        cross_pairs = [[query, ev.description] for ev in candidates]
        cross_scores = self.cross_encoder.predict(cross_pairs)
        
        # Rank by deep linguistic relevance, stripping generic term overlaps
        ranked_candidates = [
            (candidates[i], float(cross_scores[i])) 
            for i in range(len(candidates))
        ]
        ranked_candidates.sort(key=lambda x: x[1], reverse=True)
        
        # 3. Finalization
        final_events = [ev for ev, score in ranked_candidates[:rerank_depth]]
        
        # Sort chronologically, not conceptually.
        return sorted(final_events, key=lambda x: x.date_normalized)

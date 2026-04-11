import numpy as np
from typing import List, Dict

try:
    import faiss
    from sentence_transformers import SentenceTransformer, CrossEncoder
except ImportError:
    faiss, SentenceTransformer, CrossEncoder = None, None, None

class RAGTimelineService:
    """
    Retrieval-Augmented Generation Service for generating query-specific historical timelines.
    Utilizes FAISS for massive vector indexing and a strict Cross-Encoder for precision re-ranking.
    """
    def __init__(self, 
                 bi_encoder_model='all-MiniLM-L6-v2', 
                 cross_encoder_model='cross-encoder/ms-marco-MiniLM-L-6-v2'):
        if SentenceTransformer and faiss:
            # Bi-Encoder: Used for massive scale, fast vector retrieval (calculates embeddings separately)
            self.bi_encoder = SentenceTransformer(bi_encoder_model)
            
            # Cross-Encoder: Deeply compares query + text pair simultaneously for maximum relevance logic
            self.cross_encoder = CrossEncoder(cross_encoder_model)
            
            self.dimension = self.bi_encoder.get_sentence_embedding_dimension()
            
            # Initialize FAISS index using Inner Product (Requires normalized vectors to act as Cosine Similarity)
            self.index = faiss.IndexFlatIP(self.dimension)
            
            # In-memory document store matching the FAISS specific indices
            self.event_store = []
        else:
            self.bi_encoder = None

    def ingest_events(self, events: List[Dict]):
        """
        Indexes raw historical events into the FAISS vector database.
        """
        if not self.bi_encoder or not events:
            return
            
        self.event_store.extend(events)
        descriptions = [e.get('description', '') for e in events]
        
        # O(N) Encoding
        embeddings = self.bi_encoder.encode(descriptions, convert_to_numpy=True)
        
        # Normalize the vectors (L2) so that Inner Product yields exact Cosine Similarity
        faiss.normalize_L2(embeddings)
        self.index.add(embeddings)

    def query_timeline(self, query: str, top_k_retrieval: int = 100, top_n_rerank: int = 10) -> List[Dict]:
        """
        Two-stage retrieval pipeline:
        1. Fast Bi-Encoder FAISS retrieval grabs a broad pool of 100 events.
        2. Powerful Cross-Encoder deeply analyzes the 100 events and slices to the top 10 most relevant.
        """
        if not self.bi_encoder or self.index.ntotal == 0:
            return []
            
        # === STAGE 1: Broad Semantic Retrieval (Bi-Encoder) ===
        query_emb = self.bi_encoder.encode([query], convert_to_numpy=True)
        faiss.normalize_L2(query_emb)
        
        # Search FAISS index scaling logarithmically 
        distances, indices = self.index.search(query_emb, min(top_k_retrieval, self.index.ntotal))
        
        # Extract candidate events from the datastore
        candidates = [self.event_store[idx] for idx in indices[0] if idx != -1]
        
        if not candidates:
            return []
            
        # === STAGE 2: Precision Re-Ranking (Cross-Encoder) ===
        # The Cross-Encoder doesn't use vectors, it runs the query and description simultaneously through the BERT layers 
        # allowing full self-attention across both texts.
        cross_inp = [[query, ev.get('description', '')] for ev in candidates]
        cross_scores = self.cross_encoder.predict(cross_inp)
        
        # Attach strict relevancy scores to candidates
        for idx, ev in enumerate(candidates):
            ev['rag_score'] = float(cross_scores[idx])
            
        # Rank by RAG relevancy score
        reranked_events = sorted(candidates, key=lambda x: x['rag_score'], reverse=True)[:top_n_rerank]
        
        # === STAGE 3: Timeline Construction ===
        # A timeline must be sequential, not ordered by relevance. Re-sort by actual historical Date.
        final_timeline = sorted(reranked_events, key=lambda x: x.get('date', '9999-12-31'))
        
        return final_timeline

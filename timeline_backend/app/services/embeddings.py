import logging
import numpy as np

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    SentenceTransformer = None

logger = logging.getLogger(__name__)

class ModelStore:
    """
    Singleton registry to prevent OOM errors by ensuring Heavy ML Weights 
    are loaded exactly once and shared across all sub-modules.
    """
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ModelStore, cls).__new__(cls)
            cls._instance.sbert_model = None
            cls._instance.encoder_dimension = 384
            cls._instance._available = False
        return cls._instance
        
    def load_models(self, model_name='all-MiniLM-L6-v2'):
        if not SentenceTransformer:
            logger.warning("SentenceTransformer not installed. Using zero-vector fallback.")
            return
            
        if self.sbert_model is None:
            try:
                logger.info(f"Loading Global SBERT Embedder: {model_name}")
                self.sbert_model = SentenceTransformer(model_name)
                self.encoder_dimension = self.sbert_model.get_sentence_embedding_dimension()
                self._available = True
            except Exception as e:
                logger.error(f"Failed to load SBERT model: {e}")
            
    def get_embedding(self, texts):
        """Returns embeddings. Falls back to zero vectors if model unavailable."""
        if self.sbert_model:
            return self.sbert_model.encode(texts, convert_to_numpy=True)
        # Graceful fallback: return zero vectors so pipeline never crashes
        return np.zeros((len(texts), self.encoder_dimension), dtype=np.float32)
    
    @property
    def is_available(self):
        return self._available

# Export the singleton instance
model_store = ModelStore()

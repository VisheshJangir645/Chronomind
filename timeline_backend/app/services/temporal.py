import re
from typing import Dict, List, Optional
import numpy as np

import logging
logger = logging.getLogger(__name__)

try:
    from sentence_transformers import SentenceTransformer, util
except ImportError:
    SentenceTransformer, util = None, None

class TemporalReasoner:
    """
    Advanced Rule + ML inference engine for resolving highly ambiguous historical bounds.
    Handles exact spans (Regex), relative vectors (Graph Math), and Historical Epoch bounding.
    """
    def __init__(self, encoder_model='all-MiniLM-L6-v2'):
        if SentenceTransformer:
            self.encoder = SentenceTransformer(encoder_model)
        else:
            self.encoder = None
            
        # Hardcoded fallback cache mapping massive historical epochs to exact ISO boundaries
        # In a production environment, this would ping a Wikidata API or an internal SQL table
        self.epoch_cache = {
            "mughal rule": {"start": "1526-04-20", "end": "1857-09-21"},
            "roman empire": {"start": "0027-01-01", "end": "0476-09-04"},
            "french revolution": {"start": "1789-05-05", "end": "1799-11-09"},
            "victorian era": {"start": "1837-06-20", "end": "1901-01-22"},
            "cold war": {"start": "1947-03-12", "end": "1991-12-26"}
        }

    def resolve_date(self, raw_expression: str, global_knowledge_graph: List[Dict] = None) -> Optional[Dict]:
        """
        Ingests colloquial expressions, normalizes them, and infers approximate ISO bounds.
        """
        raw_lower = raw_expression.lower().strip()
        
        # ==========================================
        # STAGE 1: Explicit Mathematical Spans
        # ==========================================
        # Example: "late 19th century"
        century_match = re.match(r'(early|mid|late)?\-?\s*(\d{1,2})(st|nd|rd|th)?\s*century', raw_lower)
        if century_match:
            modifier = century_match.group(1)
            century = int(century_match.group(2))
            
            base_year = (century - 1) * 100
            start_year, end_year = base_year, base_year + 99
            
            if modifier == 'early': end_year = base_year + 33
            elif modifier == 'mid': start_year = base_year + 34; end_year = base_year + 66
            elif modifier == 'late': start_year = base_year + 67
                
            return {
                "type": "isolated_bound",
                "raw_text": raw_expression,
                "start": f"{start_year:04d}-01-01",
                "end": f"{end_year:04d}-12-31"
            }
            
        # ==========================================
        # STAGE 2: Historical Epoch Bounding
        # ==========================================
        # Example: "during Mughal rule" or "in the Victorian era"
        epoch_match = re.search(r'(during|in|throughout)\s+(the\s+)?(.*(rule|era|empire|dynasty|kingdom|period))', raw_lower)
        if epoch_match:
            epoch_name = epoch_match.group(3).strip()
            # Approximate date inference via Cache Hit
            for cache_key, bounds in self.epoch_cache.items():
                if cache_key in epoch_name:
                    return {
                        "type": "epoch_span",
                        "raw_text": raw_expression,
                        "start": bounds["start"],
                        "end": bounds["end"],
                        "confidence": 1.0,
                        "inferred_from_epoch": cache_key
                    }
                    
        # ==========================================
        # STAGE 3: Dense Semantic Anchoring
        # ==========================================
        # Example: "after the revolution"
        anchor_match = re.match(r'(before|after|prior to|following)\s+(.*)', raw_lower)
        
        if anchor_match and global_knowledge_graph and self.encoder:
            relation = anchor_match.group(1)
            event_query = anchor_match.group(2).strip()
            
            event_strs = [e.get('description', '') for e in global_knowledge_graph]
            event_embs = self.encoder.encode(event_strs, convert_to_tensor=True)
            query_emb = self.encoder.encode([event_query], convert_to_tensor=True)
            
            cos_scores = util.cos_sim(query_emb, event_embs)[0]
            best_idx = int(np.argmax(cos_scores))
            
            # Require high confidence to maintain chronological consistency
            if cos_scores[best_idx] > 0.65: 
                anchored_date = global_knowledge_graph[best_idx].get('date_normalized', 'UNKNOWN')
                
                return {
                    "type": "relative_semantic_bound",
                    "raw_text": raw_expression,
                    "relational_bound": relation,         
                    "anchor_date": anchored_date,         
                    "confidence": float(cos_scores[best_idx]),
                    "semantic_graph_match": event_strs[best_idx]
                }

        # Dead-end edge cases return None to be tagged as "Undated" graphically
        return None

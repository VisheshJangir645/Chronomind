import numpy as np
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)

try:
    from sentence_transformers import SentenceTransformer, util
except ImportError:
    SentenceTransformer, util = None, None

class CrossLingualAligner:
    """
    Aligns and merges historical events across different linguistic sources 
    utilizing a multilingual Transformer model (XLM-R / mBERT).
    """
    def __init__(self, model_name='paraphrase-multilingual-mpnet-base-v2'):
        # paraphrase-multilingual natively supports English, Hindi, and 48 other languages 
        # mapping them into the exact same dense vector space.
        if SentenceTransformer:
            logger.info(f"Loading Cross-Lingual Model: {model_name}")
            self.model = SentenceTransformer(model_name)
        else:
            self.model = None

    def merge_timelines(self, timelines: List[List[Dict]], similarity_threshold: float = 0.85) -> List[Dict]:
        """
        Ingests multiple timelines from different languages and merges them into a unified chronological array.
        Resolves duplicate events via Cosine Similarity and flags conflicting extractions.
        """
        if not self.model:
            raise RuntimeError("SentenceTransformer not installed.")
        
        # 1. Flatten all events from all languages into a unified pool
        all_events = []
        for i, timeline in enumerate(timelines):
            for event in timeline:
                event['source_lang'] = f"timeline_source_{i}"
                all_events.append(event)
                
        # 2. Group events strictly by Date. 
        # In a heavier system, this could group by 'Year' or 'Month' for loose temporal bounds.
        date_groups = {}
        for event in all_events:
            date = event.get('date', 'UNKNOWN')
            if date not in date_groups:
                date_groups[date] = []
            date_groups[date].append(event)
            
        unified_timeline = []
        
        # 3. Cross-Lingual Semantic Alignment
        for date, events in date_groups.items():
            if len(events) == 1:
                unified_timeline.append(events[0])
                continue
                
            # If multiple events occur on the same date, check cross-lingual semantic similarity
            descriptions = [e.get('description', '') for e in events]
            
            # Encode sentences from disparate languages into the same vector space
            embeddings = self.model.encode(descriptions, convert_to_tensor=True)
            
            # Calculate cross-matrix Cosine Similarities
            cosine_scores = util.cos_sim(embeddings, embeddings)
            
            merged_indices = set()
            for i in range(len(events)):
                if i in merged_indices:
                    continue
                    
                cluster = [events[i]]
                merged_indices.add(i)
                
                for j in range(i + 1, len(events)):
                    if j not in merged_indices and cosine_scores[i][j].item() > similarity_threshold:
                        cluster.append(events[j])
                        merged_indices.add(j)
                        
                if len(cluster) > 1: # We found a duplicate cross-lingual event!
                    base_event = self._resolve_cluster(cluster)
                    unified_timeline.append(base_event)
                else:
                    unified_timeline.append(events[i])
                    
        return sorted(unified_timeline, key=lambda x: x.get('date', '9999'))
        
    def _resolve_cluster(self, cluster: List[Dict]) -> Dict:
        """
        Handles deduplication and conflict-flagging for an identified cross-lingual cluster.
        """
        base_event = cluster[0].copy()
        
        # Merge descriptions
        base_event['description'] = " | ".join([e.get('description', '') for e in cluster])
        base_event['sources'] = [e['source_lang'] for e in cluster]
        
        # Conflict Detection Logic: If the model determined these describe the identical event, 
        # but the specific extracted Actors/Locations differ, it is a Historiographical Conflict!
        actors = set([e.get('actor') for e in cluster if e.get('actor')])
        locations = set([e.get('location') for e in cluster if e.get('location')])
        
        base_event['conflict_flag'] = len(actors) > 1 or len(locations) > 1
        return base_event

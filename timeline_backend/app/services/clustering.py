import numpy as np
from typing import List, Dict

try:
    from sklearn.cluster import AgglomerativeClustering
    from sentence_transformers import SentenceTransformer
except ImportError:
    AgglomerativeClustering, SentenceTransformer = None, None

class MultiLevelTimelineService:
    """
    A data science module dedicated to Hierarchical Event Grouping. 
    Prevents UI cognitive overload by clustering hundreds of raw events into 
    dynamically scalable 'Macro', 'Meso', and 'Micro' chronological tiers.
    """
    def __init__(self, encoder_model='all-MiniLM-L6-v2'):
        if SentenceTransformer:
            self.encoder = SentenceTransformer(encoder_model)
        else:
            self.encoder = None

    def _calculate_importance(self, events: List[Dict]) -> tuple[List[Dict], np.ndarray]:
        """
        Assigns an absolute scalar Importance Score to each node based on 
        graph corroboration and semantic centrality.
        """
        if not events: return [], np.array([])
        
        descriptions = [e.get('description', '') for e in events]
        embeddings = self.encoder.encode(descriptions)
        
        # Calculate the "center of gravity" of the timeline era
        global_centroid = np.mean(embeddings, axis=0)
        
        for i, event in enumerate(events):
            # Graph Corroboration Metric: Number of historic sources that cited this event
            source_count = len(set(event.get('sources', ['unknown'])))
            
            # Semantic Metric: How structurally central is this event to the overall extracted history?
            emb = embeddings[i]
            sim_to_center = np.dot(emb, global_centroid) / (np.linalg.norm(emb) * np.linalg.norm(global_centroid))
            
            # Composite Importance Weighting
            importance = (source_count * 0.7) + (sim_to_center * 0.3)
            event['importance_score'] = round(float(importance), 3)
            
        return events, embeddings

    def _build_hierarchy(self, events: List[Dict], embeddings: np.ndarray, distance_thresh: float) -> Dict[int, List[Dict]]:
        """
        Applies Hierarchical Agglomerative Clustering (Bottom-Up) 
        to group semantically bound events across time.
        """
        if not AgglomerativeClustering:
            raise RuntimeError("Scikit-learn not available for clustering.")
            
        clustering = AgglomerativeClustering(
            n_clusters=None, 
            distance_threshold=distance_thresh, 
            linkage='ward' # Minimizes the variance of clusters being merged
        )
        clustering.fit(embeddings)
        
        clusters = {}
        for idx, label in enumerate(clustering.labels_):
            if label not in clusters:
                clusters[label] = []
            clusters[label].append(events[idx])
            
        return clusters

    def render_zoom_level(self, events: List[Dict], zoom_level: str = "high") -> List[Dict]:
        """
        Public API scaling the detail resolution of the array.
        zoom_level enum: "high" (Macro), "mid" (Meso), "detailed" (Micro)
        """
        if not self.encoder or not events:
            return events

        events, embeddings = self._calculate_importance(events)
        
        if zoom_level == "detailed":
            # Micro-level: Return raw, un-clustered history.
            return sorted(events, key=lambda x: x.get('date', ''))
            
        # Threshold scales dictating how aggressively to group clusters
        threshold = 2.0 if zoom_level == "high" else 1.2
        clusters = self._build_hierarchy(events, embeddings, distance_thresh=threshold)
        
        rendered_timeline = []
        
        for cluster_id, cluster_events in clusters.items():
            # The cluster's "Avatar" is simply the highest scored event inside the cluster
            representative = max(cluster_events, key=lambda x: x.get('importance_score', 0))
            
            # Package the child events inside the representative node for optional UI expansion
            representative['sub_events_count'] = len(cluster_events) - 1
            representative['sub_events'] = [e for e in cluster_events if e != representative]
            
            if zoom_level == "high":
                # High-level explicitly filters out 'noise' clusters that only contain 1 minor stray event
                if len(cluster_events) >= 3 or representative['importance_score'] > 2.5:
                    rendered_timeline.append(representative)
            else:
                # Mid-level returns all cluster representatives
                rendered_timeline.append(representative)
                
        # Final output guaranteed chronological
        return sorted(rendered_timeline, key=lambda x: x.get('date', ''))

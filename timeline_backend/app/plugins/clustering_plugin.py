import numpy as np
from typing import List, Tuple
import logging

try:
    from sklearn.cluster import AgglomerativeClustering
except ImportError:
    AgglomerativeClustering = None

from app.schemas import ChronoEvent

logger = logging.getLogger(__name__)

class ZoomableClusteringPlugin:
    """
    Refactored to comply with the Unified Plugin Architecture.
    Prevents UI cognitive overload by clustering hundreds of raw events into 
    scalable 'Macro' and 'Meso' hierarchical tiers using natively baked SBERT arrays.
    """
    def name(self) -> str:
        return "Agglomerative_Zoom_Plugin"
        
    def execute(self, events: List[ChronoEvent], zoom_level: str = "high") -> List[ChronoEvent]:
        if zoom_level == "detailed" or not AgglomerativeClustering or len(events) < 3:
            return sorted(events, key=lambda x: x.date_normalized)

        scored_events: List[Tuple[ChronoEvent, float]] = []
        for ev in events:
            source_weight = len(set(ev.sources)) * 0.7
            confidence_weight = (ev.confidence.overall_score if ev.confidence else 0.5) * 0.3
            importance = round(source_weight + confidence_weight, 3)
            scored_events.append((ev, importance))

        embeddings = np.array([ev.embedding for ev in events], dtype=np.float32)
        distance_thresh = 1.9 if zoom_level == "high" else 1.3
        
        clustering = AgglomerativeClustering(
            n_clusters=None, 
            distance_threshold=distance_thresh, 
            linkage='ward'
        )
        clustering.fit(embeddings)
        
        clusters = {}
        for idx, label in enumerate(clustering.labels_):
            if label not in clusters: clusters[label] = []
            clusters[label].append(scored_events[idx])
            
        rendered_timeline: List[ChronoEvent] = []
        
        for cluster_id, cluster_group in clusters.items():
            avatar_event, avatar_score = max(cluster_group, key=lambda x: x[1])
            if zoom_level == "high":
                if len(cluster_group) >= 3 or avatar_score > 1.5:
                    setattr(avatar_event, 'dynamic_sub_events_count', len(cluster_group) - 1)
                    rendered_timeline.append(avatar_event)
            else:
                setattr(avatar_event, 'dynamic_sub_events_count', len(cluster_group) - 1)
                rendered_timeline.append(avatar_event)
                
        return sorted(rendered_timeline, key=lambda x: x.date_normalized)

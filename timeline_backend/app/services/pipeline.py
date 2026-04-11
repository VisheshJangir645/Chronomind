import uuid
import logging
from typing import List

from app.schemas import ChronoEvent, ConfidenceMetrics
from app.services.embeddings import model_store
from app.services.extractor import TimelineExtractor
from app.services.temporal import TemporalReasoner
from app.services.confidence import ConfidenceScorer

logger = logging.getLogger(__name__)

class MasterPipeline:
    """
    The Core Orchestrator. 
    Linearly pipes raw text through all ML modules enforcing the Unified Pydantic Schema.
    Pipeline: Raw -> NER -> Temp Norm -> Confidence Scorer -> Embedding -> Schema -> Output 
    """
    def __init__(self):
        self.extractor = TimelineExtractor()
        self.temporal_reasoner = TemporalReasoner()
        self.confidence_scorer = ConfidenceScorer()
        self._loaded = False

    def load_infrastructure(self):
        """Triggered during FastAPI lifespan to warm up all GPUs/Memory."""
        if not self._loaded:
            model_store.load_models()
            self.extractor.load_models()
            self._loaded = True

    def process_document(self, text: str) -> List[ChronoEvent]:
        # Ensure models are loaded
        if not self._loaded:
            self.load_infrastructure()
            
        logger.info("1. Executing NER & Base Extraction")
        raw_events_dict = self.extractor.process_text(text)
        
        if not raw_events_dict:
            logger.warning("Extractor returned 0 events.")
            return []
        
        unified_events = []
        for raw in raw_events_dict:
            try:
                # Extract raw inputs
                raw_date = raw.get('date', 'Unknown')
                raw_desc = raw.get('description', '')
                raw_actor = raw.get('actor')
                raw_loc = raw.get('location')

                logger.info(f"2. Temporal Normalization for: {raw_date}")
                resolved_temporal = self.temporal_reasoner.resolve_date(raw_date)
                normalized_iso = resolved_temporal.get('start', raw_date) if resolved_temporal else raw_date
                
                logger.info("3. Calculating XAI Confidence")
                conf_payload = self.confidence_scorer._calculate_confidence({
                    'ner_confidence': 0.88,
                    'sources': ['User Uploaded Document Input'],
                    'is_absolute_date': bool(resolved_temporal is None or resolved_temporal.get('type') == 'isolated_bound')
                })
                
                # Extract confidence metrics from nested structure
                metrics_raw = conf_payload.get('confidence_metrics', {})
                factors = metrics_raw.get('factors', {})
                
                confidence = ConfidenceMetrics(
                    overall_score=min(metrics_raw.get('overall_score', 0.5), 1.0),
                    model_probability=factors.get('model_probability', 0.5),
                    source_agreement=factors.get('source_agreement', 0.5),
                    temporal_consistency=factors.get('temporal_consistency', 0.5)
                )

                logger.info("4. Generating Dense Vector Embeddings")
                dense_vector = model_store.get_embedding([raw_desc])[0].tolist()
                
                logger.info("5. Structuring into Unified ChronoEvent Schema")
                title_str = raw_desc[:50] if raw_desc else "Historical Event"
                
                event = ChronoEvent(
                    id=str(uuid.uuid4()),
                    title=title_str,
                    description=raw_desc,
                    date_normalized=normalized_iso,
                    raw_date_string=raw_date,
                    people=[raw_actor] if raw_actor else [],
                    locations=[raw_loc] if raw_loc else [],
                    confidence=confidence,
                    related_context=raw.get('related_context'),
                    embedding=dense_vector,
                    sources=['User Context']
                )
                
                unified_events.append(event)
            except Exception as e:
                logger.error(f"Failed to process event: {e}")
                continue
            
        logger.info(f"6. Processed {len(unified_events)} events successfully.")
        return unified_events

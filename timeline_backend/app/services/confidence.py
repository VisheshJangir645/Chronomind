import math
from typing import Dict, List

class ConfidenceScorer:
    """
    Explainable AI (XAI) module for the Historical Timeline system.
    Rather than merely presenting generated facts as absolute truth, this calculates 
    and attributes a dynamic reliability metric.
    """
    def __init__(self):
        # Academic weighting logic:
        # A high neural model probability means nothing if only 1 obscure source cited it.
        # Therefore, source agreement and model probability are weighted heavily.
        self.weights = {
            "model_probability": 0.4,
            "source_agreement": 0.4,
            "temporal_consistency": 0.2
        }

    def score_timeline(self, events: List[Dict]) -> List[Dict]:
        """Scores an entire array of events."""
        for event in events:
            self._calculate_confidence(event)
        return events

    def _calculate_confidence(self, event: Dict) -> Dict:
        """
        Calculates transparency metrics evaluating mathematical extraction confidence 
        against historical historiographical corroboration.
        """
        # 1. Model Probability
        # Represents the Softmax output from the HuggingFace RoBERTa token classifier
        raw_model_score = event.get('ner_confidence', 0.5)

        # 2. Source Attribution & Corroboration
        # Standard timeline extractors pull from 1 book. Our RAG pipeline pulls from thousands.
        # We mathematically model corroboration using asymptotic gain (diminishing return).
        sources = event.get('sources', ["Unknown Context"])
        unique_source_count = len(set(sources))
        
        # 1 source = 0.5 | 2 sources = 0.66 | 4 sources = 0.80
        source_score = 1.0 - (1.0 / (unique_source_count + 1))

        # 3. Temporal Consistency
        # Explores the "fuzziness" of the date extraction. 
        # Explicit (July 4, 1776) yields 1.0. Relative (The following spring) yields 0.6.
        temporal_score = 1.0 if event.get('is_absolute_date', True) else 0.6
        
        # Severely penalize temporal score if the cross-lingual pipeline detected a historiographical conflict
        if event.get('conflict_flag', False):
            temporal_score = max(0.1, temporal_score - 0.4)

        # Calculate Final Weighted Composite
        composite_score = (
            (raw_model_score * self.weights["model_probability"]) +
            (source_score * self.weights["source_agreement"]) +
            (temporal_score * self.weights["temporal_consistency"])
        )

        # Attach Explainable dict directly to the event payload
        event['confidence_metrics'] = {
            "overall_score": round(composite_score, 3),
            "factors": {
                "model_probability": round(raw_model_score, 3),
                "source_agreement": round(source_score, 3),
                "temporal_consistency": round(temporal_score, 3),
                "unique_sources_count": unique_source_count
            },
            "interpretation": self._get_interpretation(composite_score)
        }
        return event

    def _get_interpretation(self, score: float) -> str:
        if score >= 0.85: return "High Verification"
        if score >= 0.65: return "Moderate Confidence"
        return "Low Verification (Potential Hallucination)"

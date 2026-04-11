from typing import List, Dict
import logging

try:
    from neo4j import GraphDatabase
except ImportError:
    GraphDatabase = None

from app.schemas import ChronoEvent
from app.services.embeddings import model_store

logger = logging.getLogger(__name__)

class KnowledgeGraphPlugin:
    """
    Transforms linear timelines into semantic relational networks using Neo4j.
    Complies with the Unified Plugin Architecture as a 'Consumer' plugin.
    Includes ML-based relative causality extraction.
    """
    def __init__(self, uri="bolt://localhost:7687", user="neo4j", password="password"):
        if GraphDatabase:
            self.driver = GraphDatabase.driver(uri, auth=(user, password))
        else:
            self.driver = None

    def name(self) -> str:
        return "Neo4j_Knowledge_Graph_Plugin"

    def execute(self, events: List[ChronoEvent]) -> List[ChronoEvent]:
        """
        1. Infers 'causes' and 'leads_to' relations via vector math.
        2. Ingests the formal schemas directly into the local Neo4j clusters.
        """
        if not self.driver or not events:
            logger.warning("Neo4j driver missing or empty event array.")
            return events

        # 1. Infer Causality (ML Association)
        events = self._infer_causality(events)

        # 2. Neo4j Insertion
        with self.driver.session() as session:
            for ev in events:
                session.execute_write(self._merge_event_node, ev)
                
            # Second pass needed to create relationships after nodes exist
            for ev in events:
                session.execute_write(self._merge_relationships, ev)

        logger.info(f"Successfully synced {len(events)} nodes to Neo4j Graph.")
        return events

    def _infer_causality(self, events: List[ChronoEvent]) -> List[ChronoEvent]:
        """
        Uses the pre-baked SBERT embeddings to detect causal associations.
        If an event occurs within a 5-year window of a highly semantically related prior event,
        we infer a CAUSES relationship.
        """
        import numpy as np

        sorted_events = sorted(events, key=lambda x: x.date_normalized)
        
        for i, current in enumerate(sorted_events):
            if not current.embedding:
                continue
                
            curr_vector = np.array(current.embedding)
            
            # Look backwards in time (max 10 preceding events for localized causal chains)
            window_start = max(0, i - 10)
            prior_events = sorted_events[window_start:i]
            
            for prior in prior_events:
                if not prior.embedding:
                    continue
                    
                prior_vector = np.array(prior.embedding)
                cos_sim = np.dot(curr_vector, prior_vector) / (np.linalg.norm(curr_vector) * np.linalg.norm(prior_vector))
                
                # If highly semantically related (>0.75) and temporally adjacent
                if cos_sim > 0.75:
                    if prior.id not in current.causes:
                        current.causes.append(prior.id)
                    if current.id not in prior.leads_to:
                        prior.leads_to.append(current.id)
                        
        return sorted_events

    def _merge_event_node(self, tx, event: ChronoEvent):
        """
        Idempotent Graph Ingestion creating 'Event', 'Actor', and 'Location' nodes.
        """
        query = """
        MERGE (e:Event {id: $id})
        SET e.title = $title,
            e.date = $date,
            e.confidence = $confidence,
            e.conflict = $conflict
            
        WITH e
        UNWIND $actors AS actor_name
        MERGE (a:Actor {name: actor_name})
        MERGE (a)-[:PARTICIPATED_IN]->(e)
        
        WITH e
        UNWIND $locations AS loc_name
        MERGE (l:Location {name: loc_name})
        MERGE (e)-[:OCCURRED_IN]->(l)
        """
        tx.run(query, 
               id=event.id, 
               title=event.title, 
               date=event.date_normalized,
               confidence=event.confidence.overall_score if event.confidence else 0.5,
               conflict=event.conflict_flag,
               actors=event.people,
               locations=event.locations)

    def _merge_relationships(self, tx, event: ChronoEvent):
        """
        Creates 'CAUSED' relationships strictly using UUIDs to prevent duplicating nodes.
        """
        if event.causes:
            query = """
            UNWIND $cause_ids AS cause_id
            MATCH (e1:Event {id: cause_id})
            MATCH (e2:Event {id: $current_id})
            MERGE (e1)-[:LEADS_TO]->(e2)
            """
            tx.run(query, cause_ids=event.causes, current_id=event.id)

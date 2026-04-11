import logging
from neo4j import GraphDatabase

logger = logging.getLogger(__name__)

class KnowledgeGraphService:
    """
    Handles the construction and querying of the Semantic Historical Graph.
    Requires a running Neo4j instance.
    """
    def __init__(self, uri="bolt://localhost:7687", user="neo4j", password="password"):
        try:
            self.driver = GraphDatabase.driver(uri, auth=(user, password))
            # Verify connectivity
            self.driver.verify_connectivity()
            logger.info("Connected to Neo4j Knowledge Graph successfully.")
            self._init_schema()
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {e}. Graph features will be disabled.")
            self.driver = None

    def close(self):
        if self.driver:
            self.driver.close()

    def _init_schema(self):
        """Create uniqueness constraints to avoid duplicating historical figures/locations."""
        if not self.driver:
            return
        
        queries = [
            "CREATE CONSTRAINT event_id IF NOT EXISTS FOR (e:Event) REQUIRE e.id IS UNIQUE",
            "CREATE CONSTRAINT person_name IF NOT EXISTS FOR (p:Person) REQUIRE p.name IS UNIQUE",
            "CREATE CONSTRAINT loc_name IF NOT EXISTS FOR (l:Location) REQUIRE l.name IS UNIQUE"
        ]
        
        with self.driver.session() as session:
            for q in queries:
                session.run(q)

    def insert_extracted_timeline(self, events: list):
        """
        Converts the linear timeline extracted by the NLP pipeline into a connected graph.
        Expects `events` list containing dicts with keys: 
        [id, date, description, actors, locations, causes, leads_to]
        """
        if not self.driver:
            return

        with self.driver.session() as session:
            for event in events:
                # 1. Merge the Core Event Node
                session.run(
                    """
                    MERGE (e:Event {id: $id})
                    SET e.date = $date, e.description = $desc
                    """,
                    id=event.get("id"), date=event.get("date"), desc=event.get("description")
                )

                # 2. Link Actors (Person) -> PARTICIPATED_IN -> (Event)
                if event.get("actors"):
                    for actor in event["actors"]:
                        session.run(
                            """
                            MATCH (e:Event {id: $event_id})
                            MERGE (p:Person {name: $actor_name})
                            MERGE (p)-[:PARTICIPATED_IN]->(e)
                            """,
                            event_id=event.get("id"), actor_name=actor
                        )

                # 3. Link Locations (Location) <- OCCURRED_IN <- (Event)
                if event.get("locations"):
                    for loc in event["locations"]:
                        session.run(
                            """
                            MATCH (e:Event {id: $event_id})
                            MERGE (l:Location {name: $loc_name})
                            MERGE (e)-[:OCCURRED_IN]->(l)
                            """,
                            event_id=event.get("id"), loc_name=loc
                        )
                        
                # 4. Link Semantic Causal Chains via Relation Extraction (SpanBERT)
                # Ensure the target event exists first so we don't create orphaned edges
                if event.get("causes"):
                    for target_event_id in event["causes"]:
                        session.run(
                            """
                            MERGE (target:Event {id: $target_id})
                            WITH target
                            MATCH (source:Event {id: $source_id})
                            MERGE (source)-[:CAUSED_BY]->(target)
                            """,
                            source_id=event.get("id"), target_id=target_event_id
                        )

                if event.get("leads_to"):
                    for target_event_id in event["leads_to"]:
                        session.run(
                            """
                            MERGE (target:Event {id: $target_id})
                            WITH target
                            MATCH (source:Event {id: $source_id})
                            MERGE (source)-[:LEADS_TO]->(target)
                            """,
                            source_id=event.get("id"), target_id=target_event_id
                        )

    def query_actor_impact(self, actor_name: str):
        """
        Sample analytic query: Find all down-stream consequences triggered by an Event 
        this specific Person participated in.
        """
        if not self.driver:
            return []
            
        query = """
        MATCH (p:Person {name: $actor_name})-[:PARTICIPATED_IN]->(e1:Event)-[:LEADS_TO*1..3]->(consequence:Event)
        RETURN e1.description AS Source_Event, consequence.description AS Consequence
        """
        with self.driver.session() as session:
            result = session.run(query, actor_name=actor_name)
            return [{"Source": record["Source_Event"], "Consequence": record["Consequence"]} for record in result]

import uuid
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.schemas import TextRequest, QueryRequest, TimelineResponse, ChronoEvent
from app.services.wiki_retriever import wiki_retriever

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting ChronoMind Query-Driven API...")
    yield
    logger.info("Shutting down API...")

app = FastAPI(
    title="ChronoMind API",
    description="Query-driven historical timeline generation using Wikipedia.",
    version="3.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/api/v1/query", response_model=TimelineResponse, summary="Generate timeline from query")
async def query_timeline(request: QueryRequest):
    """
    Accepts a topic/person/event query. Fetches Wikipedia data,
    extracts events, and returns a structured chronological timeline.
    """
    try:
        data = wiki_retriever.fetch_historical_data(request.query)
        
        events = []
        for raw in data.get("events", []):
            event = ChronoEvent(
                id=str(uuid.uuid4()),
                title=raw.get("title", "Historical Event"),
                description=raw.get("description", ""),
                date_normalized=raw.get("date", "Unknown"),
                raw_date_string=raw.get("date", ""),
                people=raw.get("people", []),
                locations=[raw.get("location")] if raw.get("location") else [],
                relevance_score=raw.get("relevance_score"),
                related_to=raw.get("related_to"),
                sources=["Wikipedia"],
            )
            events.append(event)
        
        return TimelineResponse(
            events=events,
            topic=data.get("topic"),
            summary=data.get("summary"),
            thumbnail=data.get("thumbnail"),
            images=data.get("images", [])
        )
    except Exception as e:
        logger.error(f"Query pipeline failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/extract", response_model=TimelineResponse, summary="Extract from text (legacy)")
async def extract_timeline(request: TextRequest):
    """Backward-compatible text extraction endpoint."""
    try:
        from app.services.pipeline import MasterPipeline
        pipeline = MasterPipeline()
        events = pipeline.process_document(request.text)
        return TimelineResponse(events=events)
    except Exception as e:
        logger.error(f"Extraction failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health", status_code=200)
async def health_check():
    return {"status": "ok", "version": "3.0.0", "mode": "query-driven"}

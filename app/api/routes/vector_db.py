from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

from app.services.vector_db import ingest_items, ingest_text

router = APIRouter(prefix="/vector-ops", tags=["vector-ops"])


# A quick Pydantic model for document ingestion
class IngestItem(BaseModel):
    id: str
    text: str
    metadata: dict[str, Any] | None = None


# Another quick model for ingesting raw text
class IngestTextRequest(BaseModel):
    text: str


# Another quick model for similarity search request results
class SearchRequest(BaseModel):
    query: str = ""
    k: int = 3


# Endpoint for data ingestion
@router.post("/ingest-json")
async def ingest_json(items: list[IngestItem]):
    # Call the service method to ingest items
    count = ingest_items([item.model_dump() for item in items])
    return {"ingested:": count}


# Endpoint for raw text ingestion
@router.post("/ingest-text")
async def ingest_raw_text(request: IngestTextRequest):
    count = ingest_text(request.text)
    return {"ingested chunks: ": count}

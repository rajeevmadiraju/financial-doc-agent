"""
api/main.py
FastAPI application — upload docs, query the agent, manage sessions.
"""

import os
import shutil
import tempfile
from typing import List

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from loguru import logger

from backend.config import get_settings
from backend.ingestion.ingestor import ingest_document, get_qdrant_client, list_documents
from backend.agent.graph import run_agent

settings = get_settings()

app = FastAPI(
    title="Financial Document Intelligence Agent",
    description="Upload financial PDFs and ask questions using an AI agent with citations.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory session store (replace with Redis for production)
_sessions: dict = {}


# ── Schemas ────────────────────────────────────────────────────────────────

class QueryRequest(BaseModel):
    message: str
    session_id: str = "default"

class QueryResponse(BaseModel):
    answer: str
    session_id: str
    tool_calls_made: List[str]
    message_count: int

class DocumentInfo(BaseModel):
    name: str

class UploadResponse(BaseModel):
    document_id: str
    document_name: str
    pages_extracted: int
    tables_extracted: int
    chunks_stored: int
    message: str

class HealthResponse(BaseModel):
    status: str
    qdrant_connected: bool
    documents_count: int


# ── Endpoints ──────────────────────────────────────────────────────────────

@app.get("/health", response_model=HealthResponse)
def health_check():
    try:
        client = get_qdrant_client()
        docs = list_documents(client)
        return HealthResponse(status="ok", qdrant_connected=True, documents_count=len(docs))
    except Exception:
        return HealthResponse(status="degraded", qdrant_connected=False, documents_count=0)


@app.post("/upload", response_model=UploadResponse)
async def upload_document(file: UploadFile = File(...)):
    """Upload and ingest a PDF financial document."""
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name

    try:
        logger.info(f"Ingesting: {file.filename}")
        result = ingest_document(tmp_path, document_name=file.filename)
        return UploadResponse(
            **result,
            message=f"Successfully ingested '{file.filename}' — {result['chunks_stored']} chunks stored."
        )
    except Exception as e:
        logger.error(f"Ingestion failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        os.unlink(tmp_path)


@app.get("/documents", response_model=List[DocumentInfo])
def get_documents():
    """List all documents currently in the vector DB."""
    return [DocumentInfo(name=n) for n in list_documents(get_qdrant_client())]


@app.post("/query", response_model=QueryResponse)
def query_agent(request: QueryRequest):
    """Send a message to the financial agent. Maintains history per session_id."""
    history = _sessions.get(request.session_id, [])
    try:
        result = run_agent(user_message=request.message, conversation_history=history)
        _sessions[request.session_id] = result["updated_history"]
        return QueryResponse(
            answer=result["answer"],
            session_id=request.session_id,
            tool_calls_made=result["tool_calls_made"],
            message_count=len(result["updated_history"]),
        )
    except Exception as e:
        logger.error(f"Agent error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/session/{session_id}")
def clear_session(session_id: str):
    """Clear conversation history for a session."""
    _sessions.pop(session_id, None)
    return {"message": f"Session '{session_id}' cleared."}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.api.main:app", host="0.0.0.0", port=8000, reload=True)
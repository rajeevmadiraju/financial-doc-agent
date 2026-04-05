"""
retrieval/retriever.py
Semantic search over Qdrant with optional document filtering.
"""

from typing import List, Dict, Any, Optional

from langchain_openai import OpenAIEmbeddings
from qdrant_client.models import Filter, FieldCondition, MatchValue
from loguru import logger

from backend.config import get_settings
from backend.ingestion.ingestor import get_qdrant_client

settings = get_settings()


def get_embedder() -> OpenAIEmbeddings:
    return OpenAIEmbeddings(model=settings.embedding_model, api_key=settings.openai_api_key)


def search(
    query: str,
    top_k: int = None,
    document_filter: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    top_k = top_k or settings.top_k_retrieval
    client = get_qdrant_client()
    query_vector = get_embedder().embed_query(query)

    qdrant_filter = None
    if document_filter:
        qdrant_filter = Filter(
            should=[
                FieldCondition(key="document_name", match=MatchValue(value=name))
                for name in document_filter
            ]
        )

    results = client.search(
        collection_name=settings.collection_name,
        query_vector=query_vector,
        limit=top_k,
        query_filter=qdrant_filter,
        with_payload=True,
    )

    formatted = [
        {
            "text": r.payload["text"],
            "document_name": r.payload["document_name"],
            "document_id": r.payload.get("document_id", ""),
            "page_num": r.payload.get("page_num", 0),
            "has_tables": r.payload.get("has_tables", False),
            "score": round(r.score, 4),
        }
        for r in results
    ]
    logger.debug(f"Retrieved {len(formatted)} chunks for: '{query[:60]}'")
    return formatted


def search_two_documents(query: str, doc_a: str, doc_b: str, top_k_each: int = 4) -> Dict:
    return {
        "doc_a": search(query, top_k=top_k_each, document_filter=[doc_a]),
        "doc_b": search(query, top_k=top_k_each, document_filter=[doc_b]),
    }


def format_context(results: List[Dict[str, Any]]) -> str:
    if not results:
        return "No relevant information found."
    parts = [
        f"[Source {i}: {r['document_name']}, Page {r['page_num']}]\n{r['text']}"
        for i, r in enumerate(results, 1)
    ]
    return "\n\n---\n\n".join(parts)


def format_citations(results: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    seen, citations = set(), []
    for r in results:
        key = f"{r['document_name']}_{r['page_num']}"
        if key not in seen:
            seen.add(key)
            citations.append({
                "document": r["document_name"],
                "page": str(r["page_num"]),
                "score": str(r["score"]),
            })
    return citations
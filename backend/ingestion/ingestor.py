"""
ingestion/ingestor.py
PDF -> raw text + tables -> smart chunks -> embeddings -> Qdrant
"""

import hashlib
import re
from pathlib import Path
from typing import List, Dict, Any

import fitz  # PyMuPDF
import pdfplumber
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from loguru import logger

from backend.config import get_settings

settings = get_settings()


def get_qdrant_client() -> QdrantClient:
    return QdrantClient(
        url=settings.qdrant_url,
        api_key=settings.qdrant_api_key or None,
    )


def ensure_collection(client: QdrantClient, embedding_dim: int = 1536):
    existing = [c.name for c in client.get_collections().collections]
    if settings.collection_name not in existing:
        client.create_collection(
            collection_name=settings.collection_name,
            vectors_config=VectorParams(size=embedding_dim, distance=Distance.COSINE),
        )
        logger.info(f"Created collection: {settings.collection_name}")
    else:
        logger.info(f"Collection exists: {settings.collection_name}")


def extract_text_from_pdf(pdf_path: str) -> List[Dict[str, Any]]:
    pages = []
    doc = fitz.open(pdf_path)
    for page_num, page in enumerate(doc, start=1):
        text = _clean_text(page.get_text("text"))
        if text.strip():
            pages.append({"page_num": page_num, "text": text, "has_tables": False})
    doc.close()
    logger.info(f"Extracted {len(pages)} pages from {Path(pdf_path).name}")
    return pages


def extract_tables_from_pdf(pdf_path: str) -> List[Dict[str, Any]]:
    tables_text = []
    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages, start=1):
            for i, table in enumerate(page.extract_tables()):
                if not table:
                    continue
                rows = [" | ".join(str(c).strip() if c else "" for c in row) for row in table]
                text = f"[TABLE {i+1} on page {page_num}]\n" + "\n".join(rows)
                if text.strip():
                    tables_text.append({"page_num": page_num, "text": text, "has_tables": True})
    logger.info(f"Extracted {len(tables_text)} tables from {Path(pdf_path).name}")
    return tables_text


def _clean_text(text: str) -> str:
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\x00', '', text)
    return text.strip()


def chunk_pages(pages: List[Dict], document_name: str, document_id: str) -> List[Dict]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    chunks = []
    for page in pages:
        for i, split in enumerate(splitter.split_text(page["text"])):
            chunk_id = hashlib.md5(f"{document_id}_{page['page_num']}_{i}".encode()).hexdigest()
            chunks.append({
                "chunk_id": chunk_id,
                "text": split,
                "document_name": document_name,
                "document_id": document_id,
                "page_num": page["page_num"],
                "has_tables": page.get("has_tables", False),
                "chunk_index": i,
            })
    logger.info(f"Created {len(chunks)} chunks for: {document_name}")
    return chunks


def embed_and_store(chunks: List[Dict], client: QdrantClient):
    embedder = OpenAIEmbeddings(model=settings.embedding_model, api_key=settings.openai_api_key)
    texts = [c["text"] for c in chunks]
    logger.info(f"Embedding {len(texts)} chunks...")
    vectors = embedder.embed_documents(texts)

    points = [
        PointStruct(
            id=int(c["chunk_id"][:8], 16),
            vector=v,
            payload={
                "text": c["text"],
                "document_name": c["document_name"],
                "document_id": c["document_id"],
                "page_num": c["page_num"],
                "has_tables": c["has_tables"],
                "chunk_index": c["chunk_index"],
            }
        )
        for c, v in zip(chunks, vectors)
    ]

    for i in range(0, len(points), 100):
        client.upsert(collection_name=settings.collection_name, points=points[i:i+100])
    logger.info(f"Stored {len(points)} vectors in Qdrant.")


def ingest_document(pdf_path: str, document_name: str) -> Dict[str, Any]:
    document_id = hashlib.md5(document_name.encode()).hexdigest()[:12]
    pages = extract_text_from_pdf(pdf_path)
    tables = extract_tables_from_pdf(pdf_path)
    chunks = chunk_pages(pages + tables, document_name, document_id)

    if not chunks:
        raise ValueError(f"No extractable content found in {pdf_path}")

    client = get_qdrant_client()
    ensure_collection(client)
    embed_and_store(chunks, client)

    return {
        "document_id": document_id,
        "document_name": document_name,
        "pages_extracted": len(pages),
        "tables_extracted": len(tables),
        "chunks_stored": len(chunks),
    }


def list_documents(client: QdrantClient) -> List[str]:
    try:
        results = client.scroll(
            collection_name=settings.collection_name,
            limit=1000,
            with_payload=True,
            with_vectors=False,
        )
        return sorted({p.payload["document_name"] for p in results[0]})
    except Exception:
        return []
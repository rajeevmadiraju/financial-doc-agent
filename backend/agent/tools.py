"""
agent/tools.py
Tools available to the LangGraph agent.
"""

import re
from typing import Optional
from langchain_core.tools import tool

from backend.retrieval.retriever import search, search_two_documents, format_context, format_citations
from backend.ingestion.ingestor import get_qdrant_client, list_documents


@tool
def search_documents(query: str, document_name: Optional[str] = None) -> str:
    """
    Search across uploaded financial documents for information relevant to the query.
    Use for general questions about financials, metrics, or company info.

    Args:
        query: The question or topic to search for
        document_name: Optional — restrict search to a specific document
    """
    results = search(query, document_filter=[document_name] if document_name else None)
    if not results:
        return "No relevant information found."
    context = format_context(results)
    citations = "\n".join(f"  - {c['document']} (page {c['page']})" for c in format_citations(results))
    return f"{context}\n\nSOURCES:\n{citations}"


@tool
def compare_documents(query: str, document_a: str, document_b: str) -> str:
    """
    Compare information from two documents side by side.
    Use when asked to compare metrics or data across two reports or companies.

    Args:
        query: What to compare (e.g. "revenue growth", "operating expenses")
        document_a: Name of the first document
        document_b: Name of the second document
    """
    results = search_two_documents(query, document_a, document_b)
    return (
        f"=== FROM {document_a} ===\n{format_context(results['doc_a'])}\n\n"
        f"=== FROM {document_b} ===\n{format_context(results['doc_b'])}"
    )


@tool
def calculate_financial_ratio(expression: str) -> str:
    """
    Perform a financial calculation. Supports basic arithmetic.
    Use to compute P/E ratio, YoY growth %, margins, debt-to-equity, etc.

    Args:
        expression: Arithmetic expression e.g. "(150 - 120) / 120 * 100" for YoY growth
    """
    try:
        clean = re.sub(r'[^0-9+\-*/().\s]', '', expression)
        if not clean.strip():
            return "Invalid expression."
        return f"Result: {round(eval(clean), 4)}"
    except Exception as e:
        return f"Calculation error: {str(e)}"


@tool
def list_available_documents() -> str:
    """
    List all financial documents currently uploaded and available.
    Use at the start of a conversation or when the user asks what's available.
    """
    docs = list_documents(get_qdrant_client())
    if not docs:
        return "No documents uploaded yet."
    return "Available documents:\n" + "\n".join(f"  - {d}" for d in docs)


@tool
def summarize_section(document_name: str, section_topic: str) -> str:
    """
    Retrieve content from a specific section of a document.
    Use for named sections like 'risk factors', 'cash flow', 'revenue breakdown'.

    Args:
        document_name: The document to look in
        section_topic: Section to retrieve e.g. "risk factors", "operating expenses"
    """
    results = search(f"{section_topic} section", top_k=8, document_filter=[document_name])
    if not results:
        return f"Could not find '{section_topic}' in {document_name}."
    return f"Content from '{section_topic}' in {document_name}:\n\n{format_context(results)}"


AGENT_TOOLS = [
    search_documents,
    compare_documents,
    calculate_financial_ratio,
    list_available_documents,
    summarize_section,
]
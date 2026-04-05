"""
evaluation/evaluate.py
RAGAS evaluation pipeline for the RAG system.

Usage:
    python -m evaluation.evaluate
"""

import json
from pathlib import Path
from typing import List, Dict
from datetime import datetime

from datasets import Dataset
from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevancy, context_recall, context_precision
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from loguru import logger

from backend.config import get_settings
from backend.retrieval.retriever import search

settings = get_settings()

# ── Replace with real Q&A pairs from your uploaded documents ───────────────
SAMPLE_TEST_SET = [
    {
        "question": "What was the total revenue reported?",
        "ground_truth": "The total revenue is stated in the income statement section.",
        "document": None,
    },
    {
        "question": "What are the main risk factors mentioned?",
        "ground_truth": "Key risks include market, operational, and regulatory factors.",
        "document": None,
    },
    {
        "question": "What was the year-over-year revenue growth?",
        "ground_truth": "YoY revenue growth is discussed in the management analysis section.",
        "document": None,
    },
]


def build_ragas_dataset(test_set: List[Dict]) -> Dataset:
    from backend.agent.graph import run_agent

    data = {"question": [], "answer": [], "contexts": [], "ground_truth": []}

    for item in test_set:
        question = item["question"]
        logger.info(f"Evaluating: '{question[:60]}'")

        result = run_agent(question)
        contexts = search(question, document_filter=[item["document"]] if item.get("document") else None)

        data["question"].append(question)
        data["answer"].append(result["answer"])
        data["contexts"].append([c["text"] for c in contexts])
        data["ground_truth"].append(item["ground_truth"])

    return Dataset.from_dict(data)


def run_evaluation(test_set: List[Dict] = None) -> Dict:
    test_set = test_set or SAMPLE_TEST_SET
    logger.info(f"Running RAGAS on {len(test_set)} questions...")

    dataset = build_ragas_dataset(test_set)
    llm = ChatOpenAI(model=settings.llm_model, api_key=settings.openai_api_key)
    embeddings = OpenAIEmbeddings(model=settings.embedding_model, api_key=settings.openai_api_key)

    result = evaluate(
        dataset=dataset,
        metrics=[faithfulness, answer_relevancy, context_recall, context_precision],
        llm=llm,
        embeddings=embeddings,
    )

    scores = {
        "faithfulness": round(result["faithfulness"], 4),
        "answer_relevancy": round(result["answer_relevancy"], 4),
        "context_recall": round(result["context_recall"], 4),
        "context_precision": round(result["context_precision"], 4),
        "timestamp": datetime.now().isoformat(),
        "num_questions": len(test_set),
    }

    output_path = Path("evaluation/results.json")
    history = json.loads(output_path.read_text()) if output_path.exists() else []
    history.append(scores)
    output_path.write_text(json.dumps(history, indent=2))

    logger.info(f"Scores: {scores}")
    return scores


def load_results() -> List[Dict]:
    path = Path("evaluation/results.json")
    return json.loads(path.read_text()) if path.exists() else []


if __name__ == "__main__":
    scores = run_evaluation()
    print("\n=== RAGAS Evaluation Results ===")
    for k, v in scores.items():
        print(f"  {k}: {v}")
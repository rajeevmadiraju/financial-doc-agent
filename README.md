# 📊 Financial Document Intelligence Agent

An AI agent that ingests financial documents — annual reports, 10-Ks, earnings call transcripts — and lets you ask natural language questions across them. It reasons over multiple documents, compares data, calculates financial ratios on the fly, and cites every answer with document name and page number.

🔗 **[Live Demo](https://financial-doc-agent.vercel.app/)** · **[API Docs](https://web-production-3d94.up.railway.app/docs)**

---

## What it does

Upload any financial PDF and ask questions like:

- _"What was the total revenue and YoY growth?"_
- _"What are the main risk factors?"_
- _"Compare the operating expenses between these two reports"_
- _"Calculate the gross margin"_

The agent searches the document, reasons across multiple chunks, runs calculations, and responds with cited sources — document name and page number — so you always know where the answer came from.

---

## Architecture

```
User Query
    │
    ▼
React Frontend (Vercel)
    │
    ▼
FastAPI Backend (Railway)
    │
    ▼
LangGraph Agent
    ├── search_documents        → Qdrant semantic search
    ├── compare_documents       → Side-by-side retrieval
    ├── calculate_financial_ratio → Python arithmetic
    ├── summarize_section       → Section-targeted retrieval
    └── list_available_documents → Qdrant metadata scan
         │
         ▼
     GPT-4o-mini
         │
         ▼
     Answer + Citations
```

---

## Tech Stack

| Layer           | Technology                            |
| --------------- | ------------------------------------- |
| LLM             | GPT-4o-mini (OpenAI)                  |
| Embeddings      | text-embedding-3-small                |
| Vector DB       | Qdrant Cloud                          |
| Agent Framework | LangGraph                             |
| PDF Parsing     | PyMuPDF + pdfplumber                  |
| Evaluation      | RAGAS                                 |
| Backend         | FastAPI + Uvicorn                     |
| Frontend        | React + Tailwind CSS                  |
| Deployment      | Railway (backend) · Vercel (frontend) |

---

## Features

- 📄 **Smart PDF ingestion** — extracts text and tables separately, chunks by section
- 🔍 **Semantic search** — vector similarity over Qdrant with metadata filtering
- 🤖 **Agentic reasoning** — multi-step agent with 5 tools, decides what to call based on the question
- 📊 **Financial calculations** — computes ratios, margins, and YoY growth on the fly
- 🆚 **Multi-document comparison** — queries two documents side-by-side
- 📎 **Source citations** — every answer includes document name and page number
- 💬 **Conversation memory** — multi-turn chat with session history
- 🧪 **RAG evaluation** — RAGAS metrics: faithfulness, relevancy, recall, precision

---

## Running locally

**1. Clone and set up environment**

```bash
git clone https://github.com/rajeevmadiraju/financial-doc-agent
cd financial-doc-agent
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
```

**2. Configure environment**

```bash
cp .env.example .env
# Add your OPENAI_API_KEY and QDRANT credentials
```

**3. Start the backend**

```bash
uvicorn backend.api.main:app --reload
```

**4. Start the frontend**

```bash
cd frontend
npm install
npm run dev
```

Visit `http://localhost:5173` for the UI or `http://localhost:8000/docs` for the API.

---

## Project structure

```
financial-doc-agent/
├── backend/
│   ├── config.py              # Settings & environment variables
│   ├── ingestion/
│   │   └── ingestor.py        # PDF parsing, chunking, embedding, Qdrant storage
│   ├── retrieval/
│   │   └── retriever.py       # Semantic search with metadata filtering
│   ├── agent/
│   │   ├── tools.py           # 5 agent tool definitions
│   │   └── graph.py           # LangGraph agent with conversation memory
│   └── api/
│       └── main.py            # FastAPI endpoints
├── frontend/
│   └── src/
│       ├── App.jsx
│       └── components/
│           ├── Sidebar.jsx    # File upload + document list
│           ├── ChatWindow.jsx # Chat interface
│           └── Message.jsx    # Message bubbles with citations
├── evaluation/
│   └── evaluate.py            # RAGAS evaluation pipeline
├── docker-compose.yml
├── requirements.txt
└── .env.example
```

---

## API Endpoints

| Method   | Endpoint        | Description                     |
| -------- | --------------- | ------------------------------- |
| `GET`    | `/health`       | Check service and Qdrant status |
| `POST`   | `/upload`       | Upload and ingest a PDF         |
| `GET`    | `/documents`    | List all uploaded documents     |
| `POST`   | `/query`        | Ask the agent a question        |
| `DELETE` | `/session/{id}` | Clear conversation history      |

---

## Roadmap

- [ ] Add evaluation dashboard to the frontend UI
- [ ] Support Excel/CSV financial files
- [ ] German-language document support
- [ ] Fine-tuned embeddings on financial text
- [ ] Persistent session storage with Redis

---

## Author

**Rajeev Madiraju** — MSc AI @ BTU Cottbus-Senftenberg

[GitHub](https://github.com/rajeevmadiraju) · [LinkedIn](https://www.linkedin.com/in/rajeev-madiraju/)

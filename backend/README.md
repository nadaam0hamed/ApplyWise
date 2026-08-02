# ApplyWise Backend

FastAPI backend for ApplyWise. Provides REST endpoints and is structured for future LangChain, ChromaDB, and OpenAI integrations.

## Project structure

```
backend/
├── app/
│   ├── api/          # HTTP routes and routers
│   ├── agents/       # LangChain agents (future)
│   ├── chains/       # LangChain chains (future)
│   ├── rag/          # ChromaDB retrieval (future)
│   ├── services/     # Business logic
│   ├── models/       # Domain models
│   ├── schemas/      # Pydantic request/response schemas
│   ├── utils/        # Config and shared utilities
│   └── main.py       # FastAPI application entry point
├── requirements.txt
├── .env.example
└── README.md
```

## Quick start

### 1. Create a virtual environment

```bash
cd backend
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment

```bash
cp .env.example .env
```

Edit `.env` as needed. Defaults work for local development.

### 4. Run the server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Or from the `backend` directory with env-based host/port:

```bash
uvicorn app.main:app --reload
```

## Endpoints

| Method | Path     | Description              |
|--------|----------|--------------------------|
| GET    | `/`      | API welcome message      |
| GET    | `/health`| Health check             |
| GET    | `/docs`  | Swagger UI (interactive) |
| GET    | `/redoc` | ReDoc API documentation  |

## AI integrations

- **LangChain chains** — scholarship analysis pipeline (`app/chains/`)
- **ChromaDB / RAG** — hybrid retrieval (`app/rag/`)
- **Hugging Face Inference API** — remote LLM for analysis (`app/chains/huggingface_provider.py`). Uses the Hub Inference API via `huggingface_hub.InferenceClient`, not local model weights.
- **OpenAI** (future) — alternate LLM provider via the same `AnalysisLLMProvider` interface

### Hugging Face LLM (analysis)

Set these in `backend/.env` (see `.env.example`):

| Variable | Required | Description |
|----------|----------|-------------|
| `HF_TOKEN` | **Yes** (for HF analysis) | Hugging Face API token ([create one](https://huggingface.co/settings/tokens)). Also accepted: `HUGGINGFACEHUB_API_TOKEN`, `HUGGINGFACE_HUB_TOKEN`. |
| `HUGGINGFACE_INFERENCE_MODEL` | No | Hub model id for inference (default: `microsoft/Phi-3-mini-4k-instruct`). |

Example wiring (no HTTP endpoint yet):

```python
from app.chains import ApplicationAnalysisChain, HuggingFaceAnalysisLLMProvider
from app.rag.retriever import HybridRetriever

llm = HuggingFaceAnalysisLLMProvider().create_chat_model()
chain = ApplicationAnalysisChain(llm=llm, retriever=HybridRetriever(application_id="..."))
```

Other environment variables (RAG, server, OpenAI placeholders) are documented in `.env.example`.

## Development notes

- Run commands from the `backend/` directory so `app` resolves as a Python package.
- CORS is configured for `http://localhost:3000` by default to match the Next.js frontend.
- Set `APP_ENV=production` and `DEBUG=false` before deploying.

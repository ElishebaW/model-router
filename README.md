# GenAI LLM Model Router

An enterprise-grade, resilient **Model Router Application** that intelligently routes text prompts between **Google API** (`google/gemini-2.5-flash`) and **HuggingFace API** (`Qwen/Qwen2.5-7B-Instruct`) based on static text rules and dynamic API health failovers.

Featuring a **Python FastAPI** backend with exponential backoff & jitter retries, and a modern **Next.js (TypeScript)** frontend styled with Google's iconic four-color light theme. Designed for seamless deployment to **Google Cloud Run**.

---

## 🌟 Key Features

- 🎯 **Static Routing Rules**:
  - **Hugging Face (`Qwen/Qwen2.5-7B-Instruct`)**: Prompts with **< 10 words OR < 10 characters**.
  - **Google API (`google/gemini-2.5-flash`)**: Prompts with **&ge; 10 words AND &ge; 10 characters**.
- 🛡️ **Resilience with Backoff & Jitter**: All model calls are wrapped with randomized exponential backoff retries using `tenacity`.
- ⚡ **Automatic Dynamic Failover**: If the primary target (e.g. Google API) encounters rate limits, timeouts, or errors, the router automatically fails over to the secondary provider (Hugging Face).
- 🚨 **Graceful Degradation**: Clear user feedback and fallback notices if services experience outage.
- 🎨 **Google-Themed Light UI**: Next.js 16 + TypeScript dashboard with live routing target badge, real-time counters, failover simulation controls, and execution metrics.
- ☁️ **Google Cloud Ready**: Containerized with Dockerfiles and automated Cloud Run deployment scripts.

---

## 🏗️ Architecture Overview

```
                      ┌──────────────────────────────────────┐
                      │      Next.js Frontend (TS)           │
                      │  - Google Light Theme UI             │
                      │  - Live Target Route Badge           │
                      │  - Metrics & Failover Inspector      │
                      └──────────────────┬───────────────────┘
                                         │ HTTP REST API
                                         ▼
                      ┌──────────────────────────────────────┐
                      │       FastAPI Python Backend         │
                      │  - Static Length Router              │
                      │  - Input Sanitize & Validation       │
                      │  - Exponential Backoff & Jitter      │
                      │  - Dynamic Failover Engine           │
                      └──────────┬─────────────────┬─────────┘
                                 │                 │
             ┌───────────────────┴─┐             ┌─┴───────────────────┐
             │   Google Gemini API │             │   HuggingFace API   │
             │ google/gemini-2.5-flash           │ Qwen/Qwen2.5-7B-Instruct
             └─────────────────────┘             └─────────────────────┘
```

---

## ⚙️ Environment Configuration

Copy `.env.example` to create your local `.env` file:

```bash
cp .env.example .env
cp backend/.env.example backend/.env
```

Edit `backend/.env` to include your credentials:

```env
# Google API Key (for Gemini 2.5 Flash)
GOOGLE_API_KEY=your_google_api_key_here

# HuggingFace API Key (for Qwen2.5-7B-Instruct)
HUGGINGFACE_API_KEY=your_huggingface_api_key_here

# Optional Overrides
GOOGLE_MODEL=google/gemini-2.5-flash
HUGGINGFACE_MODEL=Qwen/Qwen2.5-7B-Instruct
WORD_COUNT_THRESHOLD=10
CHAR_COUNT_THRESHOLD=10
MAX_RETRIES=3
```

*Note: If no API keys are supplied, the application automatically runs in **Synthetic Demo Mode** for local testing.*

---

## 🚀 Quick Start (Local Development)

### 1. Start Python Backend

```bash
cd backend

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run FastAPI server
uvicorn app.main:app --reload --port 8000
```
Backend API will be running at: `http://localhost:8000` (Docs: `http://localhost:8000/docs`).

### 2. Start Next.js Frontend

In a new terminal tab:

```bash
cd frontend

# Install packages
npm install

# Start development server
npm run dev
```
Frontend UI will be running at: `http://localhost:3000`

---

## 🧪 Testing

### Backend Unit & Integration Tests (Pytest)

```bash
cd backend
source .venv/bin/activate
pytest tests/ -v
```

The test suite verifies:
- Static routing rules (<10 words/chars -> HuggingFace, >=10 -> Google).
- Prompt input validation & sanitization.
- Exponential backoff retry behavior.
- Automatic failover from Google API to Hugging Face on failure.
- Graceful degradation status when both providers fail.

### Frontend Production Build Test

```bash
cd frontend
npm run build
```

---

## ☁️ Deployment to Google Cloud Run

To deploy both frontend and backend to Google Cloud Run:

1. Ensure the Google Cloud SDK (`gcloud`) is installed and authenticated:
   ```bash
   gcloud auth login
   gcloud config set project YOUR_PROJECT_ID
   ```

2. Execute the deployment script:
   ```bash
   ./deploy_cloudrun.sh
   ```

Or deploy manually via Cloud Run:
```bash
# Deploy Backend
gcloud run deploy model-router-backend --source ./backend --region us-central1 --allow-unauthenticated

# Deploy Frontend
gcloud run deploy model-router-frontend --source ./frontend --region us-central1 --allow-unauthenticated
```

---

## 📂 Project Repository Structure

```
model-router/
├── backend/
│   ├── app/
│   │   ├── config.py           # Application settings & environment variables
│   │   ├── main.py             # FastAPI entrypoint & endpoints
│   │   ├── router.py           # Core routing & failover engine
│   │   ├── schemas.py          # Pydantic validation models
│   │   └── services/
│   │       ├── google_service.py # Gemini 2.5 Flash client with backoff
│   │       └── hf_service.py     # Qwen2.5-7B client with backoff
│   ├── tests/
│   │   └── test_router.py      # Pytest test suite
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── page.tsx        # Main dashboard UI
│   │   │   └── globals.css     # Google color design tokens
│   │   └── components/
│   │       ├── Header.tsx      # Top bar & status
│   │       ├── RouteBadge.tsx  # Dynamic live target preview
│   │       ├── MetricsPanel.tsx# Latency & failover statistics
│   │       └── ErrorAlert.tsx  # Graceful degradation alert
│   ├── Dockerfile
│   └── package.json
├── .env.example
├── deploy_cloudrun.sh
└── README.md
```

---

## 📄 License

MIT License. Designed for Staff AI Engineering & Production GenAI Workloads.

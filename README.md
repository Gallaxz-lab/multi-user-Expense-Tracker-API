# Multi-User Enterprise Expense Tracker & Context-Grounded Knowledge API

An enterprise-ready, provider-agnostic hybrid RAG architecture and autonomous agent gateway built with **FastAPI**, **LangChain**, and **LangGraph**. The platform unifies unstructured document intelligence with structured transactional bookkeeping—backed by **Azure Blob Storage**, **Azure AI Search**, and **PostgreSQL**.

---

## 🛠️ System Architecture & Data Flow

Use code with caution.[ Ingest Pipeline ] ──► Permanent Cloud Binary Storage ──► [ 📁 Azure Blob Containers ]│[ Chat /ask Query ] ──► Multi-Tenant OData Filter Shield ──► [ 🔍 Azure AI Search Index ]│ (Hybrid Vector + Token)▼[ Clean Data JSON ] ◄── Configurable LLM Factory Engine  ◄── [ 📶 Cross-Encoder Reranker ]
1. **Secure Storage Lake:** Raw PDF compliance documents and expense guidelines are streamed directly to **Azure Blob Storage** for permanent cloud archiving.
2. **Multi-Tenant Ingestion:** Text is extracted, parsed into semantic shards, metadata-tagged with the authenticated user context (`owner_username`), and indexed persistently in **Azure AI Search**.
3. **Optimized Cloud Retrieval:** Incoming queries use direct Azure Search Client interfaces to fire multi-engine **Hybrid Searches** (Dense Vectors + BM25 Keywords) coupled with strict OData filter constraints (`owner_username eq 'user'`), completely isolating tenant visibility walls.
4. **Cross-Encoder Reranking:** Results are scored and pruned locally down to high-fidelity context shards to eliminate token noise, block prompt contamination, and mitigate AI hallucinations.
5. **Grounded JSON Generation:** The context is processed via a decoupled model factory (.env toggled across **Gemini**, **OpenAI**, or **Anthropic**) enforcing strict **Pydantic schema synthesis** to decouple conversational telemetry text from isolated page citations.
6. **Cross-Linked Relational Logging:** Live expense items posted to the database engine automatically trigger parallel, asynchronous vector pipeline loops to evaluate real-time transactions against compliance policies stored in the cloud.

---

## ✨ Production Capabilities & Features

*   🔀 **Provider-Agnostic LLM Factory:** Swap your core orchestration intelligence instantly across Google Gemini, OpenAI GPT, or Anthropic Claude via environment variables without touching backend code.
*   🛡️ **Multi-Tenant Security Silos:** Cryptographically signed JWT access handshakes map individual database schemas. Sub-query filters execute directly inside Azure indices, preventing cross-user data exposure.
*   ⏱️ **Distributed PostgreSQL Rate-Limiting:** Shared transactional database tracking tables run a high-priority token bucket limiter (`max_burst=2`, `refill=0.1/s`) across scaled cloud containers on Render, rendering the system immune to high-speed API resource depletion attacks.
*   🛑 **Adversarial Input Sanitization:** Intercepts malicious string control command patterns ("ignore previous instructions") at the gateway before text reaches your model pipelines.
*   📊 **End-to-End Trace Observability:** Every request attaches a unique tracking token ID computing real-time stopwatch metrics, heuristic token usage maps, and true transactional USD costs.
*   🔧 **Self-Healing Schema Synchronization:** Startup hooks programmatically run raw database updates on boot to add fields (`role`, `is_active`, `category`), preventing application crashes when moving between legacy and updated enterprise tables.

---

## 📁 Repository Directory Structure

```text
├── app/
│   ├── database/
│   │   └── connection.py          # Database engines & transaction worker pool sessions
│   ├── models/
│   │   ├── expense.py             # SQLAlchemy model for relational expense records
│   │   └── user.py                # SQLAlchemy model for authenticated enterprise profiles
│   ├── routers/
│   │   ├── auth.py                # JWT authentication gates & security mapping
│   │   ├── expenses.py            # Live transaction logger & real-time RAG compliance audit
│   │   └── search.py              # Consolidated secure API gateway endpoints
│   ├── schemas/
│   │   ├── auth.py                # maps security payload tokens
│   │   ├── expense.py             # map to updated category and timestamp fields
│   │   └── support_state.py       # Pydantic input schemas & LangGraph state dicts
│   ├── services/
│   │   ├── document_processor.py  # Azure Blob Streaming & Text Chunk Ingestion
│   │   ├── model_factory.py       # Decoupled model provider switch router
│   │   ├── observability.py       # Stopwatch trace telemetry logger & metrics cost analyzer
│   │   ├── security_guardrails.py # Input sanitizers, payload caps, and Postgres limiters
│   │   └── vector_store.py        # Managed Azure AI Search Cloud Vector database connectors
│   ├── main.py                    # Master app startup event & creation binding engine
├── tests/
│   └── pentest_suite.py           # Automated security validation attack suite scripts
├── .env                           # Environment configuration credential matrices
└── requirements.txt               # Core enterprise software deployment dependencies
```

---

## 🚀 Local Installation & Deployment

### 1. Clone & Setup Workspace Environment
```bash
git clone https://github.com
cd multi-user-Expense-Tracker-API
python -m venv venv
source venv/Scripts/activate  # On Windows
pip install -r requirements.txt
```

### 2. Configure Environment Properties (`.env`)
Create a `.env` file right next to your root directory matching this schema matrix:
```env
DB_USER="postgres"
DB_PASSWORD="your_database_password"
DB_HOST="localhost"
DB_PORT=5432
DB_NAME="expense_tracker"

SECRET_KEY="your_private_sha256_encryption_secret_key"
ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE_MINUTES=60

LLM_PROVIDER="gemini" # Options: gemini | openai | anthropic
GEMINI_API_KEY="AIzaSyYourActualGoogleAIStudioKey"

AZURE_STORAGE_CONNECTION_STRING="DefaultEndpointsProtocol=https;AccountName=..."
AZURE_STORAGE_CONTAINER_NAME="user-policy-documents"

AZURE_SEARCH_ENDPOINT="https://windows.net"
AZURE_SEARCH_API_KEY="YourSearchPrimaryAdminKey"
AZURE_SEARCH_INDEX_NAME="enterprise-knowledge-base"
```

### 3. Initialize & Execute API App
```bash
uvicorn app.main:app --reload
```
Navigate your browser window tab directly to `http://127.0.0` to interface with the complete, interactive Swagger UI control dashboard.

---

## 🔬 Automated Penetration Testing
The system contains a dedicated, standalone integration security check module to run high-velocity validation passes against potential threat vectors.

Execute the suite using:
```bash
python tests/pentest_suite.py
```

### Handled Security Status Matrix:
*   **Test 1 (Blank/Whitespace Query Input):** Gateways intercept early and respond with a secure `422 Unprocessable Entity` rather than leaking traceback logs into a `500` server crash.
*   **Test 3 (Prompt Injection Jailbreak Attempt):** Sanitizers capture instructions targeting password key outputs or role overrides and issue a defensive `400 Bad Request`.
*   **Test 4 (Missing JWT Authentication Credentials):** Security handlers automatically drop unauthenticated traffic blocks with a `401 Unauthorized`.
*   **Test 6 (High-Speed Request Flooding Spam):** The PostgreSQL shared rate-limit table captures bursts over the limit thresholds and throws a persistent `429 Too Many Requests` speed wall across all server containers.
# VERIF-AI Backend — Gemini CLI Agent Context

## 🧠 WHO YOU ARE

You are a **senior backend engineer + LangGraph architect** building VERIF-AI for a hackathon. You write production-quality Python/FastAPI code using LangGraph + LangChain + Gemini as the AI stack.

**🔴 AUTO-UPDATE AFTER EVERY TASK (do all 3 without being asked):**
1. Mark `[x]` in `## 📌 PROJECT STATUS` in this file
2. Update `contracts/CONTRACT.md` with new/changed endpoint (full spec)
3. `@git commit -m "feat: [feature name]" && git push`

---

## 📦 PROJECT IDENTITY

| Item | Value |
|------|-------|
| Project | VERIF-AI — AI Academic Profile & Skill Verification |
| Backend repo | `github.com/tejasM17/verif-ai-backend` |
| Frontend repo | `github.com/SharathKumar-M/verif-ai-frontend` (READ-ONLY) |
| Backend deploy | Render.com |
| Frontend deploy | Vercel |
| Goal | Working demo in 48 hours |
| Differentiator | LangGraph cross-agent reasoning + Grok-style live research logs |

---

## 📁 REPO LAYOUT — WHERE EVERYTHING LIVES

```
verif-ai-backend/          ← GitHub: tejasM17/verif-ai-backend
├── GEMINI.md              ← THIS file — committed, Gemini CLI reads it
├── AGENTS.md              ← OpenCode reads this — committed
├── opencode.json          ← OpenCode config — committed
├── .gemini/
│   └── settings.json      ← Gemini CLI MCP config — committed
│
├── contracts/             ← API contract — committed, brother reads via git clone
│   ├── CONTRACT.md        ← THE single source of truth for all endpoints
│   ├── resume-agent.md    ← System prompt for Resume Agent
│   ├── certificate-agent.md
│   └── github-agent.md
│
├── app/
│   ├── api/v1/
│   │   ├── auth.py
│   │   ├── documents.py
│   │   ├── analysis.py
│   │   ├── profile.py
│   │   ├── discover.py
│   │   └── verification.py
│   ├── services/
│   │   ├── graph/
│   │   │   ├── state.py
│   │   │   ├── supervisor.py
│   │   │   ├── resume_node.py
│   │   │   ├── certificate_node.py
│   │   │   ├── github_node.py
│   │   │   ├── cross_reference.py
│   │   │   ├── final_decision.py
│   │   │   └── graph_builder.py
│   │   ├── tools/
│   │   │   ├── pdf_tools.py
│   │   │   ├── image_tools.py
│   │   │   ├── github_tools.py
│   │   │   └── stylometry_tools.py
│   │   ├── streaming.py
│   │   ├── trust_score.py
│   │   └── discovery_service.py
│   ├── models/
│   │   ├── user.py
│   │   └── document.py
│   ├── schemas/
│   │   ├── auth.py
│   │   ├── document.py
│   │   ├── analysis.py
│   │   ├── profile.py
│   │   └── discover.py
│   ├── core/
│   │   ├── database.py
│   │   ├── firebase.py
│   │   ├── config.py
│   │   └── langchain_setup.py
│   └── main.py
│
├── tests/
│   ├── conftest.py
│   ├── test_auth.py
│   ├── test_documents.py
│   ├── test_resume_node.py
│   ├── test_certificate_node.py
│   ├── test_github_node.py
│   ├── test_graph.py
│   ├── test_cross_reference.py
│   ├── test_discover.py
│   └── test_profile.py
│
├── bruno-collection/      ← Bruno API tests — committed so brother can use them
├── scripts/
│   └── seed_fake_data.py  ← Creates all fake test users/companies
│
├── .env                   ← NEVER committed
├── .env.example           ← Committed (empty values)
├── .gitignore
├── requirements.txt
└── render.yaml
```

---

## 🗄️ DATA STORAGE — STRICT SPLIT (Never Mix These)

| What | Where | Why |
|------|-------|-----|
| Auth + sessions | Firebase Auth | Battle-tested, JWT built-in |
| User profiles, results, logs | Firebase Firestore | Structured, real-time |
| Resume PDFs, certificate images | MongoDB GridFS | Binary files |
| Documents metadata | MongoDB `documents` collection | Links GridFS IDs to Firebase UIDs |

### Firestore Collections
```
/users/{firebase_uid}          → email, role, display_name, created_at
/verifications/{id}            → student_uid, trust_score, verdict, all agent scores
/ai_results/{id}               → student_uid, agent_type, scores, flags, summary
/research_logs/{id}            → result_id, student_uid, agent_type, logs[]
/profiles/{firebase_uid}       → is_public, skills[], domain, trust_score (for search)
/shortlists/{recruiter_uid}    → student_uids[]
```

### MongoDB Collections
```
documents    → firebase_uid, type, gridfs_id, filename, hash_sha256, status
GridFS:
  resumes.files / resumes.chunks       → resume PDF bytes
  certificates.files / certificates.chunks → certificate bytes
```

---

## 🌐 STUDENT ↔ RECRUITER FLOW

```
STUDENT:
  Register → Upload (resume + certs + GitHub URL) →
  Trigger Analysis → Watch live research log →
  Get Trust Score → Toggle is_public=true →
  Profile searchable by recruiters

RECRUITER:
  Register → Go to Discover →
  Search: skills + min_trust + domain + location →
  View student profile + full research log →
  Shortlist students

3 WAYS TO CONNECT:
  1. Student shares link: verif-ai.app/profile/{uid}
  2. Recruiter searches and student appears in results
  3. Recruiter browses all public verified profiles (sorted by trust score)
```

---

## 🏗️ COMPLETE TECH STACK

| Layer | Technology | Package |
|-------|-----------|---------|
| Language | Python 3.11+ | — |
| Framework | FastAPI | `fastapi` |
| Agent Framework | **LangGraph** | `langgraph` |
| Agent Chains | LangChain | `langchain` |
| LLM Text | Gemini 2.5 pro | `langchain-google-genai` |
| LLM Vision | Gemini 2.5 Pro | `langchain-google-genai` |
| MCP in Python | LangChain MCP Adapters | `langchain-mcp-adapters` |
| Streaming | astream_events v3 | built-in |
| Structured Output | Pydantic + with_structured_output | `pydantic>=2.7` |
| Tracing | LangSmith | `langsmith` |
| MongoDB Async | Motor | `motor` |
| MongoDB ODM | Beanie | `beanie` |
| File Storage | MongoDB GridFS | via Motor |
| Auth | Firebase Admin SDK | `firebase-admin` |
| Firestore | Firebase Firestore | `firebase-admin` |
| PDF | pdfplumber + pypdf | both |
| OCR | pytesseract | `pytesseract` |
| Image Forensics | Pillow | `Pillow` |
| GitHub OSINT | PyGithub + radon | both |
| HTTP | httpx | `httpx` |
| Server | uvicorn | `uvicorn` |
| Tests | pytest-asyncio | `pytest-asyncio` |

**NEVER USE:** requests, SQLAlchemy, Django, Flask, synchronous Motor, raw google-generativeai

---

## 🤖 LANGGRAPH ARCHITECTURE

### Shared State (the brain all agents read/write)
```python
class VerificationState(TypedDict):
    student_uid: str
    resume_doc_id: str
    cert_doc_ids: list[str]
    github_url: str
    resume_result: Optional[dict]
    cert_result: Optional[dict]
    github_result: Optional[dict]
    cross_ref_findings: Optional[list]
    research_logs: Annotated[list[dict], operator.add]   # append-only
    flags: Annotated[list[dict], operator.add]           # append-only
    completed_agents: Annotated[list[str], operator.add] # append-only
    overall_trust_score: Optional[float]
    verdict: Optional[str]
```

### Graph Flow
```
START → supervisor → [resume_node ─┐
                   → cert_node    ─┼─ all parallel
                   → github_node ─┘]
       → cross_reference → final_decision → END
```

### Trust Score (NEVER CHANGE)
```
trust_score = resume×0.40 + cert×0.35 + github×0.25
```

### Streaming (astream_events v3)
```python
async for event in agent.astream_events(input, version="v3"):
    "on_chat_model_stream" → yield thinking_token
    "on_tool_start"        → yield research_step_start
    "on_tool_end"          → yield research_step_complete
    "on_chain_end"         → yield analysis_complete
```

---

## 🔐 AUTH PATTERN

```python
# app/core/firebase.py — EXACT pattern, never change
from firebase_admin import auth
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

bearer = HTTPBearer()

async def verify_firebase_token(creds = Depends(bearer)) -> dict:
    try:
        return auth.verify_id_token(creds.credentials)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")

async def require_student(user = Depends(verify_firebase_token)) -> dict:
    if user.get("role") != "student":
        raise HTTPException(status_code=403, detail="Students only")
    return user

async def require_recruiter(user = Depends(verify_firebase_token)) -> dict:
    if user.get("role") != "recruiter":
        raise HTTPException(status_code=403, detail="Recruiters only")
    return user
```

---

## 📡 API RESPONSE FORMAT (Always consistent)

```python
# Success
{"success": True, "data": {...}, "message": "Done"}
# Error
{"success": False, "error": "Short title", "detail": "Full description"}
# Async job started
{"success": True, "data": {"job_id": "...", "status": "analyzing", "websocket_url": "..."}}
```

---

## 📋 CODING RULES

1. Read `contracts/CONTRACT.md` before writing any endpoint
2. Update `contracts/CONTRACT.md` after any endpoint change
3. Update `## 📌 PROJECT STATUS` after each task
4. All `async def` — no synchronous I/O anywhere
5. All LLM calls via `langchain-google-genai`
6. All agents MUST produce `research_steps[]` — never skip
7. All streaming via `astream_events(version="v3")`
8. All structured output via `with_structured_output(schema, method="json_schema")`
9. Always try/except Gemini + GitHub + Firestore calls with fallback
10. Agents always parallel via LangGraph (never asyncio.gather for agents)
11. Never `requests` — always `httpx`
12. Never commit `.env`

---

## 🔐 ENVIRONMENT VARIABLES

```bash
# MongoDB (files only)
MONGODB_URI=mongodb+srv://...
MONGODB_DB_NAME=verifai

# Firebase (auth + all structured data)
FIREBASE_PROJECT_ID=your-project-id
FIREBASE_CREDENTIALS_JSON={"type":"service_account",...}

# Google AI
GEMINI_API_KEY=from-aistudio.google.com
GOOGLE_API_KEY=same-as-above

# LangSmith
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=from-smith.langchain.com
LANGCHAIN_PROJECT=verif-ai-hackathon

# External
GITHUB_TOKEN=your-github-pat
BRAVE_API_KEY=your-brave-key

# App
ALLOWED_ORIGINS=http://localhost:3000,https://verif-ai-frontend.vercel.app
PORT=8000
ENVIRONMENT=development
```

---

## ⚡ MCP TOOLS

| Command | Use for |
|---------|---------|
| `@mongodb` | Seed data, query collections |
| `@github` | Push code, PRs |
| `@render` | Deploy backend |

---

## 🚀 RENDER DEPLOYMENT

```yaml
services:
  - type: web
    name: verif-ai-backend
    runtime: python
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn app.main:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: MONGODB_URI
        sync: false
      - key: GEMINI_API_KEY
        sync: false
      - key: FIREBASE_CREDENTIALS_JSON
        sync: false
      - key: GITHUB_TOKEN
        sync: false
      - key: BRAVE_API_KEY
        sync: false
      - key: LANGCHAIN_API_KEY
        sync: false
      - key: ENVIRONMENT
        value: production
```

---

## 🚫 NEVER DO

- Touch `verif-ai-frontend` repo
- Skip `research_steps[]` in any agent output
- Run agents sequentially (use LangGraph parallel)
- Use `requests` library
- Expose raw Gemini response to frontend
- Use synchronous Motor calls
- Hardcode API keys
- Commit `.env`
- Manually edit `contracts/CONTRACT.md` — only update it when you add/change endpoints

---

## 📌 PROJECT STATUS — AGENTS AUTO-UPDATE THIS

### Phase 0: Foundation
- [ ] `requirements.txt`
- [ ] `.env.example` + `.gitignore`
- [ ] `core/config.py`
- [ ] `core/database.py` (Motor + GridFS)
- [ ] `core/firebase.py` (Admin + Firestore + JWT deps)
- [ ] `core/langchain_setup.py`
- [ ] `main.py` (lifespan + CORS + health endpoint)
- [ ] `contracts/CONTRACT.md` (initial empty shell)

### Phase 1: Auth
- [ ] `models/user.py`
- [ ] `schemas/auth.py`
- [ ] `api/v1/auth.py`
- [ ] Bruno: auth collection created

### Phase 2: File Upload
- [ ] `models/document.py`
- [ ] `schemas/document.py`
- [ ] `api/v1/documents.py`
- [ ] Bruno: documents collection created

### Phase 3: LangGraph Agents
- [ ] `services/graph/state.py`
- [ ] `services/tools/stylometry_tools.py`
- [ ] `services/tools/pdf_tools.py`
- [ ] `services/tools/image_tools.py` (ELA mandatory)
- [ ] `services/tools/github_tools.py`
- [ ] `services/graph/supervisor.py`
- [ ] `services/graph/resume_node.py`
- [ ] `services/graph/certificate_node.py`
- [ ] `services/graph/github_node.py`
- [ ] `services/graph/cross_reference.py`
- [ ] `services/graph/final_decision.py`
- [ ] `services/graph/graph_builder.py`
- [ ] `services/streaming.py`
- [ ] `services/trust_score.py`
- [ ] `api/v1/analysis.py`
- [ ] Bruno: analysis collection created

### Phase 4: Discovery
- [ ] `services/discovery_service.py`
- [ ] `schemas/profile.py` + `schemas/discover.py`
- [ ] `api/v1/profile.py`
- [ ] `api/v1/discover.py`
- [ ] `api/v1/verification.py`
- [ ] Bruno: profile + discover collections created

### Phase 5: Fake Data + Tests + Deploy
- [ ] `scripts/seed_fake_data.py` (5 students + 2 recruiters + companies)
- [ ] `tests/conftest.py`
- [ ] All test files
- [ ] `render.yaml` + deployed to Render
- [ ] `README.md` updated

**contracts/CONTRACT.md last updated:** _not yet — agent updates this_

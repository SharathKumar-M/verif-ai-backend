# VERIF-AI Backend — Gemini CLI Agent Context
> File location: `verif-ai-backend/GEMINI.md`
> Gemini CLI reads this automatically on every prompt.
> Run `/memory reload` if changes don't take effect.

---

## 🧠 WHO YOU ARE

You are a **senior backend engineer + LangGraph agent architect** building VERIF-AI — an AI-powered academic credential verification platform for a hackathon. You use **LangGraph + LangChain + Gemini** as the core AI stack.

**🔴 THREE AUTO-UPDATE RULES — DO ALL THREE after EVERY completed task:**
1. Change `[ ]` to `[x]` in `## 📌 PROJECT STATUS` in this file
2. Update `contracts/CONTRACT.md` with any new/changed endpoint
3. Run `@git commit -m "feat: [name]" && git push` via MCP

---

## 📦 PROJECT IDENTITY

- **Project:** VERIF-AI — AI Academic Profile & Skill Verification System
- **Backend repo:** `verif-ai-backend`
- **Frontend repo:** `verif-ai-frontend` (READ-ONLY — NEVER touch)
- **Hackathon goal:** Working demo in 48 hours
- **Core differentiator:** LangGraph agents that talk to each other + Grok-style live research logs

---

## 🌐 HOW STUDENT ↔ RECRUITER FLOW WORKS

This is critical architecture — understand it fully before writing any endpoint.

```
STUDENT FLOW:
  1. Student registers (role=student) via Firebase Auth
  2. Student uploads: resume PDF + certificate images + GitHub URL
  3. Student clicks "Analyze My Profile"
  4. LangGraph pipeline runs → saves results to MongoDB
  5. Student's profile becomes DISCOVERABLE (if they set profile_public=true)
  6. Student receives their own Trust Score in their dashboard

RECRUITER FLOW:
  1. Recruiter registers (role=recruiter) via Firebase Auth
  2. Recruiter goes to "Discover Talent" page
  3. Recruiter can:
     a. SEARCH by: skills, trust score range, location, domain
     b. BROWSE: public verified student profiles
     c. DIRECT LINK: student shares their verification URL
  4. Recruiter views full verification: Trust Score + research log
  5. Recruiter can "shortlist" student or "request contact"

CONNECTION MECHANISM:
  - Students have a shareable link: /profile/{student_uid}
  - Students can toggle profile_public = true/false
  - Verified students appear in recruiter search index
  - Trust Score acts as a filter: recruiter sets minimum score threshold
```

**Key API endpoints this requires:**
```
POST /api/v1/profile/publish      → Student makes profile public/private
GET  /api/v1/discover             → Recruiter browses all public verified profiles
GET  /api/v1/discover/search      → Recruiter searches: ?skills=Python&min_trust=70
GET  /api/v1/profile/{uid}        → Anyone views a public student profile
POST /api/v1/shortlist/{uid}      → Recruiter shortlists a student
GET  /api/v1/recruiter/shortlist  → Recruiter views their shortlist
```

---

## 🏗️ COMPLETE TECH STACK

| Layer | Technology | Package | Rule |
|-------|-----------|---------|------|
| Language | Python 3.11+ | — | Always async |
| Framework | FastAPI | `fastapi` | lifespan pattern |
| **Agent Framework** | **LangGraph** | `langgraph` | StateGraph for all agents |
| **Agent Chains** | **LangChain** | `langchain` | Tools, prompts, chains |
| **LLM Text** | **Gemini 1.5 Flash** | `langchain-google-genai` | Resume + GitHub agents |
| **LLM Vision** | **Gemini 1.5 Pro** | `langchain-google-genai` | Certificate agent |
| **MCP in Python** | **LangChain MCP Adapters** | `langchain-mcp-adapters` | Web search tool in agents |
| **Streaming** | LangChain astream_events v3 | built-in | Research log live stream |
| **Structured Output** | Pydantic + with_structured_output | `pydantic v2` | Force JSON from Gemini |
| **Observability** | LangSmith | `langsmith` | Trace every agent step |
| Async MongoDB | Motor | `motor` | Never sync |
| MongoDB ODM | Beanie | `beanie` | Document models |
| File Storage | MongoDB GridFS | via Motor | Resumes + certs ONLY |
| Auth | Firebase Admin SDK | `firebase-admin` | JWT verification |
| Firestore | Firebase Firestore | `firebase-admin` | User data + results |
| PDF | pdfplumber + pypdf | both | Text + metadata |
| OCR | pytesseract | `pytesseract` | Certificate images |
| Image Forensics | Pillow | `Pillow` | ELA analysis |
| GitHub OSINT | PyGithub | `PyGithub` | Repo/commit data |
| Code Complexity | radon | `radon` | Cyclomatic complexity |
| HTTP | httpx | `httpx` | NEVER use requests |
| Testing | pytest-asyncio | `pytest-asyncio` | All tests async |
| Server | uvicorn | `uvicorn` | ASGI server |

---

## 📁 EXACT FOLDER STRUCTURE

```
verif-ai-backend/
├── GEMINI.md                           ← This file (auto-update PROJECT STATUS)
├── app/
│   ├── api/v1/
│   │   ├── auth.py                     # Firebase JWT + user sync to Firestore
│   │   ├── documents.py                # MongoDB GridFS file uploads
│   │   ├── analysis.py                 # Trigger LangGraph + WebSocket stream
│   │   ├── profile.py                  # Student profile: publish/unpublish
│   │   ├── discover.py                 # Recruiter: browse + search students
│   │   └── verification.py             # Get results + shortlist
│   ├── services/
│   │   ├── graph/
│   │   │   ├── state.py                # VerificationState TypedDict (shared brain)
│   │   │   ├── supervisor.py           # Entry node: dispatch all agents
│   │   │   ├── resume_node.py          # Agent 1: LangChain + Gemini Flash
│   │   │   ├── certificate_node.py     # Agent 2: LangChain + Gemini Vision
│   │   │   ├── github_node.py          # Agent 3: LangChain + Deep Agent + MCP
│   │   │   ├── cross_reference.py      # Cross-agent findings: GitHub vs Resume
│   │   │   ├── final_decision.py       # Trust score + verdict + save to Firestore
│   │   │   └── graph_builder.py        # StateGraph assembly — compile here
│   │   ├── tools/
│   │   │   ├── pdf_tools.py            # pdfplumber + pypdf LangChain tools
│   │   │   ├── image_tools.py          # pytesseract + ELA LangChain tools
│   │   │   ├── github_tools.py         # PyGithub LangChain tools
│   │   │   └── stylometry_tools.py     # Burstiness, TTR, readability
│   │   ├── streaming.py                # astream_events v3 → WebSocket/SSE
│   │   ├── trust_score.py              # Weighted formula
│   │   └── discovery_service.py        # Search index + recruiter queries
│   ├── models/
│   │   ├── user.py                     # Beanie: users (MongoDB)
│   │   └── document.py                 # Beanie: documents + GridFS metadata
│   ├── schemas/
│   │   ├── auth.py
│   │   ├── document.py
│   │   ├── analysis.py                 # AgentResult, ResearchStep Pydantic
│   │   ├── profile.py                  # StudentProfile, PublicProfile
│   │   └── discover.py                 # SearchQuery, SearchResult
│   ├── core/
│   │   ├── database.py                 # Motor + GridFS init
│   │   ├── firebase.py                 # Admin SDK + Firestore client + JWT verify
│   │   ├── config.py                   # Pydantic BaseSettings
│   │   └── langchain_setup.py          # LLM factory + LangSmith config
│   └── main.py
├── contracts/
│   ├── CONTRACT.md                     ← AUTO-UPDATE after every endpoint change
│   ├── resume-agent.md
│   ├── certificate-agent.md
│   └── github-agent.md
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
├── .env
├── .env.example
├── .gitignore
├── requirements.txt
└── render.yaml
```

---

## 🗄️ DATA STORAGE — STRICT SPLIT

### Firebase Firestore (ALL user data + results)
```
/users/{firebase_uid}
  email, role, display_name, created_at

/verifications/{verification_id}
  student_uid, overall_trust_score, verdict
  resume_score, cert_score, github_score
  cross_ref_flags[], created_at, expires_at

/ai_results/{result_id}
  student_uid, agent_type, trust_score, flags[], summary

/research_logs/{log_id}
  result_id, student_uid, agent_type, status, logs[]
  summary_stats: {total_steps, high_flags, sources_visited}

/profiles/{firebase_uid}
  is_public, skills[], domain, location
  verification_id (link to verifications doc)
  trust_score (denormalized for fast search)
  shortlisted_by[] (recruiter UIDs)

/shortlists/{recruiter_uid}
  student_uids[], created_at
```

### MongoDB GridFS (FILES ONLY)
```
GridFS buckets:
  resumes/     → resume PDF bytes
  certificates/ → certificate image/PDF bytes

documents collection:
  firebase_uid, type, gridfs_id, filename
  mime_type, hash_sha256, size_bytes
  status: pending|analyzing|done|failed
  uploaded_at
```

---

## 🤖 LANGGRAPH AGENT ARCHITECTURE

### Shared State
```python
from typing import TypedDict, Optional, Annotated
import operator

class VerificationState(TypedDict):
    # Inputs
    student_uid: str
    resume_doc_id: str
    cert_doc_ids: list[str]
    github_url: str

    # Agent outputs
    resume_result: Optional[dict]
    cert_result: Optional[dict]
    github_result: Optional[dict]
    cross_ref_findings: Optional[list[dict]]

    # Accumulated across agents (append-only)
    research_logs: Annotated[list[dict], operator.add]
    flags: Annotated[list[dict], operator.add]
    completed_agents: Annotated[list[str], operator.add]

    # Final
    overall_trust_score: Optional[float]
    verdict: Optional[str]
```

### Graph Structure
```
START → supervisor → [resume_node, cert_node, github_node] (parallel)
     → cross_reference → final_decision → END
```

### Trust Score Formula (NEVER CHANGE)
```
trust_score = resume×0.40 + cert×0.35 + github×0.25
```

### Streaming Pattern (astream_events v3)
```python
async for event in agent.astream_events(input, version="v3"):
    if event["event"] == "on_chat_model_stream":
        yield {"type": "thinking_token", "content": chunk}
    elif event["event"] == "on_tool_start":
        yield {"type": "research_step_start", "data": {...}}
    elif event["event"] == "on_tool_end":
        yield {"type": "research_step_complete", "data": {...}}
    elif event["event"] == "on_chain_end":
        yield {"type": "analysis_complete", "data": {...}}
```

---

## 🔐 AUTH PATTERN — USE EXACTLY THIS

```python
# app/core/firebase.py
from firebase_admin import auth
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

bearer = HTTPBearer()

async def verify_firebase_token(
    creds: HTTPAuthorizationCredentials = Depends(bearer)
) -> dict:
    try:
        return auth.verify_id_token(creds.credentials)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

async def require_student(user: dict = Depends(verify_firebase_token)) -> dict:
    if user.get("role") != "student":
        raise HTTPException(status_code=403, detail="Students only")
    return user

async def require_recruiter(user: dict = Depends(verify_firebase_token)) -> dict:
    if user.get("role") != "recruiter":
        raise HTTPException(status_code=403, detail="Recruiters only")
    return user
```

---

## 📋 CODING RULES

1. Read `contracts/CONTRACT.md` before writing any endpoint
2. Update `contracts/CONTRACT.md` after any change
3. Update `## 📌 PROJECT STATUS` after completing any task
4. All `async def` with `await` everywhere
5. All LLM calls via `langchain-google-genai`
6. All agents MUST produce `research_steps[]`
7. Streaming via `astream_events(version="v3")`
8. Structured output via `with_structured_output(schema, method="json_schema")`
9. Always try/except Gemini + GitHub calls
10. Agents always parallel via LangGraph parallel branches
11. Never `requests` — always `httpx`
12. Never commit `.env`

---

## 🔐 ENVIRONMENT VARIABLES

```bash
# MongoDB (files only)
MONGODB_URI=mongodb+srv://...
MONGODB_DB_NAME=verifai

# Firebase (auth + all data)
FIREBASE_PROJECT_ID=your-project-id
FIREBASE_CREDENTIALS_JSON={"type":"service_account",...}

# Google AI
GEMINI_API_KEY=from-aistudio.google.com
GOOGLE_API_KEY=same-as-above

# LangSmith tracing
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=from-smith.langchain.com
LANGCHAIN_PROJECT=verif-ai-hackathon

# GitHub OSINT
GITHUB_TOKEN=your-github-pat

# Web Search (agent tool)
BRAVE_API_KEY=from-brave.com/search/api

# App
ALLOWED_ORIGINS=http://localhost:3000,https://verif-ai-frontend.vercel.app
PORT=8000
ENVIRONMENT=development
```

---

## ⚡ MCP TOOLS — USE PROACTIVELY

| Command | When to use |
|---------|------------|
| `@mongodb` | Seed test data, query collections, verify schemas |
| `@github` | Push code, create PRs |
| `@render` | Deploy after features complete |
| `@git` | Commit after every feature |

Auto-behavior: finish feature → `@git commit -m "feat: X" && git push`

---

## 📡 API RESPONSE FORMAT

```json
{"success": true, "data": {...}, "message": "Done"}
{"success": false, "error": "Short title", "detail": "Full description"}
```

---

## 🚀 RENDER DEPLOYMENT CONFIG

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

## 🚫 NEVER DO THESE

- Never touch `verif-ai-frontend` repo
- Never skip `research_logs` save step
- Never run agents sequentially (always LangGraph parallel)
- Never use `requests` (use `httpx`)
- Never expose raw Gemini response to frontend
- Never use synchronous Motor calls
- Never hardcode API keys
- Never commit `.env`

---

## 📌 PROJECT STATUS — AUTO-UPDATE THIS

### Phase 0: Foundation
- [ ] requirements.txt
- [ ] .env + .env.example + .gitignore
- [ ] core/config.py
- [ ] core/database.py (Motor + GridFS)
- [ ] core/firebase.py (Admin SDK + Firestore + JWT deps)
- [ ] core/langchain_setup.py
- [ ] main.py (lifespan + CORS + routers)

### Phase 1: Auth + User Sync
- [ ] models/user.py
- [ ] schemas/auth.py
- [ ] api/v1/auth.py (sync, me, role check)

### Phase 2: File Upload
- [ ] models/document.py
- [ ] schemas/document.py
- [ ] api/v1/documents.py (GridFS upload)

### Phase 3: LangGraph Agents
- [ ] services/graph/state.py
- [ ] services/tools/pdf_tools.py
- [ ] services/tools/image_tools.py (ELA mandatory)
- [ ] services/tools/github_tools.py
- [ ] services/tools/stylometry_tools.py
- [ ] services/graph/supervisor.py
- [ ] services/graph/resume_node.py
- [ ] services/graph/certificate_node.py
- [ ] services/graph/github_node.py
- [ ] services/graph/cross_reference.py
- [ ] services/graph/final_decision.py
- [ ] services/graph/graph_builder.py
- [ ] services/streaming.py
- [ ] services/trust_score.py
- [ ] api/v1/analysis.py (trigger + WebSocket)

### Phase 4: Results + Discovery
- [ ] schemas/profile.py + schemas/discover.py
- [ ] services/discovery_service.py
- [ ] api/v1/profile.py (publish/unpublish)
- [ ] api/v1/discover.py (browse + search)
- [ ] api/v1/verification.py (get result + shortlist)

### Phase 5: Testing + Deploy
- [ ] tests/conftest.py (fixtures + mocks)
- [ ] tests/test_auth.py
- [ ] tests/test_documents.py
- [ ] tests/test_resume_node.py
- [ ] tests/test_certificate_node.py
- [ ] tests/test_github_node.py
- [ ] tests/test_graph.py (full pipeline)
- [ ] tests/test_cross_reference.py
- [ ] tests/test_discover.py
- [ ] Seed 5 test profiles via @mongodb
- [ ] render.yaml + @render deploy

**contracts/CONTRACT.md last updated:** _not yet_

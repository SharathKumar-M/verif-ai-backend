# VERIF-AI Backend — OpenCode Agent Rules
> **File location:** `verif-ai-backend/AGENTS.md` (root, committed to git)
> OpenCode reads this on every session. Run `/init` if context is lost.

---

## 🔴 AUTO-UPDATE AFTER EVERY TASK

1. Mark `[x]` in STATUS TRACKER below
2. Update `contracts/CONTRACT.md` with new/changed endpoint
3. `@git commit -m "feat: [name]" && git push`

---

## PROJECT IN ONE SENTENCE

Three LangGraph agents (Resume + Certificate + GitHub) analyze student credentials in parallel, share findings via StateGraph, cross-reference results, then produce a Trust Score that recruiters use to discover and shortlist candidates.

**Your repo:** `verif-ai-backend` (backend only).
**Brother's repo:** `verif-ai-frontend` — NEVER TOUCH.
**contracts/CONTRACT.md** — single source of truth for all API endpoints. Update it after every change.

---

## REPO LAYOUT (Where files live)

```
verif-ai-backend/
├── GEMINI.md          ← committed (Gemini CLI context)
├── AGENTS.md          ← committed (this file, OpenCode context)
├── opencode.json      ← committed (OpenCode config)
├── contracts/         ← committed (brother reads this via git clone)
│   ├── CONTRACT.md    ← auto-updated by agent
│   ├── resume-agent.md
│   ├── certificate-agent.md
│   └── github-agent.md
├── app/ ...
├── tests/ ...
├── bruno-collection/  ← committed (API test collections)
├── scripts/seed_fake_data.py
├── .env               ← NEVER committed
└── .env.example       ← committed (empty values)
```

---

## TECH STACK

```
FastAPI + Python 3.11+ (always async def)
LangGraph (StateGraph) → multi-agent orchestration
LangChain → tools, prompts, structured output
langchain-google-genai → Gemini 2.5 Flash (text) + Pro (vision)
langchain-mcp-adapters → MCP tools inside Python agents
langsmith → trace every agent step

Firebase Auth → all authentication
Firebase Firestore → all structured data (users, results, profiles)
MongoDB GridFS → binary files ONLY (resumes, certificates)
Motor + Beanie → async MongoDB driver

pdfplumber + pypdf → PDF text + metadata
pytesseract + Pillow → OCR + ELA image forensics
PyGithub + radon → GitHub OSINT + code complexity
httpx → HTTP client (NEVER requests)
```

---

## LANGGRAPH CORE PATTERNS

### Shared State
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
    flags: Annotated[list[dict], operator.add]
    completed_agents: Annotated[list[str], operator.add]
    overall_trust_score: Optional[float]
    verdict: Optional[str]
```

### LLM Setup
```python
from langchain_google_genai import ChatGoogleGenerativeAI

flash = ChatGoogleGenerativeAI(model="gemini-2.5-pro",
    google_api_key=os.getenv("GEMINI_API_KEY"), temperature=0.1, streaming=True)
vision = ChatGoogleGenerativeAI(model="gemini-2.5-pro",
    google_api_key=os.getenv("GEMINI_API_KEY"), temperature=0.1, streaming=True)

# ALWAYS use structured output
result = await flash.with_structured_output(
    MySchema.model_json_schema(), method="json_schema").ainvoke(prompt)
```

### Streaming
```python
async for event in agent.astream_events(input, version="v3"):
    if event["event"] == "on_chat_model_stream":
        yield {"type": "thinking_token", "content": event["data"]["chunk"].content}
    elif event["event"] == "on_tool_start":
        yield {"type": "research_step_start", "data": build_step(event)}
    elif event["event"] == "on_tool_end":
        yield {"type": "research_step_complete", "data": update_step(event)}
```

---

## THREE AGENTS

| Agent | Model | Key Tools | Output Fields |
|-------|-------|-----------|---------------|
| Resume | Gemini Flash | pdf_tools, stylometry, web_search | ai_text_prob, skill_inflation, timeline_score, overall_resume_trust |
| Certificate | Gemini Vision Pro | ocr, ELA, pdf_metadata, web_search | forgery_prob, issuer_verified, tampering_score, overall_cert_trust |
| GitHub | Gemini Flash (Deep) | github_profile, repos, commits, web_search | originality, skill_match, commit_auth, overall_github_trust |

All agents write `research_steps[]` to state. NEVER skip this.

### Cross-Reference (runs after all 3)
Pure logic node — no LLM needed:
- Resume skills vs GitHub languages → flag mismatches
- Resume start dates vs GitHub first commits → flag timeline mismatches
- Certificate courses vs GitHub project evidence → flag missing proof

### Trust Score (NEVER change)
```
trust_score = resume×0.40 + cert×0.35 + github×0.25
AUTHENTIC ≥80 | FLAGGED 60-79 | SUSPICIOUS 35-59 | FAKE <35
```

---

## DISCOVERY SYSTEM

```python
# Recruiter searches Firestore profiles collection
db.collection("profiles")
  .where("is_public", "==", True)
  .where("trust_score", ">=", min_trust)  # if min_trust provided
  .where("domain", "==", domain)          # if domain provided
  .order_by("trust_score", descending)
  .limit(20)
```

Student publishes → `is_public=True` → appears in recruiter search.

---

## RESEARCH LOG SCHEMA (save to Firestore /research_logs/)

```json
{
  "logs": [{
    "step": 1,
    "agent": "resume_agent",
    "thought": "Checking if company existed...",
    "action": "web_search",
    "query": "TechCorp Bangalore founded year",
    "sources": ["https://linkedin.com/company/techcorp"],
    "finding": "Founded 2019, claim of 2017 impossible",
    "impact": "HIGH_FLAG",
    "flag_generated": {"type": "timeline_impossibility", "severity": "high"},
    "cross_agent_reference": null,
    "timestamp": "ISO8601",
    "duration_ms": 1240
  }]
}
```

---

## CODING STANDARDS

1. All `async def` + `await` on all I/O
2. All LLM via `langchain-google-genai`
3. Structured output: `with_structured_output(schema, method="json_schema")`
4. Streaming: `astream_events(version="v3")`
5. Never skip `research_steps[]`
6. Never use `requests`
7. Always try/except external calls with fallback (neutral score 50 on failure)
8. Update `contracts/CONTRACT.md` after every endpoint change
9. Save all research logs to Firestore `/research_logs/`
10. Complete files only — no partial snippets

---

## MODEL SELECTION (OpenCode)

| Task | Model |
|------|-------|
| Complex agent logic, debugging | `deepseek-r1:14b` |
| Writing LangChain/LangGraph code | `deepseek-coder-v2:16b` |
| Fast code, MongoDB queries | `qwen2.5-coder:14b` |
| Long reviews | `minimax-text-01` |

---

## MCP TOOLS

```
@mongodb   → seed data, query, verify schemas
@github    → push, branch, PR
@render    → deploy
@git       → commit after every feature
```

---

## STATUS TRACKER — MARK [x] AFTER EACH

**Phase 0:** [ ] requirements.txt | [ ] .env.example + .gitignore | [ ] core/config.py | [ ] core/database.py | [ ] core/firebase.py | [ ] core/langchain_setup.py | [ ] main.py | [ ] contracts/CONTRACT.md (shell)

**Phase 1:** [ ] models/user.py | [ ] schemas/auth.py | [ ] api/v1/auth.py | [ ] Bruno auth tests

**Phase 2:** [ ] models/document.py | [ ] schemas/document.py | [ ] api/v1/documents.py | [ ] Bruno upload tests

**Phase 3:** [ ] services/graph/state.py | [ ] services/tools/* (all 4) | [ ] services/graph/supervisor.py | [ ] services/graph/resume_node.py | [ ] services/graph/certificate_node.py | [ ] services/graph/github_node.py | [ ] services/graph/cross_reference.py | [ ] services/graph/final_decision.py | [ ] services/graph/graph_builder.py | [ ] services/streaming.py | [ ] services/trust_score.py | [ ] api/v1/analysis.py | [ ] Bruno analysis tests

**Phase 4:** [ ] services/discovery_service.py | [ ] schemas/profile.py + discover.py | [ ] api/v1/profile.py | [ ] api/v1/discover.py | [ ] api/v1/verification.py | [ ] Bruno discover tests

**Phase 5:** [ ] scripts/seed_fake_data.py | [ ] tests/* (all) | [ ] render.yaml + deployed | [ ] README.md

**CONTRACT.md last updated:** _not yet_

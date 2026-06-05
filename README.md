# VERIF-AI Backend
> AI-powered academic credential verification using LangGraph + Google Gemini

[![Backend](https://img.shields.io/badge/Backend-FastAPI-green)](https://fastapi.tiangolo.com)
[![AI](https://img.shields.io/badge/AI-LangGraph%20%2B%20Gemini-blue)](https://langchain-ai.github.io/langgraph/)
[![Database](https://img.shields.io/badge/Data-Firebase%20%2B%20MongoDB-orange)](https://firebase.google.com)
[![Deploy](https://img.shields.io/badge/Deploy-Render-purple)](https://render.com)

---

## What This Does

Three LangGraph AI agents verify student credentials in parallel:
- **Resume Agent** — detects AI-generated writing, skill inflation, timeline fraud
- **Certificate Agent** — detects forgery using ELA image forensics + Gemini Vision
- **GitHub Agent** — OSINT analysis of commit patterns, code originality, skill evidence

Agents share state and cross-reference each other's findings. Recruiters see a Trust Score (0-100) with full live AI reasoning trail.

---

## Quick Start

```bash
git clone https://github.com/tejasM17/verif-ai-backend
cd verif-ai-backend
pip install -r requirements.txt
cp .env.example .env   # fill in your keys
uvicorn app.main:app --reload --port 8000
# Visit http://localhost:8000/docs
```

---

## Environment Variables (`.env`)

```
MONGODB_URI=mongodb+srv://...
MONGODB_DB_NAME=verifai
FIREBASE_PROJECT_ID=...
FIREBASE_CREDENTIALS_JSON={"type":"service_account",...}
GEMINI_API_KEY=...
GOOGLE_API_KEY=...
LANGCHAIN_API_KEY=...
LANGCHAIN_TRACING_V2=true
LANGCHAIN_PROJECT=verif-ai-hackathon
GITHUB_TOKEN=...
BRAVE_API_KEY=...
ALLOWED_ORIGINS=http://localhost:3000
PORT=8000
ENVIRONMENT=development
```

---

## Seed Test Data

```bash
python scripts/seed_fake_data.py
```
Creates 5 student accounts (trust scores 18-88) + 2 recruiter accounts.
See TESTING_GUIDE.md for credentials.

---

## Run Tests

```bash
pytest tests/ -v
```

---

## API Documentation

Interactive docs: `http://localhost:8000/docs`
Full contract: `contracts/CONTRACT.md`

---

## Related Files

| File | Purpose |
|------|---------|
| `GEMINI.md` | Gemini CLI agent context |
| `AGENTS.md` | OpenCode agent context |
| `TESTING_GUIDE.md` | Bruno + pytest testing guide |
| `contracts/CONTRACT.md` | API endpoint specification |

---

## Frontend Repo
[github.com/SharathKumar-M/verif-ai-frontend](https://github.com/SharathKumar-M/verif-ai-frontend)

---

*Auto-updated by AI agents as the project grows.*

"""
MediQuery AI — Natural Language Clinical Data Query API
========================================================
A REST API that accepts plain-English questions about patient data,
converts them to parameterized SQL using a pluggable NLP layer,
executes the query, and returns structured JSON.

Architecture:
    Client → POST /query → NLP Parser → SQL Generator → SQLite → JSON Response

Why this design:
    - NLP layer is a swappable interface: swap rule-based parser for any
      LLM backend (OpenAI, IBM watsonx) without changing the API contract.
    - Parameterized queries prevent SQL injection.
    - SQLite for portability; swap DATABASE_URL for PostgreSQL/MySQL in prod.

Run locally:
    pip install -r requirements.txt
    uvicorn app.main:app --reload

Docker:
    docker build -t mediquery-ai .
    docker run -p 8000:8000 mediquery-ai
"""

from fastapi import FastAPI
from app.database import init_db
from app.routers import query, patients

# ── App initialization ────────────────────────────────────────────────────────

app = FastAPI(
    title="MediQuery AI",
    description="Natural language interface for structured clinical data queries.",
    version="1.0.0",
)

# Seed the database on startup
@app.on_event("startup")
def startup():
    init_db()

# ── Routers ───────────────────────────────────────────────────────────────────

app.include_router(query.router,    prefix="/query",    tags=["NL Query"])
app.include_router(patients.router, prefix="/patients", tags=["Patients"])


@app.get("/")
def root():
    """Health check + usage hint."""
    return {
        "service": "MediQuery AI",
        "status":  "running",
        "usage":   "POST /query with JSON body: {\"question\": \"How many patients are admitted?\"}",
    }

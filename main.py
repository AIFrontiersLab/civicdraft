"""CivicDraft: Draft compliant government content with verifiable sources."""
import os
import sqlite3
import hashlib
from typing import List, Optional, Dict
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="CivicDraft MVP")
DB_PATH = os.getenv("CIVIC_DRAFT_DB", "civic_draft.db")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    return conn

def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS drafts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            topic TEXT NOT NULL,
            source_text TEXT,
            draft_content TEXT,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

class DraftRequest(BaseModel):
    topic: str
    source_text: str

class DraftResponse(BaseModel):
    id: int
    topic: str
    draft_content: str
    status: str

class AuditLog(BaseModel):
    draft_id: int
    action: str
    notes: str

# Simulated Local LLM Logic
def generate_draft(topic: str, source: str) -> str:
    return f"[DRAFT] Regarding {topic}: Based on source '{source[:20]}...', the proposed update is to clarify regulations."

# Simulated Vector Retrieval
def retrieve_sources(topic: str) -> str:
    return f"Official Record: {topic} - Updated 2023."

@app.on_event("startup")
def startup():
    init_db()

@app.post("/drafts", response_model=DraftResponse)
def create_draft(req: DraftRequest):
    source = retrieve_sources(req.topic)
    draft_content = generate_draft(req.topic, source)
    conn = get_db()
    cursor = conn.execute(
        "INSERT INTO drafts (topic, source_text, draft_content) VALUES (?, ?, ?)",
        (req.topic, req.source_text, draft_content)
    )
    draft_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return DraftResponse(id=draft_id, topic=req.topic, draft_content=draft_content, status="pending")

@app.get("/drafts")
def list_drafts():
    conn = get_db()
    rows = conn.execute("SELECT id, topic, draft_content, status FROM drafts").fetchall()
    conn.close()
    return [{"id": r[0], "topic": r[1], "content": r[2], "status": r[3]} for r in rows]

@app.post("/drafts/{draft_id}/approve")
def approve_draft(draft_id: int):
    conn = get_db()
    conn.execute("UPDATE drafts SET status = 'approved' WHERE id = ?", (draft_id,))
    if conn.execute("SELECT 1 FROM drafts WHERE id = ?", (draft_id,)).fetchone() is None:
        conn.close()
        raise HTTPException(status_code=404, detail="Draft not found")
    conn.commit()
    conn.close()
    return {"status": "approved", "draft_id": draft_id}

def demo():
    """Run a quick demo of the core capability."""
    print("Starting CivicDraft Demo...")
    init_db()
    req = DraftRequest(topic="Zoning Law 404", source_text="City Code 2022")
    resp = create_draft(req)
    print(f"Created Draft: {resp.id}, Status: {resp.status}")
    print(f"Content: {resp.draft_content}")
    approve = approve_draft(resp.id)
    print(f"Approved: {approve}")
    drafts = list_drafts()
    print(f"All Drafts: {drafts}")
    # Cleanup
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    print("Demo complete.")

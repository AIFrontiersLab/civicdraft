"""Tests for CivicDraft MVP."""
import os
import pytest
from fastapi.testclient import TestClient
from main import app, init_db, create_draft, approve_draft, list_drafts, DraftRequest

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_db():
    """Initialize DB before each test."""
    os.environ["CIVIC_DRAFT_DB"] = "test_civic.db"
    init_db()
    yield
    if os.path.exists("test_civic.db"):
        os.remove("test_civic.db")

def test_startup():
    """Test that the app starts and DB is initialized."""
    response = client.get("/drafts")
    assert response.status_code == 200
    assert response.json() == []

def test_create_draft_happy_path():
    """Test creating a draft with valid data."""
    payload = {"topic": "Traffic Signal Update", "source_text": "City Manual v2"}
    response = client.post("/drafts", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "pending"
    assert data["topic"] == "Traffic Signal Update"
    assert "[DRAFT]" in data["draft_content"]

def test_create_draft_missing_fields():
    """Test creating a draft with missing fields."""
    payload = {"topic": "Traffic Signal Update"} # Missing source_text
    response = client.post("/drafts", json=payload)
    assert response.status_code == 422

def test_approve_draft():
    """Test approving a draft."""
    payload = {"topic": "Park Hours", "source_text": "City Code"}
    create_resp = client.post("/drafts", json=payload)
    draft_id = create_resp.json()["id"]
    
    approve_resp = client.post(f"/drafts/{draft_id}/approve")
    assert approve_resp.status_code == 200
    assert approve_resp.json()["status"] == "approved"
    
    # Verify status in list
    list_resp = client.get("/drafts")
    draft = next(d for d in list_resp.json() if d["id"] == draft_id)
    assert draft["status"] == "approved"

def test_approve_nonexistent_draft():
    """Test approving a draft that does not exist."""
    response = client.post("/drafts/99999/approve")
    assert response.status_code == 404

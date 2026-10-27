"""
Unit and integration tests for the AI QA Engineer API.
"""

import pytest
from fastapi.testclient import TestClient
from backend.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_health_check(client):
    """Test health endpoint returns 200 and version information."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data
    assert "demo_mode" in data


def test_demo_endpoint(client):
    """Test demo info endpoint returns existing files."""
    response = client.get("/api/demo")
    assert response.status_code == 200
    data = response.json()
    assert "demo_project_path" in data
    assert len(data.get("files", [])) > 0


def test_analyze_demo_project(client):
    """Test starting an analysis on the built-in demo project."""
    payload = {"project_path": "demo"}
    response = client.post("/api/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "job_id" in data
    assert data["status"] == "started"


def test_status_endpoint(client):
    """Test status polling endpoint."""
    # First start analysis
    start_res = client.post("/api/analyze", json={"project_path": "demo"})
    job_id = start_res.json()["job_id"]

    # Poll status
    status_res = client.get(f"/api/status/{job_id}")
    assert status_res.status_code == 200
    status_data = status_res.json()
    assert status_data["job_id"] == job_id
    assert "workflow_status" in status_data

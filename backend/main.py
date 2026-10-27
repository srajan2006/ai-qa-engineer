"""
FastAPI Backend — Main Entry Point for the AI QA Engineer Platform.

Endpoints:
    GET  /                        → Serve the frontend dashboard
    GET  /health                  → Health check
    POST /api/analyze             → Start analysis of a project path
    POST /api/upload              → Upload a zip project
    GET  /api/status/{job_id}     → Get job status and workflow progress
    GET  /api/report/{job_id}     → Get full analysis report
    POST /api/approve/{job_id}    → Human approval of report
    GET  /api/results/{job_id}    → Alias for report
    GET  /api/demo                → Get demo project path
"""

import asyncio
import io
import os
import shutil
import sys
import tempfile
import uuid
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

# Ensure project root is in sys.path
BASE_DIR_BOOTSTRAP = Path(__file__).resolve().parent.parent
if str(BASE_DIR_BOOTSTRAP) not in sys.path:
    sys.path.insert(0, str(BASE_DIR_BOOTSTRAP))

import uvicorn
from fastapi import BackgroundTasks, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from loguru import logger
from pydantic import BaseModel

from backend.config import (
    APP_TITLE,
    APP_VERSION,
    BASE_DIR,
    DEBUG,
    DEMO_MODE,
    DEMO_PROJECT_DIR,
    HOST,
    PORT,
)
from backend.graphs.qa_graph import get_qa_graph
from backend.models.state import QAState, create_initial_state

# ──────────────────────────────────────────────────────────────────────────────
# App Setup
# ──────────────────────────────────────────────────────────────────────────────

app = FastAPI(
    title=APP_TITLE,
    version=APP_VERSION,
    description="Multi-Agent AI-Powered Software Quality & Testing Platform",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve frontend static files
FRONTEND_DIR = BASE_DIR / "frontend"
if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")

# In-memory job store (sufficient for MVP demo)
jobs: dict[str, dict[str, Any]] = {}

# ──────────────────────────────────────────────────────────────────────────────
# Pydantic Models
# ──────────────────────────────────────────────────────────────────────────────


class AnalyzeRequest(BaseModel):
    project_path: str
    job_id: Optional[str] = None


class ApprovalRequest(BaseModel):
    decision: str  # "approved" | "rejected"
    notes: Optional[str] = ""


class JobStatus(BaseModel):
    job_id: str
    status: str  # "pending" | "running" | "completed" | "failed"
    current_agent: str
    workflow_status: dict[str, str]
    progress: int  # 0-100
    started_at: str
    completed_at: Optional[str]
    demo_mode: bool
    errors: list[str]


# ──────────────────────────────────────────────────────────────────────────────
# Routes
# ──────────────────────────────────────────────────────────────────────────────


@app.get("/", response_class=HTMLResponse)
async def serve_dashboard():
    """Serve the main dashboard HTML."""
    index_file = FRONTEND_DIR / "index.html"
    if index_file.exists():
        return HTMLResponse(content=index_file.read_text(encoding="utf-8"))
    return HTMLResponse("<h1>AI QA Engineer</h1><p>Frontend not found. Run from project root.</p>")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "ok",
        "version": APP_VERSION,
        "demo_mode": DEMO_MODE,
        "timestamp": datetime.now().isoformat(),
    }


@app.get("/api/demo")
async def get_demo_info():
    """Return information about the built-in demo project."""
    demo_files = list(DEMO_PROJECT_DIR.glob("*.py")) if DEMO_PROJECT_DIR.exists() else []
    return {
        "demo_project_path": str(DEMO_PROJECT_DIR),
        "exists": DEMO_PROJECT_DIR.exists(),
        "files": sorted([f.name for f in demo_files if not f.name.startswith("test_ai_generated")]),
        "demo_mode": DEMO_MODE,
    }


@app.get("/api/file")
async def get_file_content(filename: str):
    """Retrieve content of a demo or project file."""
    # Sanitize filename
    safe_name = Path(filename).name
    file_path = DEMO_PROJECT_DIR / safe_name
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail=f"File {safe_name} not found.")
    return {
        "filename": safe_name,
        "content": file_path.read_text(encoding="utf-8", errors="ignore"),
        "lines": len(file_path.read_text(encoding="utf-8", errors="ignore").splitlines()),
    }


@app.post("/api/analyze")
async def start_analysis(
    request: AnalyzeRequest,
    background_tasks: BackgroundTasks,
):
    """
    Start an AI QA analysis on a project directory.
    Returns a job_id that can be used to poll for status.
    """
    job_id = request.job_id or str(uuid.uuid4())[:8]

    # Resolve project path
    project_path = request.project_path
    if project_path == "demo" or project_path == "__demo__":
        project_path = str(DEMO_PROJECT_DIR)

    path = Path(project_path)
    if not path.exists():
        raise HTTPException(status_code=400, detail=f"Project path not found: {project_path}")
    if not path.is_dir():
        raise HTTPException(status_code=400, detail="Project path must be a directory.")

    # Initialize job
    jobs[job_id] = {
        "job_id": job_id,
        "status": "pending",
        "current_agent": "",
        "workflow_status": {
            "code_loader": "pending",
            "code_analyzer": "pending",
            "security_agent": "pending",
            "test_generator": "pending",
            "test_runner": "pending",
            "coverage_agent": "pending",
            "bug_analysis": "pending",
            "root_cause": "pending",
            "qa_report": "pending",
        },
        "progress": 0,
        "started_at": datetime.now().isoformat(),
        "completed_at": None,
        "demo_mode": DEMO_MODE,
        "errors": [],
        "report": None,
        "project_path": str(path),
    }

    background_tasks.add_task(_run_analysis, job_id, str(path))

    return {
        "job_id": job_id,
        "status": "started",
        "message": f"Analysis started for: {path.name}",
        "demo_mode": DEMO_MODE,
    }


@app.post("/api/upload")
async def upload_project(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
):
    """
    Accept a ZIP file containing a Python project.
    Extracts it to a temp directory and starts analysis.
    """
    if not file.filename or not file.filename.endswith(".zip"):
        raise HTTPException(status_code=400, detail="Please upload a .zip file.")

    job_id = str(uuid.uuid4())[:8]

    try:
        # Read and extract zip
        contents = await file.read()
        tmp_dir = tempfile.mkdtemp(prefix=f"qa_upload_{job_id}_")

        with zipfile.ZipFile(io.BytesIO(contents)) as zf:
            zf.extractall(tmp_dir)

        # Find the actual Python project root (handle nested directories)
        project_path = _find_project_root(Path(tmp_dir))

    except zipfile.BadZipFile:
        raise HTTPException(status_code=400, detail="Invalid ZIP file.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

    # Initialize job
    jobs[job_id] = {
        "job_id": job_id,
        "status": "pending",
        "current_agent": "",
        "workflow_status": {k: "pending" for k in [
            "code_loader", "code_analyzer", "security_agent",
            "test_generator", "test_runner", "coverage_agent",
            "bug_analysis", "root_cause", "qa_report",
        ]},
        "progress": 0,
        "started_at": datetime.now().isoformat(),
        "completed_at": None,
        "demo_mode": DEMO_MODE,
        "errors": [],
        "report": None,
        "project_path": str(project_path),
        "_tmp_dir": tmp_dir,
    }

    background_tasks.add_task(_run_analysis, job_id, str(project_path))

    return {
        "job_id": job_id,
        "status": "started",
        "message": f"Upload received. Analyzing: {file.filename}",
        "demo_mode": DEMO_MODE,
    }


@app.get("/api/status/{job_id}")
async def get_status(job_id: str):
    """Get the current status and workflow progress of a job."""
    job = jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")

    # Calculate progress
    ws = job.get("workflow_status", {})
    total = len(ws)
    completed = sum(1 for v in ws.values() if v == "completed")
    progress = int(completed / total * 100) if total > 0 else 0

    return {
        "job_id": job_id,
        "status": job.get("status", "unknown"),
        "current_agent": job.get("current_agent", ""),
        "workflow_status": ws,
        "progress": progress,
        "started_at": job.get("started_at", ""),
        "completed_at": job.get("completed_at"),
        "demo_mode": job.get("demo_mode", DEMO_MODE),
        "errors": job.get("errors", []),
    }


@app.get("/api/report/{job_id}")
async def get_report(job_id: str):
    """Get the full QA analysis report for a completed job."""
    job = jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")
    if job.get("status") not in ("completed", "failed"):
        raise HTTPException(status_code=202, detail="Analysis still in progress.")

    report = job.get("report")
    if not report:
        raise HTTPException(status_code=404, detail="Report not yet generated.")

    return report


@app.get("/api/results/{job_id}")
async def get_results(job_id: str):
    """Alias for /api/report/{job_id}."""
    return await get_report(job_id)


@app.post("/api/approve/{job_id}")
async def approve_report(job_id: str, request: ApprovalRequest):
    """Human-in-the-loop: approve or reject the QA report."""
    job = jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")

    if request.decision not in ("approved", "rejected"):
        raise HTTPException(status_code=400, detail="Decision must be 'approved' or 'rejected'.")

    job["approval_status"] = request.decision
    job["approval_notes"] = request.notes or ""

    if job.get("report"):
        job["report"]["approval_status"] = request.decision
        job["report"]["approval_notes"] = request.notes

    logger.info(f"[Approval] Job {job_id} — {request.decision.upper()}: {request.notes}")

    return {
        "job_id": job_id,
        "approval_status": request.decision,
        "message": f"Report {request.decision} successfully.",
        "timestamp": datetime.now().isoformat(),
    }


@app.post("/api/run-tests")
async def run_tests_endpoint(request: AnalyzeRequest, background_tasks: BackgroundTasks):
    """Run only the test generation + execution pipeline on an already-analyzed project."""
    return await start_analysis(request, background_tasks)


# ──────────────────────────────────────────────────────────────────────────────
# Background Task
# ──────────────────────────────────────────────────────────────────────────────


async def _run_analysis(job_id: str, project_path: str):
    """Background task: run the full LangGraph QA pipeline with live streaming updates."""
    job = jobs[job_id]
    job["status"] = "running"

    try:
        # Create initial state
        initial_state = create_initial_state(project_path, job_id)

        # Get the compiled LangGraph
        qa_graph = get_qa_graph()

        # Run streaming in background executor
        def _execute_graph():
            final_st = initial_state
            for event in qa_graph.stream(initial_state):
                for node_name, node_output in event.items():
                    if node_name not in ("supervisor_start", "supervisor_end"):
                        job["workflow_status"][node_name] = "completed"
                        job["current_agent"] = node_name
                    # Save current cumulative state
                    if isinstance(node_output, dict):
                        final_st.update(node_output)
            return final_st

        loop = asyncio.get_event_loop()
        final_state: QAState = await loop.run_in_executor(None, _execute_graph)

        # Finalize job results
        job["workflow_status"] = final_state.get("workflow_status", {})
        job["current_agent"] = "completed"
        job["errors"] = final_state.get("errors", [])
        job["report"] = final_state.get("qa_report", {})
        job["status"] = "completed"
        job["completed_at"] = datetime.now().isoformat()

        logger.info(f"[Job {job_id}] Analysis completed successfully.")

    except Exception as e:
        logger.error(f"[Job {job_id}] Analysis failed: {e}")
        job["status"] = "failed"
        job["errors"] = job.get("errors", []) + [str(e)]
        job["completed_at"] = datetime.now().isoformat()
        job["current_agent"] = "failed"

    finally:
        # Clean up uploaded tmp directory if present
        tmp_dir = job.get("_tmp_dir")
        if tmp_dir and Path(tmp_dir).exists():
            try:
                shutil.rmtree(tmp_dir, ignore_errors=True)
            except Exception:
                pass


def _find_project_root(base: Path) -> Path:
    """Find the actual Python project directory inside an extracted zip."""
    # Check if base has Python files directly
    py_files = list(base.glob("*.py"))
    if py_files:
        return base

    # Check one level deep (common for zipped projects)
    for subdir in base.iterdir():
        if subdir.is_dir():
            if list(subdir.glob("*.py")):
                return subdir

    return base


# ──────────────────────────────────────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    logger.info(f"Starting {APP_TITLE} v{APP_VERSION}")
    logger.info(f"Demo mode: {DEMO_MODE}")
    logger.info(f"Frontend: {FRONTEND_DIR}")
    uvicorn.run(
        "backend.main:app",
        host=HOST,
        port=PORT,
        reload=DEBUG,
        log_level="info",
    )

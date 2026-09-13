"""
CAREERX – FastAPI Application
Exposes all agent capabilities as REST API endpoints.
Serves the frontend static files from /static.
"""
from __future__ import annotations

import logging
import sys
import os

# Ensure project root is on the path so relative imports work
sys.path.insert(0, os.path.dirname(__file__))

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from config import settings
from agents.models import StudentProfile, ProgressUpdate, CareerXReport
from agents.orchestrator import orchestrator

# ── Logging ────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=getattr(logging, settings.log_level, logging.INFO),
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("careerx.api")

# ── App ────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="CAREERX – Agentic AI Career & Skill Gap Navigator",
    description=(
        "Multi-agent system that analyses student profiles, identifies skill gaps, "
        "and generates personalised career roadmaps using IBM Granite and RAG."
    ),
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory session store (use Redis/DB in production)
_session_store: dict[str, CareerXReport] = {}


# ── Health ─────────────────────────────────────────────────────────────────
@app.get("/api/health", tags=["System"])
def health_check():
    """Basic liveness probe."""
    return {
        "status": "ok",
        "model": settings.granite_llm_model,
        "watsonx_configured": bool(settings.watsonx_api_key and settings.watsonx_project_id),
        "disclaimer": settings.disclaimer_text,
    }


# ── Roles ──────────────────────────────────────────────────────────────────
@app.get("/api/roles", tags=["Knowledge Base"])
def list_roles():
    """Return all available career roles from the knowledge base."""
    try:
        from rag.knowledge_base import CareerKnowledgeBase
        kb = CareerKnowledgeBase(
            persist_dir=settings.chroma_persist_dir,
            kb_path=settings.kb_data_path,
        )
        kb.init()
        return {"roles": kb.list_roles()}
    except Exception as exc:
        logger.error("list_roles error: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/api/roles/{role_id}", tags=["Knowledge Base"])
def get_role(role_id: str):
    """Return full details for a specific career role."""
    try:
        from rag.knowledge_base import CareerKnowledgeBase
        kb = CareerKnowledgeBase(
            persist_dir=settings.chroma_persist_dir,
            kb_path=settings.kb_data_path,
        )
        kb.init()
        role = kb.get_role_by_id(role_id)
        if not role:
            raise HTTPException(status_code=404, detail=f"Role '{role_id}' not found.")
        return role
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("get_role error: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))


# ── Core Pipeline ──────────────────────────────────────────────────────────
@app.post("/api/analyze", response_model=CareerXReport, tags=["Core Pipeline"])
def analyze_profile(profile: StudentProfile):
    """
    **Main endpoint.** Accepts a student profile and runs the full multi-agent pipeline.

    Returns a CareerXReport containing:
    - Profile summary
    - Career match scores
    - Skill gap analysis
    - Personalized learning roadmap
    - Project recommendations
    - Certification recommendations
    - Career insights

    ⚠️ Career recommendations are AI-generated guidance only
    and do not guarantee employment outcomes.
    """
    try:
        report = orchestrator.run(profile)
        # Store in session for progress updates
        session_key = f"{profile.name}_{profile.target_career}".lower().replace(" ", "_")
        _session_store[session_key] = report
        logger.info("Analysis complete and stored with key '%s'", session_key)
        return report
    except Exception as exc:
        logger.exception("analyze_profile error")
        raise HTTPException(status_code=500, detail=str(exc))


# ── Progress Update ────────────────────────────────────────────────────────
class ProgressRequest(BaseModel):
    profile: StudentProfile
    progress: ProgressUpdate


@app.post("/api/progress", tags=["Progress Tracking"])
def update_progress(request: ProgressRequest):
    """
    Update the student's progress.
    Recalculates remaining gaps and updates the roadmap.
    Requires a previous /api/analyze call for the same profile.
    """
    try:
        session_key = (
            f"{request.profile.name}_{request.profile.target_career}"
            .lower()
            .replace(" ", "_")
        )
        existing = _session_store.get(session_key)
        if existing is None:
            # Run a fresh analysis if no session exists
            existing = orchestrator.run(request.profile)

        updated = orchestrator.update_progress(request.profile, existing, request.progress)
        _session_store[session_key] = updated
        return updated
    except Exception as exc:
        logger.exception("update_progress error")
        raise HTTPException(status_code=500, detail=str(exc))


# ── RAG Search ─────────────────────────────────────────────────────────────
class SearchRequest(BaseModel):
    query: str
    role_id: str | None = None
    top_k: int = 5


@app.post("/api/search", tags=["Knowledge Base"])
def semantic_search(request: SearchRequest):
    """Semantic search over the career knowledge base (RAG retrieval)."""
    try:
        from rag.knowledge_base import CareerKnowledgeBase
        kb = CareerKnowledgeBase(
            persist_dir=settings.chroma_persist_dir,
            kb_path=settings.kb_data_path,
        )
        kb.init()
        results = kb.retrieve(
            query=request.query,
            role_id=request.role_id,
            top_k=min(request.top_k, 10),
        )
        return {
            "query": request.query,
            "source": "CAREERX Knowledge Base (RAG)",
            "results": results,
        }
    except Exception as exc:
        logger.error("semantic_search error: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))


# ── Rebuild KB ─────────────────────────────────────────────────────────────
@app.post("/api/admin/rebuild-kb", tags=["Admin"])
def rebuild_knowledge_base():
    """Force rebuild of the vector store from knowledge_base.json."""
    try:
        from rag.knowledge_base import CareerKnowledgeBase
        kb = CareerKnowledgeBase(
            persist_dir=settings.chroma_persist_dir,
            kb_path=settings.kb_data_path,
        )
        kb.init()
        kb.rebuild()
        return {"status": "Knowledge base rebuilt successfully."}
    except Exception as exc:
        logger.error("rebuild_knowledge_base error: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))


# ── Frontend ───────────────────────────────────────────────────────────────
_static_dir = os.path.join(os.path.dirname(__file__), "frontend")
if os.path.isdir(_static_dir):
    app.mount("/static", StaticFiles(directory=_static_dir), name="static")

    @app.get("/", include_in_schema=False)
    def serve_frontend():
        return FileResponse(os.path.join(_static_dir, "index.html"))


# ── Entry Point ────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.app_debug,
        log_level=settings.log_level.lower(),
    )

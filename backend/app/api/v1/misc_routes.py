from fastapi import APIRouter, Request

from app.core.rate_limit import limiter
from app.schemas.analysis import RoadmapRequest
from app.services import analysis_service, resume_service, roadmap_service, session_service

router = APIRouter(tags=["roadmap-history-dashboard"])


@router.post("/roadmap")
@limiter.limit("10/hour")
async def create_roadmap(request: Request, body: RoadmapRequest):
    session_service.ensure_session(body.session_id)
    resume_json = resume_service.get_resume_json(body.resume_id)
    result = roadmap_service.generate_roadmap(
        session_id=body.session_id,
        resume_id=body.resume_id,
        resume=resume_json,
        current_role=body.current_role,
        target_role=body.target_role,
    )
    return result


@router.get("/history")
async def history(session_id: str, limit: int = 20):
    return {"history": analysis_service.get_history(session_id, limit)}


@router.get("/dashboard")
async def dashboard(session_id: str):
    return analysis_service.get_dashboard_metrics(session_id)

from fastapi import APIRouter, Form, Request

from app.core.rate_limit import limiter
from app.services import jd_service, session_service

router = APIRouter(prefix="/jd", tags=["job-description"])


@router.post("/paste")
@limiter.limit("20/hour")
async def paste_jd(
    request: Request,
    session_id: str = Form(...),
    jd_text: str = Form(...),
):
    """Submit a job description as pasted text. Parsed and cached by content hash."""
    session_service.ensure_session(session_id)
    jd_id, jd_json = jd_service.ingest_jd_from_text(session_id, jd_text)
    return {"jd_id": jd_id, "jd": jd_json.model_dump()}

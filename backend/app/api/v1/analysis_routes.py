from fastapi import APIRouter, Request

from app.core.exceptions import ResourceNotFoundError
from app.core.rate_limit import limiter
from app.schemas.analysis import AnalyzeRequest
from app.services import analysis_service, jd_service, resume_service, session_service
from app.db.supabase_client import get_supabase

router = APIRouter(prefix="/analyze", tags=["analysis"])


@router.post("")
@limiter.limit("10/hour")
async def analyze(request: Request, body: AnalyzeRequest):
    """
    Core endpoint. Two modes, decided by whether jd_text is provided:
      - Evaluation Mode: resume only → general resume quality analysis
      - Matching Mode: resume + JD → job-fit analysis with gap detection

    Accepts either an existing resume_id (from a prior /resume/upload or
    /resume/paste call) OR raw resume_text directly, to support a single-
    shot "paste resume, paste JD, click analyze" flow without a separate
    upload round-trip.
    """
    session_service.ensure_session(body.session_id)

    resume_id = None
    if body.resume_text:
        resume_id, resume_json = resume_service.ingest_resume_from_text(
            body.session_id, body.resume_text
        )
    else:
        raise ResourceNotFoundError("Provide resume_text, or call /resume/upload first and pass resume_id via /analyze/{resume_id}.")

    jd_id, jd_json = (None, None)
    if body.jd_text and body.jd_text.strip():
        jd_id, jd_json = jd_service.ingest_jd_from_text(body.session_id, body.jd_text)

    result = analysis_service.run_analysis(
        session_id=body.session_id,
        resume_id=resume_id,
        resume=resume_json,
        jd_id=jd_id,
        jd=jd_json,
    )
    result["resume_id"] = resume_id
    if jd_id:
        result["jd_id"] = jd_id
    return result


@router.post("/by-id/{resume_id}")
@limiter.limit("10/hour")
async def analyze_existing(request: Request, resume_id: str, session_id: str, jd_text: str | None = None):
    """Analyze a previously-uploaded resume (by resume_id) against an optional JD."""
    session_service.ensure_session(session_id)
    resume_json = resume_service.get_resume_json(resume_id)

    jd_id, jd_json = (None, None)
    if jd_text and jd_text.strip():
        jd_id, jd_json = jd_service.ingest_jd_from_text(session_id, jd_text)

    result = analysis_service.run_analysis(
        session_id=session_id,
        resume_id=resume_id,
        resume=resume_json,
        jd_id=jd_id,
        jd=jd_json,
    )
    result["resume_id"] = resume_id
    if jd_id:
        result["jd_id"] = jd_id
    return result


@router.get("/{analysis_id}")
async def get_analysis(analysis_id: str):
    sb = get_supabase()
    resp = sb.table("analysis_results").select("*").eq("id", analysis_id).limit(1).execute()
    if not resp.data:
        raise ResourceNotFoundError(f"No analysis found for id={analysis_id}")
    return resp.data[0]

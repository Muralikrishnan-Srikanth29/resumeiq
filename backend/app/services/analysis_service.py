from app.ai.gemini_service import get_gemini_service
from app.core.exceptions import DatabaseError
from app.core.logging import get_logger
from app.db.supabase_client import get_supabase
from app.rules.engine import run_rule_engine
from app.schemas.analysis import AIAnalysisOutput
from app.schemas.job_description import JDJSON
from app.schemas.resume import ResumeJSON

logger = get_logger(__name__)


def run_analysis(
    session_id: str,
    resume_id: str,
    resume: ResumeJSON,
    jd_id: str | None,
    jd: JDJSON | None,
) -> dict:
    """
    Full pipeline orchestration:
      1. Rule engine (deterministic, free)
      2. Gemini call with ONLY compact summaries + rule output (cheap)
      3. Persist combined result
      4. Append to resume_history for trend tracking
    """
    sb = get_supabase()
    gemini = get_gemini_service()

    rule_result = run_rule_engine(resume, jd)
    rule_ai_input = rule_result.to_ai_input()
    resume_summary = resume.to_compact_summary()

    if jd is None:
        ai_output, tokens_used = gemini.analyze_evaluation(resume_summary, rule_ai_input)
    else:
        jd_summary = jd.to_compact_summary()
        ai_output, tokens_used = gemini.analyze_matching(resume_summary, jd_summary, rule_ai_input)

    record = _build_analysis_record(
        session_id, resume_id, jd_id, rule_result, ai_output, tokens_used
    )

    insert_resp = sb.table("analysis_results").insert(record).execute()
    if not insert_resp.data:
        raise DatabaseError("Failed to persist analysis result.")
    analysis_id = insert_resp.data[0]["id"]

    _persist_interview_questions(sb, analysis_id, ai_output)
    _append_history(sb, session_id, analysis_id, rule_result, ai_output)

    return {
        "analysis_id": analysis_id,
        "mode": rule_result.mode,
        "scores": rule_result.scores.model_dump(),
        "match_scores": rule_result.match_scores.model_dump() if rule_result.match_scores else None,
        "gaps": rule_result.gaps.model_dump(),
        "ai": ai_output,
        "tokens_used": tokens_used,
    }


def _build_analysis_record(session_id, resume_id, jd_id, rule_result, ai_output: AIAnalysisOutput, tokens_used: int) -> dict:
    rec = {
        "session_id": session_id,
        "resume_id": resume_id,
        "jd_id": jd_id,
        "mode": rule_result.mode,
        **rule_result.scores.model_dump(),
        "exact_skill_matches": rule_result.gaps.exact_skill_matches,
        "missing_skills": rule_result.gaps.missing_skills,
        "missing_certifications": rule_result.gaps.missing_certifications,
        "missing_keywords": rule_result.gaps.missing_keywords,
        "missing_sections": rule_result.gaps.missing_sections,
        "strengths": ai_output.strengths,
        "weaknesses": ai_output.weaknesses,
        "recruiter_eye_view": ai_output.recruiter_eye_view.model_dump(),
        "line_improvements": [li.model_dump() for li in ai_output.line_improvements],
        "heat_map": ai_output.heat_map,
        "shortlist_probability": ai_output.shortlist_probability,
        "shortlist_reasoning": ai_output.shortlist_reasoning,
        "interview_questions": ai_output.interview_questions.model_dump(),
        "ai_tokens_used": tokens_used,
        "processing_status": "completed",
    }
    if rule_result.match_scores:
        rec.update(rule_result.match_scores.model_dump())
    return rec


def _persist_interview_questions(sb, analysis_id: str, ai_output: AIAnalysisOutput) -> None:
    rows = []
    for category, questions in ai_output.interview_questions.model_dump().items():
        for q in questions:
            rows.append({"analysis_id": analysis_id, "category": category, "question": q})
    if rows:
        sb.table("interview_questions").insert(rows).execute()


def _append_history(sb, session_id: str, analysis_id: str, rule_result, ai_output: AIAnalysisOutput) -> None:
    gap_count = (
        len(rule_result.gaps.missing_skills)
        + len(rule_result.gaps.missing_certifications)
        + len(rule_result.gaps.missing_sections)
    )
    sb.table("resume_history").insert(
        {
            "session_id": session_id,
            "analysis_id": analysis_id,
            "resume_score": rule_result.scores.resume_score,
            "ats_score": rule_result.scores.ats_score,
            "gap_count": gap_count,
        }
    ).execute()


def get_history(session_id: str, limit: int = 20) -> list[dict]:
    sb = get_supabase()
    resp = (
        sb.table("resume_history")
        .select("*")
        .eq("session_id", session_id)
        .order("recorded_at", desc=False)
        .limit(limit)
        .execute()
    )
    return resp.data or []


def get_dashboard_metrics(session_id: str) -> dict:
    sb = get_supabase()
    latest = (
        sb.table("analysis_results")
        .select("*")
        .eq("session_id", session_id)
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )
    if not latest.data:
        return {}
    row = latest.data[0]
    gap_count = (
        len(row.get("missing_skills") or [])
        + len(row.get("missing_certifications") or [])
        + len(row.get("missing_sections") or [])
    )
    return {
        "resume_score": row.get("resume_score"),
        "ats_score": row.get("ats_score"),
        "match_score": row.get("overall_match_score"),
        "recruiter_score": (row.get("recruiter_eye_view") or {}).get("confidence_score"),
        "gap_count": gap_count,
        "shortlist_probability": row.get("shortlist_probability"),
        "mode": row.get("mode"),
        "analysis_id": row.get("id"),
    }

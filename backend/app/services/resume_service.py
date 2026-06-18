"""
Orchestrates resume ingestion: dedup-check by checksum (never re-parse
the same content twice), extract/parse, persist resume + resume_json.
"""
from app.core.exceptions import DatabaseError, ResourceNotFoundError
from app.core.logging import get_logger
from app.db.supabase_client import get_supabase
from app.parsers.file_extractor import extract_text
from app.parsers.resume_parser import parse_resume_text
from app.schemas.resume import ResumeJSON
from app.utils.validation import sha256_of, validate_resume_text

logger = get_logger(__name__)


def ingest_resume_from_text(session_id: str, raw_text: str) -> tuple[str, ResumeJSON]:
    """Returns (resume_id, ResumeJSON). Reuses cached parse if checksum matches."""
    cleaned = validate_resume_text(raw_text)
    checksum = sha256_of(cleaned)
    return _ingest(session_id, cleaned, checksum, input_method="paste", file_type="text")


def ingest_resume_from_file(session_id: str, file_bytes: bytes, filename: str) -> tuple[str, ResumeJSON]:
    extracted_text, file_type = extract_text(file_bytes, filename)
    cleaned = validate_resume_text(extracted_text)
    checksum = sha256_of(cleaned)
    return _ingest(
        session_id,
        cleaned,
        checksum,
        input_method="upload",
        file_type=file_type,
        file_name=filename,
        file_size_bytes=len(file_bytes),
    )


def _ingest(
    session_id: str,
    cleaned_text: str,
    checksum: str,
    input_method: str,
    file_type: str,
    file_name: str | None = None,
    file_size_bytes: int | None = None,
) -> tuple[str, ResumeJSON]:
    sb = get_supabase()

    existing = (
        sb.table("resumes")
        .select("id, parse_status")
        .eq("session_id", session_id)
        .eq("content_checksum", checksum)
        .limit(1)
        .execute()
    )
    if existing.data:
        resume_id = existing.data[0]["id"]
        cached = sb.table("resume_json").select("*").eq("resume_id", resume_id).limit(1).execute()
        if cached.data:
            logger.info("Resume cache hit for checksum=%s", checksum[:12])
            return resume_id, _row_to_resume_json(cached.data[0])

    insert_resp = (
        sb.table("resumes")
        .insert(
            {
                "session_id": session_id,
                "input_method": input_method,
                "file_name": file_name,
                "file_type": file_type,
                "file_size_bytes": file_size_bytes,
                "content_checksum": checksum,
                "raw_text": cleaned_text,
                "parse_status": "processing",
            }
        )
        .execute()
    )
    if not insert_resp.data:
        raise DatabaseError("Failed to create resume record.")
    resume_id = insert_resp.data[0]["id"]

    try:
        resume_json = parse_resume_text(cleaned_text)
        sb.table("resume_json").insert(
            {
                "resume_id": resume_id,
                "name": resume_json.name,
                "email": resume_json.email,
                "phone": resume_json.phone,
                "linkedin": resume_json.linkedin,
                "github": resume_json.github,
                "portfolio_url": resume_json.portfolio_url,
                "experience_years": resume_json.experience_years,
                "skills": resume_json.skills,
                "education": [e.model_dump() for e in resume_json.education],
                "certifications": [c.model_dump() for c in resume_json.certifications],
                "projects": [p.model_dump() for p in resume_json.projects],
                "experience": [e.model_dump() for e in resume_json.experience],
                "achievements": resume_json.achievements,
                "summary_text": resume_json.summary_text,
                "sections_detected": resume_json.sections_detected,
            }
        ).execute()
        sb.table("resumes").update({"parse_status": "completed"}).eq("id", resume_id).execute()
        return resume_id, resume_json
    except Exception as exc:
        sb.table("resumes").update(
            {"parse_status": "failed", "parse_error": str(exc)}
        ).eq("id", resume_id).execute()
        raise


def get_resume_json(resume_id: str) -> ResumeJSON:
    sb = get_supabase()
    resp = sb.table("resume_json").select("*").eq("resume_id", resume_id).limit(1).execute()
    if not resp.data:
        raise ResourceNotFoundError(f"No parsed data found for resume_id={resume_id}")
    return _row_to_resume_json(resp.data[0])


def _row_to_resume_json(row: dict) -> ResumeJSON:
    return ResumeJSON(
        name=row.get("name") or "",
        email=row.get("email") or "",
        phone=row.get("phone") or "",
        linkedin=row.get("linkedin") or "",
        github=row.get("github") or "",
        portfolio_url=row.get("portfolio_url") or "",
        experience_years=row.get("experience_years") or 0,
        skills=row.get("skills") or [],
        education=row.get("education") or [],
        certifications=row.get("certifications") or [],
        projects=row.get("projects") or [],
        experience=row.get("experience") or [],
        achievements=row.get("achievements") or [],
        summary_text=row.get("summary_text") or "",
        sections_detected=row.get("sections_detected") or [],
    )

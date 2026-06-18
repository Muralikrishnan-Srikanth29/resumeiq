from app.core.exceptions import DatabaseError
from app.core.logging import get_logger
from app.db.supabase_client import get_supabase
from app.parsers.jd_parser import parse_jd_text
from app.schemas.job_description import JDJSON
from app.utils.validation import sha256_of, validate_jd_text

logger = get_logger(__name__)


def ingest_jd_from_text(session_id: str, raw_text: str) -> tuple[str, JDJSON]:
    cleaned = validate_jd_text(raw_text)
    checksum = sha256_of(cleaned)
    sb = get_supabase()

    existing = (
        sb.table("job_descriptions")
        .select("id")
        .eq("session_id", session_id)
        .eq("text_checksum", checksum)
        .limit(1)
        .execute()
    )
    if existing.data:
        jd_id = existing.data[0]["id"]
        cached = sb.table("jd_json").select("*").eq("jd_id", jd_id).limit(1).execute()
        if cached.data:
            logger.info("JD cache hit for checksum=%s", checksum[:12])
            return jd_id, _row_to_jd_json(cached.data[0])

    insert_resp = (
        sb.table("job_descriptions")
        .insert({"session_id": session_id, "raw_text": cleaned, "text_checksum": checksum})
        .execute()
    )
    if not insert_resp.data:
        raise DatabaseError("Failed to create job description record.")
    jd_id = insert_resp.data[0]["id"]

    jd_json = parse_jd_text(cleaned)
    sb.table("jd_json").insert(
        {
            "jd_id": jd_id,
            "required_skills": jd_json.required_skills,
            "preferred_skills": jd_json.preferred_skills,
            "experience_required": jd_json.experience_required,
            "certifications": jd_json.certifications,
            "domain": jd_json.domain,
            "role_title": jd_json.role_title,
            "seniority_level": jd_json.seniority_level,
            "keywords": jd_json.keywords,
        }
    ).execute()
    sb.table("job_descriptions").update(
        {"title": jd_json.role_title}
    ).eq("id", jd_id).execute()

    return jd_id, jd_json


def _row_to_jd_json(row: dict) -> JDJSON:
    return JDJSON(
        required_skills=row.get("required_skills") or [],
        preferred_skills=row.get("preferred_skills") or [],
        experience_required=row.get("experience_required") or 0,
        certifications=row.get("certifications") or [],
        domain=row.get("domain") or "",
        role_title=row.get("role_title") or "",
        seniority_level=row.get("seniority_level") or "",
        keywords=row.get("keywords") or [],
    )

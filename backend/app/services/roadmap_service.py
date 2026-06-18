from app.ai.gemini_service import get_gemini_service
from app.core.exceptions import DatabaseError
from app.db.supabase_client import get_supabase
from app.schemas.resume import ResumeJSON


def generate_roadmap(session_id: str, resume_id: str, resume: ResumeJSON, current_role: str, target_role: str) -> dict:
    gemini = get_gemini_service()
    resume_summary = resume.to_compact_summary()

    ai_data, tokens_used = gemini.generate_roadmap(resume_summary, current_role, target_role)

    sb = get_supabase()
    insert_resp = (
        sb.table("career_roadmaps")
        .insert(
            {
                "session_id": session_id,
                "resume_id": resume_id,
                "current_role": current_role,
                "target_role": target_role,
                "skill_gaps": ai_data.get("skill_gaps", []),
                "certification_gaps": ai_data.get("certification_gaps", []),
                "learning_path": ai_data.get("learning_path", []),
                "roadmap_90_day": ai_data.get("roadmap_90_day", []),
                "ai_tokens_used": tokens_used,
            }
        )
        .execute()
    )
    if not insert_resp.data:
        raise DatabaseError("Failed to persist career roadmap.")

    roadmap_id = insert_resp.data[0]["id"]
    return {
        "roadmap_id": roadmap_id,
        "skill_gaps": ai_data.get("skill_gaps", []),
        "certification_gaps": ai_data.get("certification_gaps", []),
        "learning_path": ai_data.get("learning_path", []),
        "roadmap_90_day": ai_data.get("roadmap_90_day", []),
    }

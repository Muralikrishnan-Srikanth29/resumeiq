"""
Anonymous sessions. No login: the frontend generates/stores a UUID in
localStorage and sends it as session_id on every request. This endpoint
just registers it server-side so FK constraints have something to point
to, and updates last_seen_at for the 90-day cleanup job.
"""
from app.db.supabase_client import get_supabase


def ensure_session(session_id: str) -> str:
    sb = get_supabase()
    existing = sb.table("sessions").select("id").eq("id", session_id).limit(1).execute()
    if existing.data:
        sb.table("sessions").update({"last_seen_at": "now()"}).eq("id", session_id).execute()
        return session_id

    sb.table("sessions").insert({"id": session_id}).execute()
    return session_id

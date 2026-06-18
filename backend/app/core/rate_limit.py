"""
Rate limiting keyed by session_id (falls back to client IP if absent).
Protects the Gemini-calling endpoints from abuse since there's no login
to throttle by account.
"""
from slowapi import Limiter
from slowapi.util import get_remote_address
from starlette.requests import Request


def _session_or_ip_key(request: Request) -> str:
    session_id = request.headers.get("X-Session-Id") or request.query_params.get("session_id")
    return session_id or get_remote_address(request)


limiter = Limiter(key_func=_session_or_ip_key)

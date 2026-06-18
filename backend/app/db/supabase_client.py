"""
Single Supabase client instance using the SERVICE ROLE key.
This backend is the only thing that ever talks to Supabase tables —
the Next.js frontend never holds a Supabase key, it only calls FastAPI.
That's what makes RLS-disabled tables safe here: there's exactly one
trusted caller, and it's this process.
"""
from functools import lru_cache

from supabase import create_client, Client
from supabase.client import ClientOptions

from app.core.config import get_settings

# Without explicit timeouts, a misconfigured/unreachable SUPABASE_URL hangs
# the request indefinitely instead of surfacing a clear 503. 10s is generous
# for Postgres queries but still fails fast on DNS/connection issues.
_CLIENT_OPTIONS = ClientOptions(postgrest_client_timeout=10, storage_client_timeout=10)


@lru_cache
def get_supabase() -> Client:
    settings = get_settings()
    return create_client(
        settings.SUPABASE_URL,
        settings.SUPABASE_SERVICE_ROLE_KEY,
        options=_CLIENT_OPTIONS,
    )


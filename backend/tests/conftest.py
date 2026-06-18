"""
Sets placeholder env vars before any app module is imported, so unit
tests that only exercise parsers/rule-engine logic (no real network
calls) don't require real Supabase/Gemini credentials to even import
the app package (Settings() validation would otherwise fail at import
time since SUPABASE_URL etc. are required fields).
"""
import os

os.environ.setdefault("SUPABASE_URL", "https://placeholder.supabase.co")
os.environ.setdefault("SUPABASE_SERVICE_ROLE_KEY", "placeholder")
os.environ.setdefault("GEMINI_API_KEY", "placeholder")
os.environ.setdefault("ALLOWED_ORIGINS", "http://localhost:3000")

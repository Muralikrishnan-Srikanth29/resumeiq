-- ============================================================
-- ResumeIQ Database Schema — Supabase PostgreSQL
-- v2: No login wall. Anonymous session_id replaces auth.users FK.
-- Input: pasted resume text OR PDF/DOCX upload. Same for JD (paste only).
-- Run via Supabase SQL Editor or `supabase db push`
-- ============================================================

create extension if not exists "uuid-ossp";
create extension if not exists pgcrypto;

-- ============================================================
-- SESSIONS (anonymous, client-generated UUID stored in localStorage)
-- No login. This exists purely to scope history/trend queries.
-- ============================================================
create table public.sessions (
    id uuid primary key default uuid_generate_v4(),
    created_at timestamptz not null default now(),
    last_seen_at timestamptz not null default now()
);

-- ============================================================
-- RESUMES (input metadata — either uploaded file OR pasted text)
-- ============================================================
create table public.resumes (
    id uuid primary key default uuid_generate_v4(),
    session_id uuid not null references public.sessions(id) on delete cascade,
    input_method text not null check (input_method in ('upload', 'paste')),
    file_name text,                        -- null if pasted
    file_path text,                        -- Supabase Storage path, null if pasted
    file_type text check (file_type in ('pdf', 'docx', 'text')),
    file_size_bytes int,
    content_checksum text not null,        -- sha256 of extracted text, used for parse cache dedup
    raw_text text not null,                -- extracted (from file) or pasted directly
    parse_status text not null default 'pending'
        check (parse_status in ('pending', 'processing', 'completed', 'failed')),
    parse_error text,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    unique (session_id, content_checksum)
);

create index idx_resumes_session_id on public.resumes(session_id);
create index idx_resumes_checksum on public.resumes(content_checksum);

-- ============================================================
-- RESUME_JSON (structured, cached parse output)
-- ============================================================
create table public.resume_json (
    id uuid primary key default uuid_generate_v4(),
    resume_id uuid not null references public.resumes(id) on delete cascade unique,
    name text,
    email text,
    phone text,
    linkedin text,
    github text,
    portfolio_url text,
    experience_years numeric(4,1) default 0,
    skills jsonb not null default '[]',
    education jsonb not null default '[]',
    certifications jsonb not null default '[]',
    projects jsonb not null default '[]',
    experience jsonb not null default '[]',
    achievements jsonb not null default '[]',
    summary_text text,
    sections_detected jsonb not null default '[]',
    parser_version text not null default 'v1',
    created_at timestamptz not null default now()
);

create index idx_resume_json_resume_id on public.resume_json(resume_id);
create index idx_resume_json_skills on public.resume_json using gin (skills);

-- ============================================================
-- JOB_DESCRIPTIONS (pasted text only — no JD file upload in scope)
-- ============================================================
create table public.job_descriptions (
    id uuid primary key default uuid_generate_v4(),
    session_id uuid not null references public.sessions(id) on delete cascade,
    raw_text text not null,
    text_checksum text not null,
    title text,
    company text,
    created_at timestamptz not null default now(),
    unique (session_id, text_checksum)
);

create index idx_jd_session_id on public.job_descriptions(session_id);

-- ============================================================
-- JD_JSON (structured, cached parse output)
-- ============================================================
create table public.jd_json (
    id uuid primary key default uuid_generate_v4(),
    jd_id uuid not null references public.job_descriptions(id) on delete cascade unique,
    required_skills jsonb not null default '[]',
    preferred_skills jsonb not null default '[]',
    experience_required numeric(4,1) default 0,
    certifications jsonb not null default '[]',
    domain text,
    role_title text,
    seniority_level text,
    keywords jsonb not null default '[]',
    parser_version text not null default 'v1',
    created_at timestamptz not null default now()
);

create index idx_jd_json_jd_id on public.jd_json(jd_id);

-- ============================================================
-- ANALYSIS_RESULTS (rule engine + AI output, one row per analysis run)
-- ============================================================
create table public.analysis_results (
    id uuid primary key default uuid_generate_v4(),
    session_id uuid not null references public.sessions(id) on delete cascade,
    resume_id uuid not null references public.resumes(id) on delete cascade,
    jd_id uuid references public.job_descriptions(id) on delete set null,  -- null = evaluation mode
    mode text not null check (mode in ('evaluation', 'matching')),

    resume_score numeric(5,2),
    ats_score numeric(5,2),
    content_score numeric(5,2),
    formatting_score numeric(5,2),
    impact_score numeric(5,2),
    project_score numeric(5,2),
    achievements_score numeric(5,2),
    summary_score numeric(5,2),
    skills_score numeric(5,2),
    education_score numeric(5,2),

    overall_match_score numeric(5,2),
    skills_match_score numeric(5,2),
    experience_match_score numeric(5,2),
    keyword_match_score numeric(5,2),
    certification_match_score numeric(5,2),
    ats_match_score numeric(5,2),
    domain_match_score numeric(5,2),

    exact_skill_matches jsonb default '[]',
    missing_skills jsonb default '[]',
    missing_certifications jsonb default '[]',
    missing_keywords jsonb default '[]',
    missing_sections jsonb default '[]',

    strengths jsonb default '[]',
    weaknesses jsonb default '[]',
    recruiter_eye_view jsonb default '{}',
    line_improvements jsonb default '[]',
    heat_map jsonb default '{}',
    shortlist_probability text check (shortlist_probability in ('Low','Medium','High')),
    shortlist_reasoning text,
    interview_questions jsonb default '{}',

    ai_tokens_used int default 0,
    ai_model text default 'gemini-2.5-flash',
    processing_status text not null default 'pending'
        check (processing_status in ('pending','rule_engine_done','ai_processing','completed','failed')),
    error_message text,

    created_at timestamptz not null default now(),
    completed_at timestamptz
);

create index idx_analysis_session_id on public.analysis_results(session_id);
create index idx_analysis_resume_id on public.analysis_results(resume_id);
create index idx_analysis_created_at on public.analysis_results(created_at desc);

-- ============================================================
-- RESUME_HISTORY (denormalized trend tracking for fast charting)
-- ============================================================
create table public.resume_history (
    id uuid primary key default uuid_generate_v4(),
    session_id uuid not null references public.sessions(id) on delete cascade,
    analysis_id uuid not null references public.analysis_results(id) on delete cascade,
    resume_score numeric(5,2),
    ats_score numeric(5,2),
    skills_count int,
    certifications_count int,
    gap_count int,
    recorded_at timestamptz not null default now()
);

create index idx_history_session_recorded on public.resume_history(session_id, recorded_at);

-- ============================================================
-- CAREER_ROADMAPS
-- ============================================================
create table public.career_roadmaps (
    id uuid primary key default uuid_generate_v4(),
    session_id uuid not null references public.sessions(id) on delete cascade,
    resume_id uuid references public.resumes(id) on delete set null,
    current_role text not null,
    target_role text not null,
    skill_gaps jsonb default '[]',
    certification_gaps jsonb default '[]',
    learning_path jsonb default '[]',
    roadmap_90_day jsonb default '[]',
    ai_tokens_used int default 0,
    created_at timestamptz not null default now()
);

create index idx_roadmap_session_id on public.career_roadmaps(session_id);

-- ============================================================
-- INTERVIEW_QUESTIONS
-- ============================================================
create table public.interview_questions (
    id uuid primary key default uuid_generate_v4(),
    analysis_id uuid not null references public.analysis_results(id) on delete cascade,
    category text not null check (category in ('technical','behavioral','leadership','project_based')),
    question text not null,
    rationale text,
    created_at timestamptz not null default now()
);

create index idx_interview_q_analysis_id on public.interview_questions(analysis_id);

-- ============================================================
-- ACTIVITY_LOGS (audit trail + rate limiting by session/IP)
-- ============================================================
create table public.activity_logs (
    id uuid primary key default uuid_generate_v4(),
    session_id uuid references public.sessions(id) on delete set null,
    action text not null,
    resource_id uuid,
    metadata jsonb default '{}',
    ip_address text,
    created_at timestamptz not null default now()
);

create index idx_activity_session_created on public.activity_logs(session_id, created_at desc);
create index idx_activity_action on public.activity_logs(action);

-- ============================================================
-- ROW LEVEL SECURITY
-- No auth.uid() available without login, so RLS is disabled and
-- access control is enforced entirely at the FastAPI layer using the
-- Supabase service_role key. The anon key is NEVER exposed to the
-- browser for table access — frontend only talks to FastAPI, never
-- directly to Supabase tables. This is the correct posture for a
-- no-login app: there is no identity for RLS to check against.
-- ============================================================
alter table public.sessions disable row level security;
alter table public.resumes disable row level security;
alter table public.resume_json disable row level security;
alter table public.job_descriptions disable row level security;
alter table public.jd_json disable row level security;
alter table public.analysis_results disable row level security;
alter table public.resume_history disable row level security;
alter table public.career_roadmaps disable row level security;
alter table public.interview_questions disable row level security;
alter table public.activity_logs disable row level security;

-- ============================================================
-- TRIGGERS: updated_at maintenance
-- ============================================================
create or replace function public.set_updated_at()
returns trigger as $$
begin
    new.updated_at = now();
    return new;
end;
$$ language plpgsql;

create trigger trg_resumes_updated_at before update on public.resumes
    for each row execute function public.set_updated_at();

-- ============================================================
-- CLEANUP: auto-purge sessions older than 90 days (privacy hygiene,
-- since there's no account ownership to anchor data retention to).
-- Requires pg_cron extension (enable in Supabase Dashboard > Database
-- > Extensions first, then run the schedule call below).
-- ============================================================
-- create extension if not exists pg_cron;
-- select cron.schedule(
--     'purge-stale-sessions',
--     '0 3 * * *',
--     $$ delete from public.sessions where last_seen_at < now() - interval '90 days'; $$
-- );

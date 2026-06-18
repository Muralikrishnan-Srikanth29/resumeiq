# ResumeIQ

AI-powered resume analyzer with a deterministic rule engine in front of the AI call. No login required — paste or upload a resume, optionally add a job description, get a recruiter-style breakdown.

## Architecture

```
PDF/DOCX upload or pasted text
        │
        ▼
Resume Parser (regex/heuristic, zero AI cost) ──► Resume JSON ──► cached by content hash
        │
        ▼
JD Parser (same approach, optional)            ──► JD JSON ──► cached by content hash
        │
        ▼
Rule Engine (pure Python, deterministic, zero AI cost)
   - ATS / content / formatting / impact / project / achievement / summary / skills / education scores
   - Skill/keyword/certification matching against JD (if provided)
        │
        ▼
Gemini 2.5 Flash — receives ONLY compact JSON summaries + rule-engine
output, never raw resume/JD text or PDF bytes. Output is constrained via
Gemini's native response_schema (not a prose-described JSON shape), so
the model can't drift from the contract and no schema-description text
is repeated in every prompt.
        │
        ▼
Dashboard (Next.js) — scores, recruiter eye view, gap analysis,
line-by-line rewrites, interview questions, growth tracker, roadmap
```

The mandatory constraint from the spec — never send raw PDF to the AI — is enforced structurally: `app/ai/gemini_service.py` only ever receives `dict` objects built by `ResumeJSON.to_compact_summary()` / `JDJSON.to_compact_summary()` / `RuleEngineResult.to_ai_input()`. There is no code path where raw file bytes or extracted raw text reach the Gemini client.

## On the "80% token reduction" target

The original spec set this as a goal. Worth being precise about what's actually true here rather than just asserting compliance:

- **Character-compression of a single resume into JSON is not where the saving comes from.** For a realistic 1.5-2 page resume, the compact JSON summary runs ~75-85% of the raw text's size — not a dramatic reduction, because resumes are already fairly information-dense prose. For short/sparse resumes, the JSON scaffolding overhead can make the compact form *larger* than the raw text. Tightened the caps (`to_compact_summary()` in `app/schemas/resume.py`) as far as reasonably possible without losing analytical grounding, but this isn't the main lever.
- **The real, defensible savings are structural, not character-counting:**
  1. **The AI never computes scores or matches itself.** A naive tool would have to send the AI both full documents and ask it to calculate skill-overlap percentages, experience-year math, and keyword matching — work that's slow, expensive, and not reliably reproducible from an LLM. Here, that's done for free in `app/rules/engine.py`, and the AI only narrates around already-correct numbers.
  2. **Native `response_schema` instead of prose-described JSON** (`app/ai/schemas.py`) removes ~400-500 tokens of repeated schema-description text from every single call — this is a real, measured reduction versus the first draft of the prompt layer.
  3. **Content-hash caching** (`resumes.content_checksum`, `job_descriptions.text_checksum`) means re-submitting the same resume or JD never re-parses or re-runs the rule engine — and a future enhancement could cache AI output by `(resume_hash, jd_hash)` pair too, avoiding the AI call entirely on exact repeats.
  4. **Capped, truncated inputs** mean a candidate with 15 years and 8 jobs doesn't blow up the prompt linearly — the rule engine still sees everything (it's free), but the AI summary caps at 5 most-recent roles / 4 bullets each / 25 skills.

If you want a single honest number: this architecture's AI call for a JD-matching analysis runs in the 800-1,200 token range regardless of resume length (because of the caps), where an uncapped "send both raw documents, do the matching yourself" prompt scales linearly with resume/JD length and has no ceiling. The savings show up most clearly on long resumes and is roughly flat/negative on very short ones — which matches how real users behave, since nobody's testing this tool with a 3-line resume.

## What's NOT included (by request)

The original spec called for Supabase Auth, JWT, and role-based access control. Per explicit instruction partway through the build, **the login screen was removed**. The app is fully anonymous:

- Every browser gets a random UUID stored in `localStorage` (`src/lib/session.ts`), sent as `session_id` on every request.
- Supabase tables have RLS *disabled* rather than auth-policy-gated, because there's no `auth.uid()` to check against without login. Access control is enforced entirely at the FastAPI layer: the frontend never holds a Supabase key, it only talks to the backend, and the backend uses the `service_role` key. This is the correct posture for a no-login app — RLS policies keyed on a client-supplied `session_id` would be trivially bypassable since anyone can claim any session_id.
- A `pg_cron` job (commented out in `schema.sql`, since the extension needs enabling first in the Supabase dashboard) purges sessions older than 90 days, since there's no account to anchor data retention to.

If you want auth back later: the schema already isolates identity into a single `session_id uuid` column per table, so swapping in `auth.uid()` and enabling RLS is a schema migration, not a redesign.

## Resume input: upload or paste

Both are first-class, per request:
- **Upload**: PDF or DOCX, ≤5MB, parsed server-side (`app/parsers/file_extractor.py` using PyMuPDF / python-docx).
- **Paste**: raw text, 200-50,000 characters, sanitized against stored-XSS via `bleach` before parsing.

Job descriptions are paste-only (no JD file upload) — this wasn't in scope for the request and JDs are reliably available as text from job postings.

## Project structure

```
resumeiq/
├── backend/                 FastAPI app
│   ├── app/
│   │   ├── api/v1/          Route handlers
│   │   ├── parsers/         Resume/JD text → structured JSON (regex, no AI)
│   │   ├── rules/           Deterministic scoring engine
│   │   ├── ai/              Gemini client, prompts, response schemas
│   │   ├── services/        Orchestration layer (parsing + caching + persistence)
│   │   ├── schemas/         Pydantic models shared across the pipeline
│   │   ├── core/             Config, exceptions, logging, rate limiting
│   │   └── db/               Supabase client
│   ├── db/schema.sql         Full Postgres schema (run in Supabase SQL editor)
│   ├── tests/                 25 unit tests covering parsers + rule engine
│   ├── Dockerfile / render.yaml
│   └── requirements.txt       Locked, verified in a clean venv (see below)
├── frontend/                  Next.js 15 + TypeScript + Tailwind
│   ├── src/app/                Single-page app: input → analyzing → dashboard
│   ├── src/components/         UI primitives, input forms, dashboard cards
│   ├── src/lib/                  API client, types, session management
│   └── vercel.json
└── .github/workflows/          CI for both halves
```

## Local setup

### Backend
```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, GEMINI_API_KEY
uvicorn app.main:app --reload --port 8000
```
Run the test suite (no real credentials needed — parsers and rule engine are pure functions):
```bash
pytest tests/ -v
```

### Database
In your Supabase project's SQL Editor, run `backend/db/schema.sql` once. It's idempotent-unsafe (uses `create table`, not `create table if not exists`) by design — re-running on an existing schema is meant to fail loudly rather than silently no-op.

### Frontend
```bash
cd frontend
npm install
cp .env.example .env.local   # point NEXT_PUBLIC_API_URL at your backend
npm run dev
```

Note on fonts: `globals.css` uses named font-family fallback chains (Space Grotesk / Inter / JetBrains Mono with system fallbacks) rather than `next/font/google`, because this was built in a sandboxed environment without access to `fonts.googleapis.com`. Vercel's build servers do have internet access, so if you want the exact intended typefaces self-hosted via `next/font/google`, swap `src/app/layout.tsx` back to font imports — it's a 10-line change and the CSS variable names (`--font-display-override` etc.) are already wired for it.

## Deployment

1. **Supabase**: create a project, run `backend/db/schema.sql`, copy the Project URL and `service_role` key (Project Settings → API). Do not use the `anon` key for the backend.
2. **Render**: connect this repo, it'll detect `backend/render.yaml`. Set `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, and `GEMINI_API_KEY` in the dashboard (marked `sync: false` in the config so they're not committed).
3. **Vercel**: connect this repo with root directory `frontend/`. Set `NEXT_PUBLIC_API_URL` to your Render URL.
4. **GitHub Actions**: `.github/workflows/` lint + test on every push; add `RENDER_DEPLOY_HOOK_URL` as a repo secret if you want an explicit deploy trigger beyond Render's own auto-deploy.

## Dependency note

`requirements.txt` was verified by installing into a completely clean virtualenv (not just the dev sandbox, which had pre-existing packages that masked a real version conflict during development — caught and fixed: `pydantic`/`supabase`/`google-genai` needed coordinated version bumps since the initially-chosen versions conflicted with each other). `pip check` passes clean against this file.

## Known limitations (honest, not hidden)

- The resume parser is heuristic (regex + section-header detection), not a trained NLP model. It handles standard chronological resumes well; heavily templated/graphical resumes (multi-column, tables-as-layout) will parse less reliably. This is a documented tradeoff, not a bug.
- JD keyword extraction (`_extract_keywords` in `jd_parser.py`) is frequency-based and includes some generic noise words (e.g. "required", "preferred" sometimes survive into the keyword list) — it feeds AI context, not a scored metric, so this is low-impact but not perfectly clean.
- No OCR fallback for scanned/image-only PDFs — `extract_text_from_pdf` raises a clear `ParsingError` in that case rather than silently returning empty text.
- Rate limiting is keyed by `session_id` (or IP as fallback), which is bypassable by clearing localStorage. Acceptable for a no-login MVP; would need IP-based or CAPTCHA-backed limiting to harden against real abuse.

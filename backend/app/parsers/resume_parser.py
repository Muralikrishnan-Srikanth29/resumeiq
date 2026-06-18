"""
Converts plain resume text into structured ResumeJSON using heuristics
and regex — deliberately NOT an AI call. This is the core of the
token-reduction architecture: structuring happens for free, and only
the compact structured summary (a few hundred tokens) ever reaches
Gemini, instead of the full raw resume (often 1500+ tokens).

This is intentionally pragmatic rather than a full NLP pipeline:
section-header detection + regex entity extraction handles the vast
majority of real-world resume formats well. It will not be perfect
on heavily templated/graphical resumes — that's a known, accepted
tradeoff documented in the README.
"""
import re

from app.schemas.resume import (
    CertificationEntry,
    EducationEntry,
    ExperienceEntry,
    ProjectEntry,
    ResumeJSON,
)

# --- Section header patterns (case-insensitive, line must be short = likely a header) ---
SECTION_PATTERNS = {
    "summary": r"^(professional\s+)?summary|objective|profile$",
    "experience": r"^(work\s+|professional\s+)?experience|employment\s+history$",
    "education": r"^education(al\s+background)?$",
    "skills": r"^(technical\s+|core\s+)?skills|technologies|competencies$",
    "projects": r"^projects?(\s+experience)?$",
    "certifications": r"^certifications?|licenses?(\s+&\s+certifications?)?$",
    "achievements": r"^achievements?|awards?|honou?rs?$",
}

EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
PHONE_RE = re.compile(r"(\+?\d{1,3}[-.\s]?)?\(?\d{3,4}\)?[-.\s]?\d{3,4}[-.\s]?\d{3,4}")
LINKEDIN_RE = re.compile(r"(https?://)?(www\.)?linkedin\.com/in/[A-Za-z0-9\-_/]+", re.I)
GITHUB_RE = re.compile(r"(https?://)?(www\.)?github\.com/[A-Za-z0-9\-_/]+", re.I)
URL_RE = re.compile(r"https?://[^\s,]+")
YEAR_RANGE_RE = re.compile(
    r"(?P<start>(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?\s*\d{4}|\d{4})"
    r"\s*[-–—to]+\s*"
    r"(?P<end>(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?\s*\d{4}|\d{4}|present|current)",
    re.I,
)
BULLET_RE = re.compile(r"^[\u2022\u25cf\u25aa\-\*\u2023\u2043]\s*")
METRIC_RE = re.compile(r"\d+%|\$\d+|\d+x\b|\d+\+|\d{2,}(?=\s*(users|customers|requests|records))", re.I)

SKILL_SEPARATORS_RE = re.compile(r"[,|;/•·]")

KNOWN_DEGREES = (
    "b.tech", "btech", "bachelor", "b.e", "be ", "b.sc", "bsc",
    "m.tech", "mtech", "master", "m.e", "me ", "m.sc", "msc",
    "mba", "phd", "ph.d", "diploma", "associate",
)

CERT_KEYWORDS_RE = re.compile(
    r"\b(AWS|Azure|GCP|PMP|CSM|CSPO|Scrum|ITIL|CISSP|CISA|CKA|CKAD|"
    r"Certified|Certification|Six\s*Sigma)\b", re.I
)


def _split_lines(text: str) -> list[str]:
    return [ln.rstrip() for ln in text.splitlines()]


def _detect_sections(lines: list[str]) -> dict[str, tuple[int, int]]:
    """Returns {section_name: (start_line_idx, end_line_idx)}."""
    headers: list[tuple[int, str]] = []
    for i, line in enumerate(lines):
        stripped = line.strip().lower().rstrip(":")
        if not stripped or len(stripped) > 40:
            continue
        for section, pattern in SECTION_PATTERNS.items():
            if re.match(pattern, stripped, re.I):
                headers.append((i, section))
                break

    sections: dict[str, tuple[int, int]] = {}
    for idx, (line_no, name) in enumerate(headers):
        end = headers[idx + 1][0] if idx + 1 < len(headers) else len(lines)
        sections[name] = (line_no + 1, end)
    return sections


def _extract_name(lines: list[str]) -> str:
    for line in lines[:5]:
        stripped = line.strip()
        if not stripped:
            continue
        if EMAIL_RE.search(stripped) or PHONE_RE.search(stripped):
            continue
        words = stripped.split()
        if 1 <= len(words) <= 5 and not any(ch.isdigit() for ch in stripped):
            return stripped
    return ""


def _extract_skills(block_text: str) -> list[str]:
    if not block_text:
        return []
    raw = SKILL_SEPARATORS_RE.split(block_text)
    skills = []
    for item in raw:
        cleaned = BULLET_RE.sub("", item).strip(" .\n\t")
        if cleaned and 1 < len(cleaned) <= 40:
            skills.append(cleaned)
    # dedupe, preserve order
    seen = set()
    out = []
    for s in skills:
        key = s.lower()
        if key not in seen:
            seen.add(key)
            out.append(s)
    return out


def _split_title_company(text: str) -> tuple[str, str]:
    text = text.strip(" -–—|,")
    if "," in text:
        title, company = text.split(",", 1)
        return title.strip(), company.strip()
    at_match = re.split(r"\s+at\s+", text, flags=re.I, maxsplit=1)
    if len(at_match) == 2:
        return at_match[0].strip(), at_match[1].strip()
    return text, ""


def _parse_experience_block(block_text: str) -> list[ExperienceEntry]:
    """
    Handles two common layouts:
      A) "Title, Company    Jan 2022 - Present"   (date on same line as header)
      B) "Title, Company"
         "Jan 2022 - Present"                      (date on its own next line)
    A new entry starts whenever a date range is found — whether inline
    with a header line or on its own line immediately after one.
    """
    entries: list[ExperienceEntry] = []
    current: ExperienceEntry | None = None
    pending_header: str | None = None  # header line seen, waiting to see if next line is a date

    def start_entry(header_text: str, date_match: re.Match) -> ExperienceEntry:
        before_date = header_text[: date_match.start()] if date_match.start() else header_text
        title, company = _split_title_company(before_date) if before_date.strip() else ("", "")
        return ExperienceEntry(
            title=title,
            company=company,
            start_date=date_match.group("start"),
            end_date=date_match.group("end"),
            duration_months=_estimate_months(date_match.group("start"), date_match.group("end")),
            raw_block=header_text,
        )

    for line in block_text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        is_bullet = bool(BULLET_RE.match(stripped))
        date_match = YEAR_RANGE_RE.search(stripped) if not is_bullet else None

        if date_match:
            inline_header_text = stripped[: date_match.start()].strip(" -–—|,")
            if inline_header_text:
                if current:
                    entries.append(current)
                current = start_entry(stripped, date_match)
                pending_header = None
            elif pending_header is not None:
                if current:
                    entries.append(current)
                title, company = _split_title_company(pending_header)
                current = ExperienceEntry(
                    title=title,
                    company=company,
                    start_date=date_match.group("start"),
                    end_date=date_match.group("end"),
                    duration_months=_estimate_months(date_match.group("start"), date_match.group("end")),
                    raw_block=f"{pending_header} | {stripped}",
                )
                pending_header = None
            else:
                if current:
                    entries.append(current)
                current = start_entry(stripped, date_match)
            continue

        if is_bullet:
            if current:
                current.bullets.append(BULLET_RE.sub("", stripped).strip())
            pending_header = None
            continue

        # Non-bullet, non-date line: either a header line (title/company) for
        # an upcoming date, or a stray company/location line for current entry.
        if pending_header is None and len(stripped) < 90:
            pending_header = stripped
        elif current and not current.company and len(stripped) < 60:
            current.company = stripped
            pending_header = None
        else:
            pending_header = stripped if len(stripped) < 90 else None

    if current:
        entries.append(current)
    return entries


def _estimate_months(start: str, end: str) -> int:
    def to_year(s: str) -> int | None:
        m = re.search(r"\d{4}", s)
        return int(m.group()) if m else None

    end_lower = end.lower().strip()
    end_year = 2026 if end_lower in ("present", "current") else to_year(end)
    start_year = to_year(start)
    if start_year and end_year and end_year >= start_year:
        return (end_year - start_year) * 12
    return 0


def _parse_education_block(block_text: str) -> list[EducationEntry]:
    entries = []
    for line in block_text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        lower = stripped.lower()
        if any(deg in lower for deg in KNOWN_DEGREES) or re.search(r"\d{4}", stripped):
            year_match = re.search(r"\d{4}", stripped)
            entries.append(
                EducationEntry(
                    degree=stripped,
                    institution="",
                    year=year_match.group() if year_match else "",
                )
            )
    return entries


def _parse_certifications(full_text: str, cert_block: str) -> list[CertificationEntry]:
    certs = []
    source = cert_block if cert_block.strip() else full_text
    for line in source.splitlines():
        stripped = BULLET_RE.sub("", line.strip())
        if not stripped:
            continue
        if cert_block.strip() or CERT_KEYWORDS_RE.search(stripped):
            year_match = re.search(r"\d{4}", stripped)
            certs.append(CertificationEntry(name=stripped, year=year_match.group() if year_match else ""))
    return certs


def _parse_projects(block_text: str) -> list[ProjectEntry]:
    projects = []
    current_name = ""
    current_desc_lines: list[str] = []
    current_tech: list[str] = []

    def flush():
        if current_name:
            projects.append(
                ProjectEntry(
                    name=current_name,
                    description=" ".join(current_desc_lines).strip(),
                    tech_stack=current_tech,
                )
            )

    TECH_LINE_RE = re.compile(r"^(?:tech(?:nologies)?|stack|tools)\s*[:\-]", re.I)

    for line in block_text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        is_bullet = bool(BULLET_RE.match(stripped))
        is_tech_line = bool(TECH_LINE_RE.match(stripped))

        if not is_bullet and not is_tech_line and len(stripped) < 80 and not stripped.endswith("."):
            flush()
            current_name = stripped
            current_desc_lines, current_tech = [], []
        else:
            text = BULLET_RE.sub("", stripped)
            tech_match = TECH_LINE_RE.match(text) and re.search(
                r"(?:tech(?:nologies)?|stack|tools)\s*[:\-]\s*(.+)", text, re.I
            )
            if tech_match:
                current_tech.extend(_extract_skills(tech_match.group(1)))
            else:
                current_desc_lines.append(text)
    flush()
    return projects


def _parse_achievements(block_text: str) -> list[str]:
    out = []
    for line in block_text.splitlines():
        stripped = BULLET_RE.sub("", line.strip())
        if stripped:
            out.append(stripped)
    return out


def parse_resume_text(raw_text: str) -> ResumeJSON:
    """Main entry point: raw extracted text → ResumeJSON."""
    lines = _split_lines(raw_text)
    sections = _detect_sections(lines)
    detected_names = list(sections.keys())

    def block(name: str) -> str:
        if name not in sections:
            return ""
        start, end = sections[name]
        return "\n".join(lines[start:end])

    full_text = raw_text

    email_match = EMAIL_RE.search(full_text)
    phone_match = PHONE_RE.search(full_text)
    linkedin_match = LINKEDIN_RE.search(full_text)
    github_match = GITHUB_RE.search(full_text)

    portfolio_url = ""
    for url in URL_RE.findall(full_text):
        if "linkedin.com" not in url and "github.com" not in url:
            portfolio_url = url
            break

    experience_entries = _parse_experience_block(block("experience"))
    total_months = sum(e.duration_months for e in experience_entries)

    summary_block = block("summary").strip()

    resume = ResumeJSON(
        name=_extract_name(lines),
        email=email_match.group() if email_match else "",
        phone=phone_match.group().strip() if phone_match else "",
        linkedin=linkedin_match.group() if linkedin_match else "",
        github=github_match.group() if github_match else "",
        portfolio_url=portfolio_url,
        experience_years=round(total_months / 12, 1),
        skills=_extract_skills(block("skills")),
        education=_parse_education_block(block("education")),
        certifications=_parse_certifications(full_text, block("certifications")),
        projects=_parse_projects(block("projects")),
        experience=experience_entries,
        achievements=_parse_achievements(block("achievements")),
        summary_text=summary_block,
        sections_detected=detected_names,
    )
    return resume

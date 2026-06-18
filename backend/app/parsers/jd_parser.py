"""
Converts pasted Job Description text into structured JDJSON.
Same philosophy as resume_parser.py: heuristic/regex, zero AI cost.
"""
import re

from app.schemas.job_description import JDJSON

REQUIRED_HEADER_RE = re.compile(
    r"(required|must.have|mandatory|essential)\s+(skills|qualifications)", re.I
)
PREFERRED_HEADER_RE = re.compile(
    r"(preferred|nice.to.have|good.to.have|bonus|desirable)\s+(skills|qualifications)?", re.I
)
ANY_HEADER_RE = re.compile(
    r"^(required|must.have|mandatory|essential|preferred|nice.to.have|good.to.have|"
    r"bonus|desirable|certifications?|responsibilities|qualifications|about|company)\b",
    re.I,
)
EXPERIENCE_RE = re.compile(
    r"(\d+)\s*\+?\s*(?:to|-)?\s*(\d+)?\s*\+?\s*years?\s+(?:of\s+)?experience", re.I
)
DOMAIN_KEYWORDS = (
    "fintech", "healthcare", "e-commerce", "ecommerce", "banking", "insurance",
    "telecom", "retail", "logistics", "saas", "edtech", "gaming", "manufacturing",
    "automotive", "government", "public sector", "energy", "media",
)
SENIORITY_KEYWORDS = (
    "intern", "junior", "associate", "mid-level", "senior", "lead", "principal",
    "staff", "manager", "director", "vp", "head of", "architect",
)
CERT_KEYWORDS_RE = re.compile(
    r"\b(AWS|Azure|GCP|PMP|CSM|CSPO|ITIL|CISSP|CISA|CKA|CKAD|Six\s*Sigma)\s*"
    r"(?:Certified\s+[A-Za-z\s\-]{0,40}|Certification[A-Za-z\s\-]{0,40})?",
    re.I,
)
SKILL_SEPARATORS_RE = re.compile(r"[,;|•·\n]")
BULLET_RE = re.compile(r"^[\u2022\u25cf\u25aa\-\*\u2023\u2043]\s*")

STOPWORDS = {
    "and", "or", "the", "a", "an", "with", "for", "to", "of", "in", "on",
    "experience", "knowledge", "ability", "strong", "excellent", "good",
}

HEADER_FRAGMENTS = {
    "preferred skills", "required skills", "certifications", "qualifications",
}


def _clean_items(text: str) -> list[str]:
    raw = SKILL_SEPARATORS_RE.split(text)
    items = []
    seen = set()
    for item in raw:
        cleaned = BULLET_RE.sub("", item).strip(" .\t")
        if not cleaned or len(cleaned) <= 1 or len(cleaned) > 50:
            continue
        if ANY_HEADER_RE.match(cleaned) or cleaned.rstrip(":").lower() in HEADER_FRAGMENTS:
            continue
        key = cleaned.lower()
        if key not in seen:
            seen.add(key)
            items.append(cleaned)
    return items


def _extract_section(text: str, header_re: re.Pattern, max_lines: int = 15) -> str:
    """
    Returns the lines following a matched header, stopping early if another
    recognized section header appears first. This prevents bleed-through
    between adjacent sections (e.g. Required Skills swallowing Preferred
    Skills or Certifications that immediately follow it).
    """
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if header_re.search(line):
            collected = []
            for j in range(i + 1, min(i + 1 + max_lines, len(lines))):
                next_line = lines[j].strip()
                if next_line and ANY_HEADER_RE.match(next_line) and not BULLET_RE.match(next_line):
                    break
                collected.append(lines[j])
            return "\n".join(collected)
    return ""


def _extract_certifications(text: str) -> list[str]:
    """
    Prefers an explicit 'Certifications: X, Y' line (parsed as a phrase
    list) over a raw keyword scan, which previously fragmented phrases
    like 'AWS Certified Solutions Architect' into separate single words.
    """
    for line in text.splitlines():
        inline_match = re.match(r"^certifications?\s*[:\-]\s*(.+)$", line.strip(), re.I)
        if inline_match:
            return _clean_items(inline_match.group(1))

    found, seen = [], set()
    for m in CERT_KEYWORDS_RE.finditer(text):
        phrase = re.sub(r"\s+", " ", m.group(0)).strip()
        key = phrase.lower()
        if key not in seen:
            seen.add(key)
            found.append(phrase)
    return found


def _extract_role_title(text: str) -> str:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    for line in lines[:3]:
        if 3 <= len(line) <= 80 and not line.lower().startswith(("about", "we are", "company")):
            return line
    return ""


def _extract_keywords(text: str, top_n: int = 25) -> list[str]:
    words = re.findall(r"[A-Za-z][A-Za-z+\-#.]{2,}", text)
    freq: dict[str, int] = {}
    for w in words:
        wl = w.lower()
        if wl in STOPWORDS or len(wl) < 3:
            continue
        freq[wl] = freq.get(wl, 0) + 1
    ranked = sorted(freq.items(), key=lambda kv: -kv[1])
    return [w for w, _ in ranked[:top_n]]


def parse_jd_text(raw_text: str) -> JDJSON:
    required_block = _extract_section(raw_text, REQUIRED_HEADER_RE)
    preferred_block = _extract_section(raw_text, PREFERRED_HEADER_RE)

    required_skills = _clean_items(required_block) if required_block else []
    preferred_skills = _clean_items(preferred_block) if preferred_block else []

    # fallback: if no explicit headers found, treat all bullet lines as required
    if not required_skills and not preferred_skills:
        bullet_lines = [
            BULLET_RE.sub("", raw_line.strip())
            for raw_line in raw_text.splitlines()
            if BULLET_RE.match(raw_line.strip())
        ]
        required_skills = _clean_items("\n".join(bullet_lines))[:30]

    exp_match = EXPERIENCE_RE.search(raw_text)
    experience_required = float(exp_match.group(1)) if exp_match else 0

    domain = next((d for d in DOMAIN_KEYWORDS if d in raw_text.lower()), "")
    seniority = next((s for s in SENIORITY_KEYWORDS if s in raw_text.lower()), "")
    certifications = _extract_certifications(raw_text)

    return JDJSON(
        required_skills=required_skills,
        preferred_skills=preferred_skills,
        experience_required=experience_required,
        certifications=certifications,
        domain=domain,
        role_title=_extract_role_title(raw_text),
        seniority_level=seniority,
        keywords=_extract_keywords(raw_text),
    )

"""
Pure deterministic rule engine. Computes every numeric score and every
gap/match list from structured JSON ONLY — no AI call happens here or
before this. This guarantees: (1) scores are explainable and reproducible,
(2) the AI layer only ever receives compact, already-computed signal
instead of raw resume content, which is the actual token-saving mechanism.
"""
import re

from app.schemas.job_description import JDJSON
from app.schemas.resume import ResumeJSON
from app.schemas.rule_engine import GapAnalysis, MatchScores, RuleEngineResult, RuleEngineScores

REQUIRED_SECTIONS = ("summary", "experience", "education", "skills", "projects", "certifications")
ACTION_VERBS_RE = re.compile(
    r"\b(led|built|designed|developed|implemented|optimized|automated|reduced|increased|"
    r"improved|launched|managed|created|architected|migrated|delivered|deployed|scaled|"
    r"streamlined|negotiated|spearheaded|mentored|drove)\b",
    re.I,
)
METRIC_RE = re.compile(r"\d+%|\$\s?\d+[kmb]?\b|\b\d+x\b|\b\d{2,}\+?\b", re.I)
GENERIC_PHRASES_RE = re.compile(
    r"\b(responsible for|worked on|involved in|helped with|various tasks|"
    r"day.to.day activities|duties included)\b",
    re.I,
)


def _clamp(value: float, lo: float = 0, hi: float = 100) -> float:
    return max(lo, min(hi, value))


def _score_ats(resume: ResumeJSON) -> float:
    score = 100.0
    if not resume.email:
        score -= 20
    if not resume.phone:
        score -= 10
    if not resume.skills:
        score -= 25
    if not resume.experience:
        score -= 25
    if len(resume.sections_detected) < 4:
        score -= 15
    return _clamp(score)


def _score_content(resume: ResumeJSON) -> float:
    all_bullets = [b for e in resume.experience for b in e.bullets] + resume.achievements
    if not all_bullets:
        return 30.0
    action_hits = sum(1 for b in all_bullets if ACTION_VERBS_RE.search(b))
    generic_hits = sum(1 for b in all_bullets if GENERIC_PHRASES_RE.search(b))
    ratio = action_hits / len(all_bullets)
    penalty = (generic_hits / len(all_bullets)) * 40
    return _clamp(40 + ratio * 60 - penalty)


def _score_formatting(resume: ResumeJSON) -> float:
    score = 100.0
    if not resume.sections_detected:
        score -= 40
    missing = [s for s in REQUIRED_SECTIONS if s not in resume.sections_detected]
    score -= len(missing) * 8
    if not resume.name:
        score -= 10
    return _clamp(score)


def _score_impact(resume: ResumeJSON) -> float:
    all_bullets = [b for e in resume.experience for b in e.bullets] + resume.achievements
    if not all_bullets:
        return 20.0
    metric_hits = sum(1 for b in all_bullets if METRIC_RE.search(b))
    ratio = metric_hits / len(all_bullets)
    return _clamp(20 + ratio * 80)


def _score_projects(resume: ResumeJSON) -> float:
    if not resume.projects:
        return 40.0
    described = sum(1 for p in resume.projects if len(p.description) > 30)
    with_tech = sum(1 for p in resume.projects if p.tech_stack)
    n = len(resume.projects)
    return _clamp(30 + (described / n) * 40 + (with_tech / n) * 30)


def _score_achievements(resume: ResumeJSON) -> float:
    if not resume.achievements:
        return 35.0
    metric_hits = sum(1 for a in resume.achievements if METRIC_RE.search(a))
    return _clamp(50 + (metric_hits / max(len(resume.achievements), 1)) * 50)


def _score_summary(resume: ResumeJSON) -> float:
    text = resume.summary_text.strip()
    if not text:
        return 0.0
    word_count = len(text.split())
    if word_count < 15:
        return 40.0
    if word_count > 120:
        return 60.0
    return 90.0


def _score_skills(resume: ResumeJSON) -> float:
    n = len(resume.skills)
    if n == 0:
        return 0.0
    if n < 5:
        return 40.0
    if n > 35:
        return 70.0  # likely keyword-stuffed
    return _clamp(60 + min(n, 20) * 1.5)


def _score_education(resume: ResumeJSON) -> float:
    if not resume.education:
        return 30.0
    return 90.0 if any(e.year for e in resume.education) else 70.0


def compute_resume_scores(resume: ResumeJSON) -> RuleEngineScores:
    scores = RuleEngineScores(
        ats_score=_score_ats(resume),
        content_score=_score_content(resume),
        formatting_score=_score_formatting(resume),
        impact_score=_score_impact(resume),
        project_score=_score_projects(resume),
        achievements_score=_score_achievements(resume),
        summary_score=_score_summary(resume),
        skills_score=_score_skills(resume),
        education_score=_score_education(resume),
    )
    weights = {
        "ats_score": 0.20,
        "content_score": 0.18,
        "formatting_score": 0.10,
        "impact_score": 0.18,
        "project_score": 0.10,
        "achievements_score": 0.08,
        "summary_score": 0.06,
        "skills_score": 0.06,
        "education_score": 0.04,
    }
    overall = sum(getattr(scores, k) * w for k, w in weights.items())
    scores.resume_score = round(_clamp(overall), 1)
    return scores


def compute_missing_sections(resume: ResumeJSON) -> list[str]:
    return [s for s in REQUIRED_SECTIONS if s not in resume.sections_detected]


def _normalize(skill: str) -> str:
    return re.sub(r"[^a-z0-9+#.]", "", skill.lower())


def compute_match(resume: ResumeJSON, jd: JDJSON) -> tuple[MatchScores, GapAnalysis]:
    resume_skills_norm = {_normalize(s): s for s in resume.skills}
    required_norm = {_normalize(s): s for s in jd.required_skills}
    preferred_norm = {_normalize(s): s for s in jd.preferred_skills}

    exact_matches = [
        orig for norm, orig in required_norm.items() if norm in resume_skills_norm
    ] + [orig for norm, orig in preferred_norm.items() if norm in resume_skills_norm]

    missing_skills = [orig for norm, orig in required_norm.items() if norm not in resume_skills_norm]

    skills_match_pct = (
        100.0 if not required_norm else
        len([n for n in required_norm if n in resume_skills_norm]) / len(required_norm) * 100
    )

    exp_match_pct = 100.0
    if jd.experience_required > 0:
        ratio = resume.experience_years / jd.experience_required
        exp_match_pct = _clamp(ratio * 100, 0, 100)

    resume_cert_names = {_normalize(c.name) for c in resume.certifications}
    jd_certs_norm = {_normalize(c): c for c in jd.certifications}
    missing_certs = [
        orig for norm, orig in jd_certs_norm.items()
        if not any(norm in rc or rc in norm for rc in resume_cert_names)
    ]
    cert_match_pct = (
        100.0 if not jd_certs_norm else
        (len(jd_certs_norm) - len(missing_certs)) / len(jd_certs_norm) * 100
    )

    resume_full_text = " ".join(
        resume.skills + resume.achievements +
        [b for e in resume.experience for b in e.bullets] +
        [resume.summary_text]
    ).lower()
    keyword_hits = [kw for kw in jd.keywords if kw in resume_full_text]
    missing_keywords = [kw for kw in jd.keywords if kw not in resume_full_text]
    keyword_match_pct = (
        100.0 if not jd.keywords else len(keyword_hits) / len(jd.keywords) * 100
    )

    ats_match_pct = _clamp(
        (skills_match_pct * 0.5) + (keyword_match_pct * 0.3) + (cert_match_pct * 0.2)
    )

    domain_match_pct = 70.0  # neutral default; refined by AI layer qualitatively
    if jd.domain and jd.domain.lower() in resume_full_text:
        domain_match_pct = 95.0
    elif jd.domain:
        domain_match_pct = 40.0

    overall = (
        skills_match_pct * 0.35
        + exp_match_pct * 0.20
        + keyword_match_pct * 0.15
        + cert_match_pct * 0.10
        + ats_match_pct * 0.10
        + domain_match_pct * 0.10
    )

    match_scores = MatchScores(
        overall_match_score=round(_clamp(overall), 1),
        skills_match_score=round(_clamp(skills_match_pct), 1),
        experience_match_score=round(_clamp(exp_match_pct), 1),
        keyword_match_score=round(_clamp(keyword_match_pct), 1),
        certification_match_score=round(_clamp(cert_match_pct), 1),
        ats_match_score=round(_clamp(ats_match_pct), 1),
        domain_match_score=round(_clamp(domain_match_pct), 1),
    )
    gaps = GapAnalysis(
        exact_skill_matches=exact_matches,
        missing_skills=missing_skills,
        missing_certifications=missing_certs,
        missing_keywords=missing_keywords[:20],
        missing_sections=compute_missing_sections(resume),
    )
    return match_scores, gaps


def run_rule_engine(resume: ResumeJSON, jd: JDJSON | None) -> RuleEngineResult:
    scores = compute_resume_scores(resume)

    if jd is None:
        return RuleEngineResult(
            mode="evaluation",
            scores=scores,
            match_scores=None,
            gaps=GapAnalysis(missing_sections=compute_missing_sections(resume)),
        )

    match_scores, gaps = compute_match(resume, jd)
    return RuleEngineResult(mode="matching", scores=scores, match_scores=match_scores, gaps=gaps)

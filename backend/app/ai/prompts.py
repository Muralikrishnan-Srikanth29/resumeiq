"""
Prompt templates. CRITICAL CONSTRAINT: every prompt here is built from
compact JSON summaries (ResumeJSON.to_compact_summary(), JDJSON.to_compact_summary(),
RuleEngineResult.to_ai_input()) — never from raw resume/JD text.

The output shape is enforced via Gemini's native response_schema (see
ai/schemas.py + gemini_service.py) rather than described in prose here.
That single change removes ~400-500 tokens of repeated schema-description
text from every call — the largest realistic lever available in this
prompt layer, larger than further squeezing the input JSON.
"""
import json

SYSTEM_INSTRUCTION = (
    "You are a senior technical recruiter and resume strategist. Evaluate ONLY "
    "the structured data given to you — never invent facts, employers, metrics, "
    "or skills not present in the input. If data is insufficient for a field, "
    "return an empty list/string rather than fabricating content."
)


def build_evaluation_prompt(resume_summary: dict, rule_output: dict) -> str:
    """Resume Evaluation Mode (no JD). Compact JSON in, schema-constrained JSON out."""
    return (
        f"RESUME:{json.dumps(resume_summary, separators=(',', ':'))}\n"
        f"SCORES(ground truth, do not recompute):{json.dumps(rule_output, separators=(',', ':'))}\n"
        "Evaluate this resume on its own merits. 3-6 strengths, 3-6 weaknesses grounded "
        "in the data. Recruiter's first 10-second impression + confidence score. "
        "2-5 line-level rewrites for the weakest bullets actually present in "
        "experience_summary (never fabricate bullets). Up to 4 interview questions "
        "per category based on actual skills/projects."
    )


def build_matching_prompt(resume_summary: dict, jd_summary: dict, rule_output: dict) -> str:
    """Job Matching Mode (JD provided). Compact JSON in, schema-constrained JSON out."""
    return (
        f"RESUME:{json.dumps(resume_summary, separators=(',', ':'))}\n"
        f"JD:{json.dumps(jd_summary, separators=(',', ':'))}\n"
        f"MATCH_RESULTS(ground truth, do not recompute):{json.dumps(rule_output, separators=(',', ':'))}\n"
        "Evaluate this candidate against this job. 3-6 strengths, 3-6 weaknesses relative "
        "to the JD. First impression + shortlist probability with reasoning that cites "
        "match_scores/gaps above — never contradict those numbers. 2-5 line-level rewrites "
        "aligning existing bullets to JD skills/keywords, using only bullets actually "
        "present in experience_summary. Up to 4 interview questions per category tailored "
        "to required_skills and domain."
    )


ROADMAP_SYSTEM_INSTRUCTION = (
    "You are a career coach specializing in role-transition planning."
)


def build_roadmap_prompt(resume_summary: dict, current_role: str, target_role: str) -> str:
    return (
        f"PROFILE:{json.dumps(resume_summary, separators=(',', ':'))}\n"
        f"CURRENT_ROLE:{current_role}\nTARGET_ROLE:{target_role}\n"
        "Based ONLY on the candidate's actual current skills/experience, identify "
        "realistic skill gaps and certification gaps for the target role, then build "
        "a 90-day roadmap."
    )

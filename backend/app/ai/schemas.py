"""
Native Gemini response schemas using the SDK's types.Schema. Passed via
GenerateContentConfig.response_schema instead of describing the JSON
shape in prose inside the prompt — this is what actually removes the
schema-hint tokens from every single call, and it's also more reliable
than asking the model to follow a textual spec.
"""
from google.genai import types

_STRING_LIST = types.Schema(type=types.Type.ARRAY, items=types.Schema(type=types.Type.STRING))

LINE_IMPROVEMENT_SCHEMA = types.Schema(
    type=types.Type.OBJECT,
    properties={
        "current": types.Schema(type=types.Type.STRING),
        "issue": types.Schema(type=types.Type.STRING),
        "improved": types.Schema(type=types.Type.STRING),
        "reason": types.Schema(type=types.Type.STRING),
    },
    required=["current", "issue", "improved", "reason"],
)

RECRUITER_EYE_VIEW_SCHEMA = types.Schema(
    type=types.Type.OBJECT,
    properties={
        "first_impression": types.Schema(type=types.Type.STRING),
        "confidence_score": types.Schema(type=types.Type.INTEGER),
        "rejection_reasons": _STRING_LIST,
        "positive_signals": _STRING_LIST,
    },
    required=["first_impression", "confidence_score", "rejection_reasons", "positive_signals"],
)

INTERVIEW_QUESTIONS_SCHEMA = types.Schema(
    type=types.Type.OBJECT,
    properties={
        "technical": _STRING_LIST,
        "behavioral": _STRING_LIST,
        "leadership": _STRING_LIST,
        "project_based": _STRING_LIST,
    },
    required=["technical", "behavioral", "leadership", "project_based"],
)

ANALYSIS_RESPONSE_SCHEMA = types.Schema(
    type=types.Type.OBJECT,
    properties={
        "strengths": _STRING_LIST,
        "weaknesses": _STRING_LIST,
        "recruiter_eye_view": RECRUITER_EYE_VIEW_SCHEMA,
        "line_improvements": types.Schema(type=types.Type.ARRAY, items=LINE_IMPROVEMENT_SCHEMA),
        "heat_map": types.Schema(
            type=types.Type.OBJECT,
            properties={
                "summary": types.Schema(type=types.Type.INTEGER),
                "experience": types.Schema(type=types.Type.INTEGER),
                "projects": types.Schema(type=types.Type.INTEGER),
                "skills": types.Schema(type=types.Type.INTEGER),
                "achievements": types.Schema(type=types.Type.INTEGER),
                "education": types.Schema(type=types.Type.INTEGER),
            },
        ),
        "shortlist_probability": types.Schema(
            type=types.Type.STRING, enum=["Low", "Medium", "High"]
        ),
        "shortlist_reasoning": types.Schema(type=types.Type.STRING),
        "interview_questions": INTERVIEW_QUESTIONS_SCHEMA,
    },
    required=[
        "strengths",
        "weaknesses",
        "recruiter_eye_view",
        "line_improvements",
        "heat_map",
        "shortlist_probability",
        "shortlist_reasoning",
        "interview_questions",
    ],
)

ROADMAP_RESPONSE_SCHEMA = types.Schema(
    type=types.Type.OBJECT,
    properties={
        "skill_gaps": _STRING_LIST,
        "certification_gaps": _STRING_LIST,
        "learning_path": types.Schema(
            type=types.Type.ARRAY,
            items=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "step": types.Schema(type=types.Type.STRING),
                    "resource_type": types.Schema(type=types.Type.STRING),
                    "priority": types.Schema(type=types.Type.STRING, enum=["High", "Medium", "Low"]),
                },
                required=["step", "resource_type", "priority"],
            ),
        ),
        "roadmap_90_day": types.Schema(
            type=types.Type.ARRAY,
            items=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "phase": types.Schema(type=types.Type.STRING),
                    "focus_areas": _STRING_LIST,
                    "milestones": _STRING_LIST,
                },
                required=["phase", "focus_areas", "milestones"],
            ),
        ),
    },
    required=["skill_gaps", "certification_gaps", "learning_path", "roadmap_90_day"],
)

from pydantic import BaseModel, Field


class LineImprovement(BaseModel):
    current: str
    issue: str
    improved: str
    reason: str


class RecruiterEyeView(BaseModel):
    first_impression: str = ""
    confidence_score: int = 0  # 0-100
    rejection_reasons: list[str] = Field(default_factory=list)
    positive_signals: list[str] = Field(default_factory=list)


class InterviewQuestionSet(BaseModel):
    technical: list[str] = Field(default_factory=list)
    behavioral: list[str] = Field(default_factory=list)
    leadership: list[str] = Field(default_factory=list)
    project_based: list[str] = Field(default_factory=list)


class AIAnalysisOutput(BaseModel):
    """Strict schema Gemini must return. Parsed straight from JSON response."""
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    recruiter_eye_view: RecruiterEyeView = Field(default_factory=RecruiterEyeView)
    line_improvements: list[LineImprovement] = Field(default_factory=list)
    heat_map: dict[str, int] = Field(default_factory=dict)
    shortlist_probability: str = "Medium"  # Low | Medium | High
    shortlist_reasoning: str = ""
    interview_questions: InterviewQuestionSet = Field(default_factory=InterviewQuestionSet)


# ---------------- API request/response models ----------------

class AnalyzeRequest(BaseModel):
    session_id: str
    resume_text: str | None = None       # used when input_method == paste
    jd_text: str | None = None           # optional JD, paste only


class AnalyzeResponse(BaseModel):
    analysis_id: str
    mode: str
    scores: dict
    match_scores: dict | None = None
    gaps: dict
    ai: AIAnalysisOutput
    tokens_used: int


class RoadmapRequest(BaseModel):
    session_id: str
    resume_id: str
    current_role: str
    target_role: str


class RoadmapResponse(BaseModel):
    roadmap_id: str
    skill_gaps: list[str]
    certification_gaps: list[str]
    learning_path: list[dict]
    roadmap_90_day: list[dict]

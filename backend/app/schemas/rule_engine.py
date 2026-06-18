from pydantic import BaseModel, Field


class RuleEngineScores(BaseModel):
    """Pure deterministic scores. Zero AI tokens spent computing these."""
    resume_score: float = 0
    ats_score: float = 0
    content_score: float = 0
    formatting_score: float = 0
    impact_score: float = 0
    project_score: float = 0
    achievements_score: float = 0
    summary_score: float = 0
    skills_score: float = 0
    education_score: float = 0


class MatchScores(BaseModel):
    overall_match_score: float = 0
    skills_match_score: float = 0
    experience_match_score: float = 0
    keyword_match_score: float = 0
    certification_match_score: float = 0
    ats_match_score: float = 0
    domain_match_score: float = 0


class GapAnalysis(BaseModel):
    exact_skill_matches: list[str] = Field(default_factory=list)
    missing_skills: list[str] = Field(default_factory=list)
    missing_certifications: list[str] = Field(default_factory=list)
    missing_keywords: list[str] = Field(default_factory=list)
    missing_sections: list[str] = Field(default_factory=list)


class RuleEngineResult(BaseModel):
    """
    Full deterministic output. This object — compacted — is the ONLY
    input besides the two compact JSON summaries that Gemini ever sees.
    """
    mode: str  # "evaluation" | "matching"
    scores: RuleEngineScores
    match_scores: MatchScores | None = None
    gaps: GapAnalysis

    def to_ai_input(self) -> dict:
        d = {
            "mode": self.mode,
            "scores": self.scores.model_dump(),
            "gaps": self.gaps.model_dump(),
        }
        if self.match_scores:
            d["match_scores"] = self.match_scores.model_dump()
        return d

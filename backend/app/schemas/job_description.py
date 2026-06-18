from pydantic import BaseModel, Field


class JDJSON(BaseModel):
    required_skills: list[str] = Field(default_factory=list)
    preferred_skills: list[str] = Field(default_factory=list)
    experience_required: float = 0
    certifications: list[str] = Field(default_factory=list)
    domain: str = ""
    role_title: str = ""
    seniority_level: str = ""
    keywords: list[str] = Field(default_factory=list)

    def to_compact_summary(self) -> dict:
        return {
            "required_skills": self.required_skills[:20],
            "preferred_skills": self.preferred_skills[:12],
            "experience_required": self.experience_required,
            "certifications": self.certifications[:6],
            "domain": self.domain,
            "role_title": self.role_title,
            "seniority_level": self.seniority_level,
        }

from pydantic import BaseModel, Field


class ExperienceEntry(BaseModel):
    title: str = ""
    company: str = ""
    start_date: str = ""
    end_date: str = ""
    duration_months: int = 0
    bullets: list[str] = Field(default_factory=list)
    raw_block: str = ""


class EducationEntry(BaseModel):
    degree: str = ""
    institution: str = ""
    year: str = ""
    gpa: str = ""


class ProjectEntry(BaseModel):
    name: str = ""
    description: str = ""
    tech_stack: list[str] = Field(default_factory=list)
    link: str = ""


class CertificationEntry(BaseModel):
    name: str = ""
    issuer: str = ""
    year: str = ""


class ResumeJSON(BaseModel):
    """
    Canonical structured representation of a resume.
    This — never the raw PDF — is what gets sent downstream to the
    rule engine and (in compact form) to Gemini.
    """
    name: str = ""
    email: str = ""
    phone: str = ""
    linkedin: str = ""
    github: str = ""
    portfolio_url: str = ""
    experience_years: float = 0
    skills: list[str] = Field(default_factory=list)
    education: list[EducationEntry] = Field(default_factory=list)
    certifications: list[CertificationEntry] = Field(default_factory=list)
    projects: list[ProjectEntry] = Field(default_factory=list)
    experience: list[ExperienceEntry] = Field(default_factory=list)
    achievements: list[str] = Field(default_factory=list)
    summary_text: str = ""
    sections_detected: list[str] = Field(default_factory=list)

    def to_compact_summary(self) -> dict:
        """
        Minimal payload for AI calls. Aggressively trims relative to the
        full resume: bullets are capped in count AND length, skills/projects
        are capped tighter, and zero-value fields are omitted. Combined with
        never sending raw resume/JD text or rule-engine recomputation
        instructions, this is what keeps the AI call cheap — the saving is
        real for longer resumes and JD-matching calls (where the alternative
        is sending both full documents) but modest-to-negative for very
        short resumes, where the JSON scaffolding itself has overhead. The
        rule engine (free) carries the analytical weight; this summary just
        gives the AI enough grounding to write qualitative commentary.
        """

        def trim_bullet(b: str, max_len: int = 110) -> str:
            return b if len(b) <= max_len else b[: max_len - 1].rstrip() + "…"

        return {
            "name": self.name,
            "experience_years": self.experience_years,
            "skills": self.skills[:25],
            "education": [f"{e.degree}" for e in self.education[:3]],
            "certifications": [c.name for c in self.certifications[:6]],
            "projects": [
                {"name": p.name, "tech": p.tech_stack[:6]} for p in self.projects[:4]
            ],
            "experience_summary": [
                {
                    "title": e.title,
                    "company": e.company,
                    "duration_months": e.duration_months,
                    "bullets": [trim_bullet(b) for b in e.bullets[:4]],
                }
                for e in self.experience[:5]
            ],
            "achievements": [trim_bullet(a) for a in self.achievements[:6]],
            "sections_detected": self.sections_detected,
            "has_summary": bool(self.summary_text.strip()),
        }

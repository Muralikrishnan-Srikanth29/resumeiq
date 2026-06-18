from app.parsers.resume_parser import parse_resume_text

SAMPLE_RESUME = """
Arjun Mehta
arjun.mehta@email.com | +91 98765 43210
linkedin.com/in/arjunmehta | github.com/arjunmehta

PROFESSIONAL SUMMARY
Software engineer with 4 years of experience building scalable backend systems.

EXPERIENCE
Senior Backend Engineer, TechCorp Solutions
Jan 2022 - Present
- Led migration of monolithic service to microservices, reducing deployment time by 60%
- Built automated regression test suite covering 300+ test cases

Backend Engineer, StartupXYZ
Jun 2020 - Dec 2021
- Worked on various tasks related to API development
- Responsible for maintaining legacy systems

EDUCATION
B.Tech in Computer Science, IIT Delhi, 2020

SKILLS
Python, FastAPI, PostgreSQL, Docker, Kubernetes, AWS, Redis

PROJECTS
Distributed Task Queue
Built a Redis-backed distributed task queue handling 10k jobs/minute.
Tech: Python, Redis, Celery

CERTIFICATIONS
AWS Certified Solutions Architect - Associate, 2023

ACHIEVEMENTS
Reduced infrastructure costs by 35% through right-sizing cloud resources
"""


def test_extracts_contact_info():
    resume = parse_resume_text(SAMPLE_RESUME)
    assert resume.name == "Arjun Mehta"
    assert resume.email == "arjun.mehta@email.com"
    assert "linkedin.com/in/arjunmehta" in resume.linkedin
    assert "github.com/arjunmehta" in resume.github


def test_detects_all_sections():
    resume = parse_resume_text(SAMPLE_RESUME)
    expected = {"summary", "experience", "education", "skills", "projects", "certifications", "achievements"}
    assert expected.issubset(set(resume.sections_detected))


def test_experience_entries_split_title_and_company_correctly():
    """Regression test: title/company must not swap or merge across two-line headers."""
    resume = parse_resume_text(SAMPLE_RESUME)
    assert len(resume.experience) == 2

    first = resume.experience[0]
    assert first.title == "Senior Backend Engineer"
    assert first.company == "TechCorp Solutions"
    assert len(first.bullets) == 2

    second = resume.experience[1]
    assert second.title == "Backend Engineer"
    assert second.company == "StartupXYZ"


def test_experience_duration_calculated():
    resume = parse_resume_text(SAMPLE_RESUME)
    # Jan 2022 - Present (treated as 2026) = 48 months
    assert resume.experience[0].duration_months == 48


def test_skills_extracted_and_deduped():
    resume = parse_resume_text(SAMPLE_RESUME)
    assert "Python" in resume.skills
    assert "Docker" in resume.skills
    assert len(resume.skills) == len(set(s.lower() for s in resume.skills))


def test_project_tech_line_does_not_become_separate_project():
    """Regression test: 'Tech: X, Y, Z' line must attach to the preceding
    project, not be parsed as a second project."""
    resume = parse_resume_text(SAMPLE_RESUME)
    assert len(resume.projects) == 1
    assert resume.projects[0].name == "Distributed Task Queue"
    assert "Python" in resume.projects[0].tech_stack
    assert "Celery" in resume.projects[0].tech_stack


def test_certifications_extracted():
    resume = parse_resume_text(SAMPLE_RESUME)
    assert len(resume.certifications) == 1
    assert "AWS Certified Solutions Architect" in resume.certifications[0].name


def test_achievements_extracted():
    resume = parse_resume_text(SAMPLE_RESUME)
    assert len(resume.achievements) == 1
    assert "35%" in resume.achievements[0]


def test_empty_resume_does_not_crash():
    resume = parse_resume_text("Just some random text with no structure at all.")
    assert resume.name == ""
    assert resume.skills == []
    assert resume.experience == []


def test_compact_summary_caps_apply():
    resume = parse_resume_text(SAMPLE_RESUME)
    summary = resume.to_compact_summary()
    assert len(summary["experience_summary"]) <= 5
    assert all(len(e["bullets"]) <= 4 for e in summary["experience_summary"])
    assert len(summary["skills"]) <= 25

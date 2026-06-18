from app.parsers.jd_parser import parse_jd_text
from app.parsers.resume_parser import parse_resume_text
from app.rules.engine import run_rule_engine

STRONG_RESUME = """
Arjun Mehta
arjun.mehta@email.com | +91 98765 43210
linkedin.com/in/arjunmehta | github.com/arjunmehta

PROFESSIONAL SUMMARY
Backend engineer with 5 years of experience designing distributed systems.

EXPERIENCE
Senior Backend Engineer, TechCorp Solutions
Jan 2022 - Present
- Led migration of monolithic service to microservices, reducing deployment time by 60%
- Architected event-driven pipeline processing 2M+ requests daily

Backend Engineer, StartupXYZ
Jun 2020 - Dec 2021
- Designed and implemented RESTful APIs for payment processing
- Optimized PostgreSQL queries reducing average query time by 70%

EDUCATION
B.Tech in Computer Science, IIT Delhi, 2019

SKILLS
Python, FastAPI, PostgreSQL, Docker, Kubernetes, AWS, Redis, Kafka

PROJECTS
Distributed Task Queue
Built a Redis-backed distributed task queue handling 10,000+ jobs per minute.
Tech: Python, Redis, Celery

CERTIFICATIONS
AWS Certified Solutions Architect - Associate, 2023

ACHIEVEMENTS
Reduced infrastructure costs by 35% through right-sizing cloud resources
"""

WEAK_RESUME = """
Priya Sharma
priya.sharma@email.com

EXPERIENCE
Intern, DevSoft Inc
Jun 2025 - Aug 2025
- Worked on various tasks
- Helped with bug fixes

SKILLS
Java, HTML, CSS
"""

SAMPLE_JD = """
Senior Backend Engineer

Required Skills:
- Python, FastAPI
- PostgreSQL, Redis
- Kubernetes, Docker

Preferred Skills:
- AWS, Kafka

Certifications: AWS Certified Solutions Architect

3+ years experience required.
"""


def test_strong_resume_scores_higher_than_weak_resume():
    strong = parse_resume_text(STRONG_RESUME)
    weak = parse_resume_text(WEAK_RESUME)

    strong_result = run_rule_engine(strong, None)
    weak_result = run_rule_engine(weak, None)

    assert strong_result.scores.resume_score > weak_result.scores.resume_score


def test_evaluation_mode_when_no_jd():
    resume = parse_resume_text(STRONG_RESUME)
    result = run_rule_engine(resume, None)
    assert result.mode == "evaluation"
    assert result.match_scores is None


def test_matching_mode_when_jd_provided():
    resume = parse_resume_text(STRONG_RESUME)
    jd = parse_jd_text(SAMPLE_JD)
    result = run_rule_engine(resume, jd)
    assert result.mode == "matching"
    assert result.match_scores is not None


def test_exact_skill_matches_detected():
    resume = parse_resume_text(STRONG_RESUME)
    jd = parse_jd_text(SAMPLE_JD)
    result = run_rule_engine(resume, jd)
    assert "Python" in result.gaps.exact_skill_matches
    assert "PostgreSQL" in result.gaps.exact_skill_matches


def test_missing_skills_detected_for_weak_resume():
    weak = parse_resume_text(WEAK_RESUME)
    jd = parse_jd_text(SAMPLE_JD)
    result = run_rule_engine(weak, jd)
    assert len(result.gaps.missing_skills) > 0


def test_scores_are_bounded_0_to_100():
    resume = parse_resume_text(STRONG_RESUME)
    jd = parse_jd_text(SAMPLE_JD)
    result = run_rule_engine(resume, jd)

    for value in result.scores.model_dump().values():
        assert 0 <= value <= 100
    for value in result.match_scores.model_dump().values():
        assert 0 <= value <= 100


def test_missing_sections_detected():
    weak = parse_resume_text(WEAK_RESUME)
    result = run_rule_engine(weak, None)
    assert "projects" in result.gaps.missing_sections
    assert "certifications" in result.gaps.missing_sections
    assert "education" in result.gaps.missing_sections


def test_certification_match_when_present():
    resume = parse_resume_text(STRONG_RESUME)
    jd = parse_jd_text(SAMPLE_JD)
    result = run_rule_engine(resume, jd)
    assert result.match_scores.certification_match_score == 100.0
    assert result.gaps.missing_certifications == []

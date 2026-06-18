from app.parsers.jd_parser import parse_jd_text

SAMPLE_JD = """
Senior Backend Engineer - Fintech Domain

Required Skills:
- Python, FastAPI or Django
- PostgreSQL, Redis
- Kubernetes, Docker
- 3+ years experience

Preferred Skills:
- AWS, Kafka
- Microservices architecture experience

Certifications: AWS Certified Solutions Architect

We are looking for a senior engineer with strong fintech domain experience.
"""


def test_required_and_preferred_skills_do_not_bleed_into_each_other():
    """Regression test: section boundary detection must stop at the next header."""
    jd = parse_jd_text(SAMPLE_JD)
    assert "AWS" not in jd.required_skills
    assert "Kafka" not in jd.required_skills
    assert "AWS" in jd.preferred_skills
    assert "Kafka" in jd.preferred_skills


def test_certifications_not_fragmented():
    """Regression test: 'AWS Certified Solutions Architect' must stay one
    phrase, not get split into ['AWS', 'Certified']."""
    jd = parse_jd_text(SAMPLE_JD)
    assert jd.certifications == ["AWS Certified Solutions Architect"]


def test_experience_required_extracted():
    jd = parse_jd_text(SAMPLE_JD)
    assert jd.experience_required == 3.0


def test_domain_detected():
    jd = parse_jd_text(SAMPLE_JD)
    assert jd.domain == "fintech"


def test_header_fragments_excluded_from_skills():
    jd = parse_jd_text(SAMPLE_JD)
    for skill in jd.required_skills + jd.preferred_skills:
        assert "preferred skills" not in skill.lower()
        assert "certifications" not in skill.lower()


def test_no_explicit_headers_falls_back_to_bullets():
    jd_text = """
    Looking for a developer with the following:
    - Strong Python skills
    - Experience with REST APIs
    - Good communication
    """
    jd = parse_jd_text(jd_text)
    assert len(jd.required_skills) > 0


def test_empty_jd_does_not_crash():
    jd = parse_jd_text("")
    assert jd.required_skills == []
    assert jd.experience_required == 0

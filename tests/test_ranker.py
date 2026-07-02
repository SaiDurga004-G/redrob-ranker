"""
Lightweight sanity tests -- run with: python -m pytest tests/
(or just `python tests/test_ranker.py`, no pytest required).

These aren't exhaustive; they check the properties that matter most for
Stage 1/3 of the challenge: format validity, honeypot exclusion, and that
the keyword-stuffer trap (title irrelevant to the role, skills list padded
with AI buzzwords) doesn't win.
"""

import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.features import extract_features
from src.integrity import check_honeypot
from src.scoring import compute_score

SAMPLE_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "sample_candidates.json"
)


def _load_samples():
    # Falls back to the uploads path used in the dev container; adjust if
    # you've copied sample_candidates.json into the repo instead.
    for path in (
        SAMPLE_PATH,
        "/mnt/user-data/uploads/sample_candidates.json",
        "sample_candidates.json",
    ):
        if os.path.exists(path):
            with open(path) as f:
                return json.load(f)
    raise FileNotFoundError("sample_candidates.json not found")


def test_honeypot_excludes_impossible_profile():
    fake = {
        "candidate_id": "CAND_9999999",
        "profile": {
            "anonymized_name": "Test", "headline": "x", "summary": "x",
            "location": "Pune, India", "country": "India",
            "years_of_experience": 15.0, "current_title": "ML Engineer",
            "current_company": "Sarvam AI", "current_company_size": "51-200",
            "current_industry": "AI/ML",
        },
        "career_history": [{
            "company": "Sarvam AI", "title": "ML Engineer",
            "start_date": "2024-01-01", "end_date": None,
            "duration_months": 12, "is_current": True,
            "industry": "AI/ML", "company_size": "51-200",
            "description": "shipped production retrieval systems",
        }],
        "education": [],
        "skills": [
            {"name": "Python", "proficiency": "expert", "endorsements": 0, "duration_months": 0},
            {"name": "PyTorch", "proficiency": "expert", "endorsements": 0, "duration_months": 0},
            {"name": "FAISS", "proficiency": "expert", "endorsements": 0, "duration_months": 0},
        ],
        "redrob_signals": {
            "profile_completeness_score": 90, "signup_date": "2025-01-01",
            "last_active_date": "2026-06-01", "open_to_work_flag": True,
            "profile_views_received_30d": 10, "applications_submitted_30d": 1,
            "recruiter_response_rate": 0.9, "avg_response_time_hours": 2,
            "skill_assessment_scores": {}, "connection_count": 100,
            "endorsements_received": 10, "notice_period_days": 15,
            "expected_salary_range_inr_lpa": {"min": 30, "max": 40},
            "preferred_work_mode": "hybrid", "willing_to_relocate": True,
            "github_activity_score": 80, "search_appearance_30d": 5,
            "saved_by_recruiters_30d": 2, "interview_completion_rate": 0.9,
            "offer_acceptance_rate": -1, "verified_email": True,
            "verified_phone": True, "linkedin_connected": True,
        },
    }
    # 15y claimed vs. only 12 months of career_history -> should be flagged.
    features = extract_features(fake)
    hp = check_honeypot(features)
    assert hp["is_honeypot"], "expected experience-timeline mismatch to be flagged"
    result = compute_score(features, hp)
    assert result["excluded"]
    assert result["final_score"] == 0.0


def test_keyword_stuffer_scores_below_real_ml_titles():
    # HR Manager with a padded AI skills list should not outrank a genuine
    # ML Engineer with fewer, better-evidenced skills.
    stuffer = {
        "candidate_id": "CAND_9999998",
        "profile": {
            "anonymized_name": "Stuffer", "headline": "HR pro",
            "summary": "HR generalist", "location": "Pune, India",
            "country": "India", "years_of_experience": 6.0,
            "current_title": "HR Manager", "current_company": "TCS",
            "current_company_size": "10001+", "current_industry": "IT Services",
        },
        "career_history": [{
            "company": "TCS", "title": "HR Manager", "start_date": "2020-01-01",
            "end_date": None, "duration_months": 72, "is_current": True,
            "industry": "IT Services", "company_size": "10001+",
            "description": "manages hiring pipelines",
        }],
        "education": [],
        "skills": [
            {"name": n, "proficiency": "expert", "endorsements": 0, "duration_months": 0}
            for n in ["RAG", "LLMs", "Embeddings", "Vector Search", "Pinecone",
                      "FAISS", "LangChain", "Prompt Engineering", "NLP"]
        ],
        "redrob_signals": {
            "profile_completeness_score": 80, "signup_date": "2025-01-01",
            "last_active_date": "2026-06-20", "open_to_work_flag": True,
            "profile_views_received_30d": 5, "applications_submitted_30d": 1,
            "recruiter_response_rate": 0.7, "avg_response_time_hours": 5,
            "skill_assessment_scores": {}, "connection_count": 50,
            "endorsements_received": 2, "notice_period_days": 30,
            "expected_salary_range_inr_lpa": {"min": 20, "max": 25},
            "preferred_work_mode": "hybrid", "willing_to_relocate": True,
            "github_activity_score": -1, "search_appearance_30d": 2,
            "saved_by_recruiters_30d": 0, "interview_completion_rate": 0.5,
            "offer_acceptance_rate": -1, "verified_email": True,
            "verified_phone": True, "linkedin_connected": True,
        },
    }
    genuine = {
        "candidate_id": "CAND_9999997",
        "profile": {
            "anonymized_name": "Genuine", "headline": "ML Engineer",
            "summary": "Built retrieval systems in production",
            "location": "Pune, India", "country": "India",
            "years_of_experience": 6.0, "current_title": "ML Engineer",
            "current_company": "Sarvam AI", "current_company_size": "51-200",
            "current_industry": "AI/ML",
        },
        "career_history": [{
            "company": "Sarvam AI", "title": "ML Engineer",
            "start_date": "2020-01-01", "end_date": None,
            "duration_months": 72, "is_current": True, "industry": "AI/ML",
            "company_size": "51-200",
            "description": "Shipped a production semantic search and "
                            "ranking system serving real users at scale, "
                            "including embedding index refresh and latency "
                            "optimization.",
        }],
        "education": [],
        "skills": [
            {"name": "Python", "proficiency": "advanced", "endorsements": 10, "duration_months": 60},
            {"name": "Embeddings", "proficiency": "advanced", "endorsements": 8, "duration_months": 48},
            {"name": "FAISS", "proficiency": "advanced", "endorsements": 5, "duration_months": 36},
        ],
        "redrob_signals": {
            "profile_completeness_score": 90, "signup_date": "2025-01-01",
            "last_active_date": "2026-06-25", "open_to_work_flag": True,
            "profile_views_received_30d": 5, "applications_submitted_30d": 1,
            "recruiter_response_rate": 0.8, "avg_response_time_hours": 4,
            "skill_assessment_scores": {}, "connection_count": 50,
            "endorsements_received": 20, "notice_period_days": 20,
            "expected_salary_range_inr_lpa": {"min": 30, "max": 40},
            "preferred_work_mode": "hybrid", "willing_to_relocate": True,
            "github_activity_score": 60, "search_appearance_30d": 4,
            "saved_by_recruiters_30d": 1, "interview_completion_rate": 0.8,
            "offer_acceptance_rate": -1, "verified_email": True,
            "verified_phone": True, "linkedin_connected": True,
        },
    }

    f1, f2 = extract_features(stuffer), extract_features(genuine)
    r1 = compute_score(f1, check_honeypot(f1))
    r2 = compute_score(f2, check_honeypot(f2))
    assert r2["final_score"] > r1["final_score"], (
        f"genuine ML engineer ({r2['final_score']}) should outrank the "
        f"keyword-stuffed HR Manager ({r1['final_score']})"
    )


def test_all_samples_score_without_error():
    samples = _load_samples()
    for cand in samples:
        features = extract_features(cand)
        hp = check_honeypot(features)
        result = compute_score(features, hp)
        assert 0.0 <= result["final_score"] <= 1.0


if __name__ == "__main__":
    test_honeypot_excludes_impossible_profile()
    test_keyword_stuffer_scores_below_real_ml_titles()
    test_all_samples_score_without_error()
    print("All tests passed.")

"""Turn a raw candidate JSON record into a flat, easy-to-score feature dict."""

import datetime
from . import constants as K


def _parse_date(s):
    if not s:
        return None
    try:
        return datetime.date.fromisoformat(s)
    except ValueError:
        return None


def extract_features(cand: dict) -> dict:
    profile = cand.get("profile", {})
    career = cand.get("career_history", []) or []
    education = cand.get("education", []) or []
    skills = cand.get("skills", []) or []
    signals = cand.get("redrob_signals", {}) or {}

    current_title = (profile.get("current_title") or "").strip()
    all_titles = [current_title] + [c.get("title", "") for c in career]
    all_titles_l = [t.lower().strip() for t in all_titles if t]

    all_companies = [profile.get("current_company", "")] + [
        c.get("company", "") for c in career
    ]
    all_companies_l = [c.lower().strip() for c in all_companies if c]

    all_industries = [profile.get("current_industry", "")] + [
        c.get("industry", "") for c in career
    ]

    # Concatenated free text used for phrase/keyword search.
    text_parts = [profile.get("headline", ""), profile.get("summary", "")]
    for c in career:
        text_parts.append(c.get("description", ""))
    concat_text = " \n ".join(t for t in text_parts if t).lower()

    total_career_months = sum(int(c.get("duration_months") or 0) for c in career)

    location = (profile.get("location") or "")
    location_l = location.lower()
    country = (profile.get("country") or "").strip()

    # Parsed career intervals, sorted by start date -- used for both
    # honeypot / integrity checks and title-chasing detection.
    intervals = []
    for c in career:
        s = _parse_date(c.get("start_date"))
        e = _parse_date(c.get("end_date")) or K.TODAY
        intervals.append(
            {
                "start": s,
                "end": e,
                "company": c.get("company", ""),
                "title": c.get("title", ""),
                "duration_months": int(c.get("duration_months") or 0),
                "raw_end": c.get("end_date"),
            }
        )
    intervals.sort(key=lambda x: x["start"] or K.TODAY)

    last_active = _parse_date(signals.get("last_active_date"))
    days_since_active = (K.TODAY - last_active).days if last_active else 9999

    return {
        "candidate_id": cand.get("candidate_id"),
        "anonymized_name": profile.get("anonymized_name", ""),
        "current_title": current_title,
        "current_title_l": current_title.lower(),
        "all_titles_l": all_titles_l,
        "current_company": profile.get("current_company", ""),
        "current_company_l": (profile.get("current_company") or "").lower(),
        "all_companies_l": all_companies_l,
        "all_industries": all_industries,
        "current_industry": profile.get("current_industry", ""),
        "yoe": float(profile.get("years_of_experience") or 0),
        "location": location,
        "location_l": location_l,
        "country": country,
        "concat_text": concat_text,
        "skills": skills,
        "education": education,
        "career_history": career,
        "career_intervals": intervals,
        "total_career_months": total_career_months,
        "signals": signals,
        "days_since_active": days_since_active,
        "notice_period_days": signals.get("notice_period_days"),
        "willing_to_relocate": bool(signals.get("willing_to_relocate")),
        "open_to_work_flag": bool(signals.get("open_to_work_flag")),
    }

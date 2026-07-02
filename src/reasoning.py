"""
Generate the 1-2 sentence `reasoning` column.

Every sentence is built from facts actually pulled off the candidate's
record (title, company, years of experience, matched skills, signal
values) -- nothing is invented. Several sentence templates are used and
selected deterministically from a hash of candidate_id, and any real
weak point found during scoring is surfaced as an honest concern, so
reasoning strings vary and aren't purely congratulatory templates.
"""

import hashlib


def _pick(seed_str, options):
    h = int(hashlib.md5(seed_str.encode()).hexdigest(), 16)
    return options[h % len(options)]


def _top_skills(detail, n=3):
    hits = detail.get("core_skill_hits") or []
    # de-dup while preserving order
    seen, out = set(), []
    for h in hits:
        if h not in seen:
            out.append(h)
            seen.add(h)
        if len(out) >= n:
            break
    return out


def _find_concern(features, score_result):
    detail = score_result["detail"]
    concerns = []

    if detail.get("consulting_only"):
        concerns.append("entire career so far has been at IT-services/consulting firms")
    if detail.get("pure_research_only"):
        concerns.append("profile reads as research-only with no clear production deployment evidence")
    if detail.get("cv_speech_only"):
        concerns.append("background is CV/speech-focused with no NLP/IR signal")
    if detail.get("title_chasing"):
        concerns.append("career shows several short (<20mo) stints across employers")

    notice = detail.get("notice_period_days")
    if notice is not None and notice > 60:
        concerns.append(f"long notice period ({notice} days)")

    if detail.get("days_inactive", 0) > 150:
        concerns.append(f"hasn't been active on Redrob in {detail['days_inactive']} days")

    rr = detail.get("response_rate")
    if rr is not None and rr < 0.3:
        concerns.append(f"low recruiter response rate ({rr:.0%})")

    loc_fit = score_result["components"]["location_fit"]
    if loc_fit <= 0.35:
        concerns.append("location/relocation fit is uncertain for Pune/Noida")

    if not detail.get("core_skill_hits"):
        concerns.append("no directly-evidenced embeddings/retrieval/vector-DB skills on record")

    if score_result["components"]["experience_fit"] < 0.7:
        concerns.append(f"{features['yoe']:.1f} years experience sits outside the 5-9y band")

    return concerns


POSITIVE_TEMPLATES = [
    "{title} at {company} with {yoe:.1f} years experience{skills_clause}{prod_clause}.",
    "{yoe:.1f}y {title} ({company}){skills_clause}{prod_clause}.",
    "Currently {title} at {company}, {yoe:.1f}y experience{skills_clause}{prod_clause}.",
]

WITH_CONCERN_TEMPLATES = [
    "{title} at {company}, {yoe:.1f}y experience{skills_clause}{prod_clause}; concern: {concern}.",
    "{yoe:.1f}y {title} ({company}){skills_clause}{prod_clause} -- but {concern}.",
    "Solid on paper as {title} at {company} ({yoe:.1f}y){skills_clause}, though {concern}.",
]

FILLER_TEMPLATES = [
    "{title} at {company}, {yoe:.1f}y experience; adjacent fit at best{skills_clause}; {concern}.",
    "Included as lower-confidence filler: {title} ({yoe:.1f}y){skills_clause}, {concern}.",
]


def build_reasoning(features, score_result, rank):
    detail = score_result["detail"]
    title = features["current_title"] or "Unspecified title"
    company = features["current_company"] or "unspecified company"
    yoe = features["yoe"]

    skills = _top_skills(detail)
    if skills:
        skills_clause = f"; skills evidenced in {', '.join(skills)}"
    else:
        skills_clause = ""

    prod_label = detail.get("company_label", "")
    if prod_label and "no distinguishing" not in prod_label:
        prod_clause = f"; {prod_label}"
    else:
        prod_clause = ""

    concerns = _find_concern(features, score_result)
    concern_text = concerns[0] if concerns else None

    if rank > 70 and concern_text:
        template = _pick(features["candidate_id"] + "f", FILLER_TEMPLATES)
        text = template.format(
            title=title, company=company, yoe=yoe,
            skills_clause=skills_clause, concern=concern_text,
        )
    elif concern_text:
        template = _pick(features["candidate_id"] + "c", WITH_CONCERN_TEMPLATES)
        text = template.format(
            title=title, company=company, yoe=yoe,
            skills_clause=skills_clause, prod_clause=prod_clause,
            concern=concern_text,
        )
    else:
        template = _pick(features["candidate_id"] + "p", POSITIVE_TEMPLATES)
        text = template.format(
            title=title, company=company, yoe=yoe,
            skills_clause=skills_clause, prod_clause=prod_clause,
        )

    # keep it to roughly 1-2 sentences / under ~260 chars
    return text[:280]

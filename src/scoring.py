"""
Composite scoring.

Final score = weighted sum of six 0-1 components, then adjusted by a
behavioral "availability" multiplier and by hard/soft gates for the
disqualifying patterns the JD calls out explicitly (pure-research-only,
consulting-only career, CV/speech-only expertise, title-chasing). Honeypots
are excluded outright (see integrity.py).

Weights (sum to 1.0):
    skill_fit            0.35
    title_role_fit        0.20
    production_evidence   0.15
    experience_fit         0.10
    location_fit           0.10
    behavioral (additive)  0.10

On top of the weighted sum we apply a multiplicative availability factor
derived from behavioral signals (JD: "a perfect-on-paper candidate who
hasn't logged in for 6 months and has a 5% recruiter response rate is, for
hiring purposes, not actually available -- down-weight them appropriately").
"""

from . import constants as K

WEIGHTS = {
    "skill_fit": 0.35,
    "title_role_fit": 0.20,
    "production_evidence": 0.15,
    "experience_fit": 0.10,
    "location_fit": 0.10,
    "behavioral": 0.10,
}


def _clip(x, lo=0.0, hi=1.0):
    return max(lo, min(hi, x))


# ---------------------------------------------------------------------------
# Skill fit
# ---------------------------------------------------------------------------

def score_skills(features):
    skills = features["skills"]
    core_hits, nice_hits, offtopic_hits = [], [], []
    core_raw = 0.0
    nice_raw = 0.0

    for s in skills:
        name = (s.get("name") or "").strip()
        name_l = name.lower()
        prof_mult = K.PROFICIENCY_MULT.get(s.get("proficiency"), 0.6)
        duration = int(s.get("duration_months") or 0)
        endorsements = int(s.get("endorsements") or 0)

        # Trust weighting: a claimed skill with zero months of use and zero
        # endorsements is weak evidence -- count it, but discount it, so a
        # keyword-stuffed skills list doesn't score as well as one backed by
        # real usage.
        trust = 1.0 if (duration > 0 or endorsements > 0) else 0.4

        if name_l in K.CORE_SKILLS:
            core_raw += prof_mult * trust
            core_hits.append(name)
        elif name_l in K.NICE_TO_HAVE_SKILLS:
            nice_raw += prof_mult * trust
            nice_hits.append(name)
        elif name_l in K.OFFTOPIC_SKILLS:
            offtopic_hits.append(name)

    # Normalize: ~6 well-evidenced core skills at "advanced" saturates the
    # score (roughly matches a strong senior IR/ML profile in this dataset).
    core_norm = _clip(core_raw / 6.0)
    nice_norm = _clip(nice_raw / 4.0)

    skill_fit = _clip(0.8 * core_norm + 0.2 * nice_norm)

    return {
        "skill_fit": skill_fit,
        "core_skill_hits": core_hits,
        "nice_skill_hits": nice_hits,
        "offtopic_skill_hits": offtopic_hits,
    }


# ---------------------------------------------------------------------------
# Title / role fit
# ---------------------------------------------------------------------------

def score_title(features):
    title_l = features["current_title_l"]
    if title_l in K.CORE_TITLES:
        base, label = 1.0, "core AI/ML/IR title"
    elif title_l in K.CV_ONLY_TITLES:
        base, label = 0.35, "CV-focused title (JD wants NLP/IR exposure too)"
    elif title_l in K.ADJACENT_TITLES:
        base, label = 0.5, "adjacent engineering title"
    elif title_l in K.IRRELEVANT_TITLES:
        base, label = 0.03, "title unrelated to the role"
    else:
        base, label = 0.4, "unrecognized/other title"

    # Trajectory bonus: did earlier roles also sit in core/adjacent buckets
    # (i.e. this isn't a one-off relabeling)?
    other_titles = features["all_titles_l"][1:]
    core_prior = sum(1 for t in other_titles if t in K.CORE_TITLES)
    if core_prior >= 1 and base >= 0.5:
        base = _clip(base + 0.1)

    return {"title_role_fit": _clip(base), "title_label": label}


# ---------------------------------------------------------------------------
# Production evidence / company quality / career-pattern gates
# ---------------------------------------------------------------------------

def score_production(features):
    text = features["concat_text"]
    companies = set(features["all_companies_l"])

    evidence_hits = [p for p in K.PRODUCTION_EVIDENCE_PHRASES if p in text]
    evidence_norm = _clip(len(evidence_hits) / 5.0)

    company_bonus = 0.0
    company_label = "no distinguishing employer"
    if companies & K.ELITE_PRODUCT_COMPANIES:
        company_bonus = 0.35
        company_label = "elite large-scale product company on record"
    elif companies & K.AI_PRODUCT_COMPANIES:
        company_bonus = 0.35
        company_label = "AI-native product company on record"
    elif companies & K.OTHER_PRODUCT_COMPANIES:
        company_bonus = 0.18
        company_label = "product company on record"

    production_evidence = _clip(0.6 * evidence_norm + 0.4 * (company_bonus / 0.35 if company_bonus else 0.0))

    # Gate: consulting-only career (JD explicit disqualifier).
    consulting_only = bool(companies) and companies.issubset(K.CONSULTING_COMPANIES)

    # Gate: pure-research-only language, no production/deployment evidence.
    research_hits = [p for p in K.PURE_RESEARCH_PHRASES if p in text]
    deploy_hits = [p for p in K.PRODUCTION_DEPLOYMENT_PHRASES if p in text]
    pure_research_only = bool(research_hits) and not deploy_hits

    # Gate: CV/speech/robotics-only expertise, no NLP/IR signal at all.
    has_offtopic_skill = any(
        (s.get("name") or "").lower() in K.OFFTOPIC_SKILLS for s in features["skills"]
    )
    has_core_skill = any(
        (s.get("name") or "").lower() in K.CORE_SKILLS for s in features["skills"]
    )
    cv_only = has_offtopic_skill and not has_core_skill

    return {
        "production_evidence": production_evidence,
        "production_evidence_hits": evidence_hits,
        "company_label": company_label,
        "consulting_only": consulting_only,
        "pure_research_only": pure_research_only,
        "cv_speech_only": cv_only,
    }


# ---------------------------------------------------------------------------
# Experience-years fit
# ---------------------------------------------------------------------------

def score_experience(features):
    yoe = features["yoe"]
    if 5 <= yoe <= 9:
        return {"experience_fit": 1.0}
    if 3 <= yoe < 5 or 9 < yoe <= 12:
        return {"experience_fit": 0.7}
    if 1 <= yoe < 3 or 12 < yoe <= 16:
        return {"experience_fit": 0.4}
    return {"experience_fit": 0.2}


# ---------------------------------------------------------------------------
# Location fit
# ---------------------------------------------------------------------------

def score_location(features):
    loc = features["location_l"]
    country = features["country"]
    relocate = features["willing_to_relocate"]
    is_india = country.strip().lower() == "india"

    if any(city in loc for city in K.PRIMARY_LOCATIONS):
        return {"location_fit": 1.0, "location_label": "Pune/Noida (primary office location)"}
    if is_india and any(city in loc for city in K.TIER1_INDIA_LOCATIONS):
        return {"location_fit": 0.85, "location_label": "Tier-1 India city named as welcome in the JD"}
    if is_india and relocate:
        return {"location_fit": 0.6, "location_label": "India, other city, willing to relocate"}
    if is_india:
        return {"location_fit": 0.35, "location_label": "India, other city, not confirmed willing to relocate"}
    if relocate:
        return {"location_fit": 0.3, "location_label": "outside India, willing to relocate (visa sponsorship not offered)"}
    return {"location_fit": 0.1, "location_label": "outside India, no relocation signal (JD: no visa sponsorship)"}


# ---------------------------------------------------------------------------
# Behavioral signals -> additive score + multiplicative availability factor
# ---------------------------------------------------------------------------

def score_behavioral(features):
    sig = features["signals"]
    days_inactive = features["days_since_active"]

    recency = _clip(1 - days_inactive / 270.0)
    open_flag = 1.0 if features["open_to_work_flag"] else 0.3
    response_rate = _clip(float(sig.get("recruiter_response_rate") or 0))
    resp_time = sig.get("avg_response_time_hours")
    resp_time_score = _clip(1 - (resp_time or 72) / 72.0)

    verified = [
        bool(sig.get("verified_email")),
        bool(sig.get("verified_phone")),
        bool(sig.get("linkedin_connected")),
    ]
    verified_score = sum(verified) / 3.0

    notice = sig.get("notice_period_days")
    if notice is None:
        notice_score = 0.5
    elif notice <= 30:
        notice_score = 1.0
    elif notice <= 45:
        notice_score = 0.7
    elif notice <= 60:
        notice_score = 0.5
    elif notice <= 90:
        notice_score = 0.3
    else:
        notice_score = 0.1

    interview_rate = _clip(float(sig.get("interview_completion_rate") or 0))
    offer_rate = sig.get("offer_acceptance_rate")
    offer_score = 0.6 if offer_rate is None or offer_rate < 0 else _clip(offer_rate)

    completeness = _clip(float(sig.get("profile_completeness_score") or 0) / 100.0)

    gh = sig.get("github_activity_score")
    gh_score = 0.5 if gh is None or gh < 0 else _clip(gh / 100.0)

    behavioral_additive = _clip(
        0.20 * open_flag
        + 0.20 * recency
        + 0.20 * response_rate
        + 0.10 * resp_time_score
        + 0.10 * notice_score
        + 0.10 * verified_score
        + 0.05 * interview_rate
        + 0.05 * completeness
    )

    # Availability multiplier: JD explicitly wants inactive / unresponsive
    # candidates down-weighted regardless of how strong they look on paper.
    availability_factor = 0.5 + 0.5 * (
        (open_flag + recency + response_rate) / 3.0
    )

    return {
        "behavioral": behavioral_additive,
        "availability_factor": _clip(availability_factor, 0.5, 1.0),
        "response_rate": response_rate,
        "days_inactive": days_inactive,
        "notice_period_days": notice,
        "gh_score": gh_score,
        "offer_score": offer_score,
    }


# ---------------------------------------------------------------------------
# Title-chasing pattern
# ---------------------------------------------------------------------------

def score_title_chasing(features):
    intervals = features["career_intervals"]
    if len(intervals) < 3:
        return {"title_chasing": False, "title_chase_multiplier": 1.0}
    short_stints = sum(1 for iv in intervals if iv["duration_months"] < 20)
    frac_short = short_stints / len(intervals)
    n_employers = len(set(iv["company"] for iv in intervals))
    chasing = frac_short >= 0.6 and n_employers >= 3
    return {
        "title_chasing": chasing,
        "title_chase_multiplier": 0.8 if chasing else 1.0,
    }


# ---------------------------------------------------------------------------
# Composite
# ---------------------------------------------------------------------------

def compute_score(features, honeypot_result):
    if honeypot_result["is_honeypot"]:
        return {
            "final_score": 0.0,
            "excluded": True,
            "exclude_reason": "honeypot: " + "; ".join(honeypot_result["reasons"]),
        }

    skill = score_skills(features)
    title = score_title(features)
    production = score_production(features)
    experience = score_experience(features)
    location = score_location(features)
    behavioral = score_behavioral(features)
    chasing = score_title_chasing(features)

    weighted = (
        WEIGHTS["skill_fit"] * skill["skill_fit"]
        + WEIGHTS["title_role_fit"] * title["title_role_fit"]
        + WEIGHTS["production_evidence"] * production["production_evidence"]
        + WEIGHTS["experience_fit"] * experience["experience_fit"]
        + WEIGHTS["location_fit"] * location["location_fit"]
        + WEIGHTS["behavioral"] * behavioral["behavioral"]
    )

    gate_multiplier = 1.0
    gate_reasons = []
    if production["consulting_only"]:
        gate_multiplier *= 0.15
        gate_reasons.append("consulting-only career (no product-company experience)")
    if production["pure_research_only"]:
        gate_multiplier *= 0.2
        gate_reasons.append("pure-research language with no production/deployment evidence")
    if production["cv_speech_only"]:
        gate_multiplier *= 0.3
        gate_reasons.append("CV/speech-only expertise, no NLP/IR signal")
    gate_multiplier *= chasing["title_chase_multiplier"]
    if chasing["title_chasing"]:
        gate_reasons.append("job-hopping pattern (frequent <20mo stints)")

    final = _clip(weighted * gate_multiplier * behavioral["availability_factor"])

    return {
        "final_score": final,
        "excluded": False,
        "components": {
            "skill_fit": skill["skill_fit"],
            "title_role_fit": title["title_role_fit"],
            "production_evidence": production["production_evidence"],
            "experience_fit": experience["experience_fit"],
            "location_fit": location["location_fit"],
            "behavioral": behavioral["behavioral"],
            "availability_factor": behavioral["availability_factor"],
            "gate_multiplier": gate_multiplier,
        },
        "detail": {
            **skill,
            **title,
            **production,
            **location,
            **behavioral,
            **chasing,
            "gate_reasons": gate_reasons,
        },
    }

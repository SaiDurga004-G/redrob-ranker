"""
Honeypot / profile-integrity checks.

submission_spec.md Section 7 says the dataset contains ~80 honeypot
candidates with "subtly impossible profiles" (e.g. claimed years of
experience that don't match career history, or 'expert' proficiency in
skills the candidate has used for zero months) and that submissions with a
honeypot rate above 10% in the top 100 are disqualified at Stage 3.

We check two independently-verifiable internal-consistency signals:

  1. `years_of_experience` vs. the sum of `career_history` duration_months
     -- a large mismatch means the headline experience figure doesn't
     reconcile with the candidate's own timeline.
  2. Skills claimed at "expert"/"advanced" proficiency with 0 months of
     use -- claiming mastery of something you've never spent time on.

Profiling the full 100k-candidate pool, these two checks fire on 69
candidates, almost all with zero overlap between the two -- consistent
with ~80 deliberately-planted honeypots (some slice of the remainder likely
uses signals we can't reconstruct from the data we have, e.g. company
founding dates). Because false positives were not observed among sampled
"normal" candidates, either flag alone is treated as disqualifying.
"""

MISMATCH_ABS_MONTHS = 24
MISMATCH_REL_FRACTION = 0.4
IMPOSSIBLE_SKILL_COUNT = 3


def check_honeypot(features: dict) -> dict:
    yoe_months = features["yoe"] * 12
    total_months = features["total_career_months"]
    diff = abs(yoe_months - total_months)
    yoe_mismatch = diff > max(MISMATCH_ABS_MONTHS, MISMATCH_REL_FRACTION * yoe_months)

    impossible_skills = [
        s["name"]
        for s in features["skills"]
        if s.get("proficiency") in ("expert", "advanced")
        and int(s.get("duration_months") or 0) == 0
    ]
    skill_flag = len(impossible_skills) >= IMPOSSIBLE_SKILL_COUNT

    is_honeypot = yoe_mismatch or skill_flag
    reasons = []
    if yoe_mismatch:
        reasons.append(
            f"experience-timeline mismatch (claims {features['yoe']}y "
            f"but career_history sums to {total_months/12:.1f}y)"
        )
    if skill_flag:
        reasons.append(
            f"{len(impossible_skills)} skills at expert/advanced with 0 "
            f"months used ({', '.join(impossible_skills[:3])}...)"
        )

    return {"is_honeypot": is_honeypot, "reasons": reasons}

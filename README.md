# Redrob Hackathon — Intelligent Candidate Discovery & Ranking

A transparent, rule-based ranker for the Redrob "Intelligent Candidate
Discovery & Ranking Challenge." Produces a top-100 shortlist CSV against
the released job description, entirely offline, CPU-only, in ~15 seconds
for the full 100K-candidate pool.

## Quickstart

```bash
# no third-party dependencies needed for ranking itself
python rank.py --candidates ./candidates.jsonl --out ./submission.csv
```

That single command reproduces `submission.csv` from `candidates.jsonl`
end to end. It also transparently handles a gzipped pool:

```bash
python rank.py --candidates ./candidates.jsonl.gz --out ./submission.csv
```

Validate before submitting:

```bash
python validate_submission.py submission.csv
```

(Optional) export a human-readable `.xlsx` shortlist for internal review,
joining the ranked CSV back against full candidate profiles:

```bash
pip install -r requirements.txt   # openpyxl only, for the xlsx export
python scripts/export_xlsx.py --candidates ./candidates.jsonl \
    --submission ./submission.csv --out ./shortlist.xlsx
```

Run the (dependency-free) sanity tests:

```bash
python tests/test_ranker.py
```

## Why rule-based, not embeddings/LLM re-ranking

The compute budget (≤5 min, CPU-only, no network, 16GB RAM) rules out
per-candidate LLM calls at 100K scale, and the JD itself says as much
("plan for a small ranker over precomputed features ... rather than an
LLM call per candidate"). A transparent, feature-scored ranker also has a
practical advantage for this challenge specifically: every scoring
decision is explainable, which is what the `reasoning` column and the
Stage 5 "defend your work" interview actually reward. Nothing here is a
black box — every weight and keyword list lives in `src/constants.py`
and `src/scoring.py` and can be inspected, argued with, and tuned.

## Architecture

```
rank.py                 CLI entry point: stream -> score -> top-100 heap -> CSV
src/
  constants.py           curated keyword/company/title vocabularies
  features.py             raw candidate JSON -> flat feature dict
  integrity.py            honeypot / profile-consistency detection
  scoring.py               six weighted 0-1 components + gates -> final score
  reasoning.py             fact-grounded, varied `reasoning` text generation
tests/
  test_ranker.py           honeypot exclusion + anti-keyword-stuffing checks
scripts/
  export_xlsx.py            optional: submission.csv + candidates.jsonl -> .xlsx
```

**Streaming, not batch.** `rank.py` reads `candidates.jsonl` one line at a
time and keeps only a size-100 min-heap of the best candidates seen so
far — memory use is O(1) in the pool size, not O(n). This is also why it
comfortably scales past 100K candidates within the compute budget.

## Methodology (mirrors `methodology_summary` in `submission_metadata.yaml`)

Each candidate gets six 0–1 component scores, weighted and summed:

| Component | Weight | What it captures |
|---|---|---|
| `skill_fit` | 0.35 | Trust-weighted match against JD "must-have" skills (embeddings/retrieval, vector DB/hybrid search, Python, ranking/eval). A skill with 0 months used and 0 endorsements counts at 40% strength — this is the main defense against keyword-stuffed skill lists. |
| `title_role_fit` | 0.20 | Current + historical titles bucketed into core / CV-only / adjacent / irrelevant. This is the primary defense against a keyword-stuffed *non*-technical title (e.g. "HR Manager" with 9 AI skills) outranking a genuine ML engineer. |
| `production_evidence` | 0.15 | Free-text scan of headline/summary/career descriptions for production-deployment language, plus employer tier (elite big tech / AI-native product company / other product company / IT-services). |
| `experience_fit` | 0.10 | Triangular preference peaking at the JD's 5–9y band. |
| `location_fit` | 0.10 | Pune/Noida highest, other Tier-1 India cities next, then India+relocation-willing, then outside-India (JD: no visa sponsorship). |
| `behavioral` | 0.10 | Redrob signals: open-to-work, recency of activity, recruiter response rate/time, verification, notice period, interview completion, profile completeness. |

On top of the weighted sum:

- **Availability multiplier** (0.5–1.0×): derived from open-to-work flag,
  activity recency, and recruiter response rate. Directly implements the
  JD's instruction to down-weight a "perfect-on-paper candidate who
  hasn't logged in for 6 months and has a 5% response rate."
- **Hard/soft gates** (multiplicative penalties, not outright exclusion,
  since the JD says these disqualifiers are about *primary* career
  pattern, not any single data point): consulting-only career (×0.15),
  pure-research-only language with no deployment evidence (×0.2),
  CV/speech-only expertise with zero NLP/IR signal (×0.3), and a
  job-hopping pattern of frequent <20-month stints (×0.8).
- **Honeypot exclusion** (see below): candidates are dropped entirely,
  not merely down-weighted, since the challenge scores honeypot rate as
  a hard Stage-3 cutoff.

### Honeypot detection

Profiling the released 100K-candidate pool found two internally-checkable
inconsistency patterns:

1. `years_of_experience` doesn't reconcile with the sum of
   `career_history[].duration_months` (large mismatch).
2. Three or more skills claimed at `expert`/`advanced` proficiency with
   `duration_months == 0`.

These two checks fire on 69 candidates in the released pool, with almost
no overlap between them, consistent with the spec's "~80 honeypots" (the
remaining gap is likely inconsistency patterns we can't reconstruct
without data we don't have, e.g. company founding dates). Either flag
alone excludes a candidate outright — no false positives were observed
among manually-sampled non-flagged candidates.

### Known limitations

- Company/title/skill matching is keyword-and-list based rather than
  semantic, so genuinely novel phrasing not represented in the
  dataset's actual vocabulary (profiled directly from `candidates.jsonl`)
  could be under-scored. This is a deliberate tradeoff for the compute
  budget and for explainability.
- "Closed-source-only 5+ years without external validation" (one of the
  JD's explicit disqualifiers) isn't checked — the dataset has no
  open-source/publication field to check against.
- The "shallow recent-LangChain-only AI experience" disqualifier is only
  partially captured, via the general production-evidence and skill-trust
  scoring, rather than a dedicated recency-of-AI-skill-only check.

## Compute environment this was developed/tested on

- CPU-only, single core, ~4GB RAM container (Python 3.x)
- Full 100,000-candidate pool: ranked in ~15 seconds
- No GPU, no network calls during ranking

## AI tools used

Anthropic's Claude was used to design and implement this ranking
pipeline (feature engineering, scoring logic, honeypot detection,
reasoning generation, and this README) based on a close reading of the
provided job description, submission spec, and signals doc, and by
profiling the actual `candidates.jsonl` vocabulary (title/company/skill
frequency counts) to ground the keyword lists in real data rather than
guesswork. No candidate data was sent to any external API during the
ranking step itself — `rank.py` runs fully offline. **Before submitting,
fill in `ai_tools_used` / `ai_usage_summary` in `submission_metadata.yaml`
to accurately reflect your own team's workflow.**

## Before you submit

`submission_metadata.yaml` in this repo root is copied from the
hackathon's template and has placeholder team info — **edit it** with
your actual team name, contacts, GitHub URL, and sandbox link before
uploading. See `submission_metadata_template.yaml` (from the original
hackathon bundle) for field descriptions.

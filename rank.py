#!/usr/bin/env python3
"""
Redrob Hackathon -- Intelligent Candidate Discovery & Ranking Challenge.

Streams the candidate pool (one JSON object per line, optionally gzipped),
scores every candidate with a transparent, rule-based feature scorer
(see src/scoring.py), excludes honeypots (see src/integrity.py), and
writes the top-100 ranking as a CSV matching submission_spec.md.

Usage:
    python rank.py --candidates ./candidates.jsonl --out ./submission.csv

Runs single-threaded, CPU-only, no network calls, streaming (O(1) memory
per candidate + a size-100 heap) so it comfortably meets the challenge's
5-minute / 16GB / CPU-only / no-network compute constraints regardless of
pool size.
"""

import argparse
import csv
import gzip
import heapq
import itertools
import json
import sys
import time

from src.features import extract_features
from src.integrity import check_honeypot
from src.scoring import compute_score
from src.reasoning import build_reasoning

TOP_N = 100
REQUIRED_HEADER = ["candidate_id", "rank", "score", "reasoning"]


def _open(path):
    if path.endswith(".gz"):
        return gzip.open(path, "rt", encoding="utf-8")
    return open(path, "r", encoding="utf-8")


def run(candidates_path: str, out_path: str, limit: int = None):
    t0 = time.time()
    heap = []  # (final_score, counter, features, score_result)
    counter = itertools.count()
    n_seen = 0
    n_excluded = 0
    n_errors = 0

    with _open(candidates_path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            n_seen += 1
            if limit and n_seen > limit:
                break
            try:
                cand = json.loads(line)
                features = extract_features(cand)
                honeypot = check_honeypot(features)
                result = compute_score(features, honeypot)
            except Exception as e:  # noqa: BLE001 -- keep ranking robust to bad rows
                n_errors += 1
                print(f"  [warn] skipping malformed row {n_seen}: {e}", file=sys.stderr)
                continue

            if result["excluded"]:
                n_excluded += 1
                continue

            entry = (result["final_score"], next(counter), features, result)
            if len(heap) < TOP_N:
                heapq.heappush(heap, entry)
            elif entry[0] > heap[0][0]:
                heapq.heapreplace(heap, entry)

    if n_seen == 0:
        raise SystemExit(f"No candidates read from {candidates_path}")

    # Final deterministic ordering: descending 4-decimal score, then
    # candidate_id ascending -- matches submission_spec.md tie-break rule
    # and validate_submission.py exactly.
    ranked = sorted(
        heap,
        key=lambda e: (-round(e[0], 4), e[2]["candidate_id"]),
    )

    if len(ranked) < TOP_N:
        print(
            f"  [warn] only {len(ranked)} non-excluded candidates available "
            f"(< {TOP_N}); check --candidates path / honeypot thresholds.",
            file=sys.stderr,
        )

    rows = []
    for i, (score, _, features, result) in enumerate(ranked[:TOP_N], start=1):
        reasoning = build_reasoning(features, result, i)
        rows.append(
            {
                "candidate_id": features["candidate_id"],
                "rank": i,
                "score": f"{round(score, 4):.4f}",
                "reasoning": reasoning,
            }
        )

    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=REQUIRED_HEADER)
        writer.writeheader()
        writer.writerows(rows)

    elapsed = time.time() - t0
    print(f"Scanned {n_seen} candidates in {elapsed:.1f}s "
          f"({n_excluded} honeypots excluded, {n_errors} malformed rows skipped).")
    print(f"Wrote top {len(rows)} to {out_path}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidates", required=True, help="Path to candidates.jsonl or candidates.jsonl.gz")
    parser.add_argument("--out", required=True, help="Path to write the submission CSV")
    parser.add_argument("--limit", type=int, default=None, help="Optional: only read the first N lines (debugging)")
    args = parser.parse_args()
    run(args.candidates, args.out, args.limit)


if __name__ == "__main__":
    main()

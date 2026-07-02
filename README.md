Redrob Hackathon – Intelligent Candidate Discovery & Ranking

Overview

This project is a transparent, rule-based candidate ranking system developed for the Redrob Intelligent Candidate Discovery & Ranking Challenge. It analyzes the provided candidate dataset, evaluates profiles against the supplied job description, and generates a ranked shortlist of the Top 100 candidates.

The solution is designed to work entirely offline, uses CPU-only computation, and processes the complete 100,000-candidate dataset in approximately 15 seconds.

Features

Rule-based and explainable ranking
Processes the complete 100K candidate dataset
Generates Top-100 ranked candidates
Detects and filters inconsistent (honeypot) profiles
Produces human-readable reasoning for every shortlisted candidate
Generates CSV and XLSX output files
No GPU or internet connection require

Project Structure
redrob-ranker/
│
├── output/
│   └── redrob_submission.csv
│
├── scripts/
│   └── export_xlsx.py
│
├── src/
│   ├── constants.py
│   ├── features.py
│   ├── integrity.py
│   ├── reasoning.py
│   └── scoring.py
│
├── tests/
│   └── test_ranker.py
│
├── rank.py
├── requirements.txt
├── README.md
└── submission_metadata.yaml

Quick Start

Install dependencies

python -m pip install -r requirements.txt

Generate the ranked CSV

python rank.py --candidates ./candidates.jsonl --out ./output/redrob_submission.csv

(Optional) Generate the Excel shortlist

python scripts/export_xlsx.py --candidates ./candidates.jsonl --submission ./output/redrob_submission.csv --out ./shortlist.xlsx

Run the sanity tests

python tests/test_ranker.py
Ranking Methodology

Each candidate is evaluated using six weighted scoring components.

Component	         Weight
Skill Fit	          35%
Title & Role Fit	  20%
Production Evidence	  15%
Experience Fit	      10%
Location Fit	      10%
Behavioral Signals	  10%

Additional adjustments include:

Availability multiplier
Job-hopping penalty
Consulting-only penalty
Research-only penalty
Honeypot filtering

The final score is computed as the weighted combination of these factors.

Honeypot Detection

The system identifies suspicious profiles using consistency checks, including:

Mismatch between total experience and career history duration
Expert-level skills reported with zero practical experience

During testing, the system excluded 69 inconsistent profiles from the released dataset.

Performance
Dataset Size: 100,000 candidates
Processing Time: ~15 seconds
Execution Mode: Offline
CPU Only
No network access required
Technologies Used
Python 3.11
Standard Python Library
OpenPyXL (for XLSX export)
VS Code
Git & GitHub
AI Assistance

AI-assisted development tools (Claude and ChatGPT) were used to assist with implementation, debugging, documentation, and code refinement.

The ranking pipeline was executed and validated locally using the provided candidate dataset. No external AI services are used during candidate ranking; the solution runs entirely offline.

Output Files

The project generates:

output/redrob_submission.csv

and (optional)

shortlist.xlsx

containing the ranked Top-100 candidates.

Compute Environment
Operating System: Windows 11
Python: 3.11.9
RAM: 16 GB
CPU: Multi-core Processor
GPU: Not Required
Repository

GitHub Repository:

https://github.com/SaiDurga004-G/redrob-ranker

Team
Team Name: The Token Girls

Team Members

Sai Durga Gundu
Lakshmi Jyothi Chanda
Lakshmi Varsha Gogusetty

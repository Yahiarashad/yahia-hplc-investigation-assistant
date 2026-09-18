# Yahia HPLC Investigation Assistant

**DON'T GUESS. FOLLOW THE EVIDENCE.**

A Streamlit-based HPLC troubleshooting and analytical decision-support assistant for Pharmaceutical QC.

## Current version — v0.7

Core scope:
- High / low / fluctuating pressure
- Retention-time shifts
- Peak tailing / fronting / splitting / broadening
- Baseline noise / drift / spikes
- Carryover / ghost peaks

Additional v0.7 capabilities:
- Arabic + English interface and responses
- Evidence-first investigation framework
- Change-Delta Check for last-known-good vs current-failure comparisons
- Conversation persistence across refresh using case IDs
- Verified Evidence Engine with local retrieval of relevant curated source cards
- 20-case validation suite

## How the assistant thinks

OBSERVE → PRESERVE EVIDENCE → LOCALIZE → HYPOTHESIZE → TEST → CONFIRM → DECIDE → DOCUMENT

The assistant is designed to avoid generic part-swapping advice. It asks a small number of high-value diagnostic questions, prefers tests that distinguish between hypotheses, and separates observation from hypothesis, evidence, and conclusion.

## Verified Evidence Engine

The application retrieves a small number of relevant evidence cards per turn rather than sending the entire knowledge base with every request.

Current source families include:
- Waters
- Agilent
- Shimadzu
- Thermo Fisher Scientific
- USP
- U.S. FDA
- ICH

Files:
- `verified_evidence.json` — curated evidence cards
- `evidence_engine.py` — lightweight local retrieval
- `EVIDENCE_MAP.md` — source hierarchy and citation rules

General source material supports hypotheses and diagnostic choices; it does **not** prove the root cause in a specific laboratory case.

## Validation

Files:
- `validation_cases.md` — detailed results from the first live cases
- `validation_suite_20.md` — full 20-case validation suite

Current live validation results:
- Case 01: 12/12
- Case 02: 12/12
- Case 03: 11/12

Case 03 exposed a diagnostic-prioritization gap and led to the Change-Delta Check rule in the core prompt.

## Streamlit deployment

Main file: `app.py`

Required secret:

```toml
OPENAI_API_KEY = "your-key"
```

Add the key only through Streamlit Secrets or a secure environment variable. Never commit it to GitHub.

## GMP note

This is decision-support software. It does not replace approved laboratory SOPs, QA oversight, formal investigations, applicable compendial requirements, manufacturer instructions, or regulatory requirements.

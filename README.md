# Yahia HPLC Investigation Assistant

**DON'T GUESS. FOLLOW THE EVIDENCE.**

A Streamlit prototype for evidence-based HPLC troubleshooting and analytical decision support in Pharmaceutical QC.

## Current v0.1 scope

- High / low / fluctuating pressure
- Retention-time shifts
- Peak tailing / fronting / splitting / broadening
- Baseline noise / drift / spikes
- Carryover / ghost peaks

## How the assistant thinks

OBSERVE → PRESERVE EVIDENCE → LOCALIZE → HYPOTHESIZE → TEST → CONFIRM → DECIDE → DOCUMENT

The assistant is designed to avoid generic part-swapping advice. It asks a small number of high-value diagnostic questions, prefers tests that distinguish between hypotheses, and separates observation from hypothesis, evidence, and conclusion.

## Streamlit deployment

Main file: `app.py`

Required secret:

```toml
OPENAI_API_KEY = "your-key"
```

Add the key only through Streamlit Secrets or a secure environment variable. Never commit it to GitHub.

## Validation case

Try:

> Pressure was normally 180 bar. Today it increased to 310 bar after about 25 injections. Same method, column, flow, and mobile phase.

A good response should not immediately blame the column. It should identify missing evidence and choose the next diagnostic question or isolation test.

## GMP note

This is decision-support software, not a replacement for approved laboratory SOPs, QA oversight, formal investigations, or applicable regulatory requirements.

# QC DATA REVIEWER™

Standalone Streamlit prototype for evidence-based HPLC Assay data review.

## Entrypoint

`qc_data_reviewer_app/app.py`

## Current scope

- CSV/XLSX sequence input
- Sequence integrity and traceability checks
- SST review: area %RSD, tailing, plates, resolution
- Standard/bracketing response drift
- Retention-time deviation
- Assay specification and replicate agreement checks
- Review Coverage separated from finding severity
- Findings export to CSV and multi-sheet XLSX
- Evidence language: OBSERVED / INFERRED RISK / MISSING INFORMATION

## GMP safeguard

This is a decision-support prototype. It does not approve, release, invalidate, or repeat a batch/run automatically. Final GMP review and disposition remain with authorized personnel.

## Run locally

From the repository root:

```bash
pip install -r qc_data_reviewer_app/requirements.txt
streamlit run qc_data_reviewer_app/app.py
```

## Streamlit Community Cloud

Deploy this as a separate app using the same repository but set the entrypoint to:

`qc_data_reviewer_app/app.py`

The dependency file beside the entrypoint is intentionally separate from the main HPLC app dependencies.

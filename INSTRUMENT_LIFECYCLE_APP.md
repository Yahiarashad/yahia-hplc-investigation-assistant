# Yahia QC Instrument Lifecycle & Investigation Intelligence™

**Status:** v0.1 MVP

**Tagline:** DON'T GUESS. FOLLOW THE EVIDENCE.

Standalone Streamlit entrypoint:

`instrument_lifecycle_app.py`

## MVP modules

1. **Instrument Command Center**
   - Instrument inventory
   - Health Score
   - Open-event count
   - Overdue / upcoming lifecycle actions

2. **Digital Instrument Passport**
   - Instrument ID
   - Type, manufacturer, model, serial number
   - Location and responsible team
   - Operational status
   - Qualification, PM, and calibration due dates

3. **Lifecycle Calendar**
   - Overdue items
   - Items due within 30 / 60 days

4. **Instrument Event / Failure Log**
   - Event type and severity
   - Subsystem
   - Observed facts
   - Immediate action / containment
   - Root cause status: Not identified / Probable / Confirmed
   - Investigation / deviation / work-order reference

5. **QC Investigation Intelligence™**
   - Separates current observations from assumptions
   - Detects repeat subsystem / event-type signals in recent history
   - Includes lifecycle alerts in the evidence map
   - Highlights missing evidence
   - Suggests one evidence-focused next action
   - Does not convert recurrence into a confirmed root cause

6. **Data / Backup**
   - CSV export/import
   - Demo data
   - Session reset

## Important MVP boundary

This version is a decision-support prototype. It is **not** a validated GxP system of record and should not replace approved SOPs, QA controls, validated CMMS/LIMS/CDS systems, official qualification/calibration records, or controlled investigation records.

## Deploy as a separate Streamlit app

Streamlit Community Cloud supports multiple apps from one repository. Deploy this entrypoint as a new app:

- Repository: `Yahiarashad/yahia-hplc-investigation-assistant`
- Branch: `main`
- Main file path: `instrument_lifecycle_app.py`

Choose a separate Streamlit subdomain so it runs independently from the HPLC Investigation Assistant.

## Next architecture milestone

For v0.2, move prototype persistence from session/CSV into a controlled external data layer, add editable lifecycle records and document attachments, then add role-aware review and audit history before considering regulated operational use.

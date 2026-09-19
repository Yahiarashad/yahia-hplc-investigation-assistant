# Yahia QC Instrument Lifecycle & Investigation Intelligence™
## v0.3 Implementation Specification

**Product positioning:** Helping Pharmaceutical Analysts Make Better Laboratory Decisions.

**Core principle:** **DON’T GUESS. FOLLOW THE EVIDENCE.**

**Scope of v0.3:** Transform the current Streamlit application from a set of functional modules into a coherent, interactive, mobile-first **Instrument Lifecycle Control System** that follows the complete equipment journey from the first idea/need for purchase through qualification, routine operation, calibration/maintenance, investigation, periodic review, and final retirement/decommissioning.

---

## 1. Non-negotiable product principles

1. Preserve current Supabase Auth, encrypted persistent login, per-user data isolation, and RLS.
2. Supabase remains the system used by the application for persistence; Streamlit session state must never be the source of truth for lifecycle records.
3. Never silently infer a completed GxP milestone. A milestone is complete only when the user records the required evidence/date/reference.
4. The app is decision support, not a validated GxP system of record. Keep the existing disclaimer visible but compact.
5. Keep evidence categories separate: **Observed / Recorded**, **Inferred**, and **Unknown**.
6. Repeated history may strengthen a hypothesis but must never be presented as confirmed root cause by itself.
7. Mobile-first UX is mandatory. Avoid wide tables as the only way to use a module.
8. Arabic guidance must render RTL correctly; English remains LTR.

---

## 2. Visual redesign

### 2.1 Hero / visual background

Create a premium pharmaceutical-tech hero section using a subtle collage/background containing:

- HPLC
- LC-MS / LC-MS/MS
- GC
- pH meter
- Analytical balance
- Viscometer

The background must be decorative only: apply a dark navy/white gradient overlay and reduced opacity so text remains easy to read. Do **not** place a strong image behind forms or tables.

Preferred visual identity:

- Deep navy / near-black
- White / very light gray surfaces
- Premium gold accents
- Teal/green for healthy/on-time states
- Amber for due-soon
- Red only for genuine overdue/critical/OOC states
- Rounded elevated cards
- Soft shadows, no clutter

Add an asset location such as:

`assets/instrument_lifecycle_hero.png`

The generated instrument collage may be used as inspiration, but crop/recompose it into a clean hero background rather than placing the complete phone mockup inside the app.

### 2.2 Interactive home dashboard

Replace the visually static opening area with interactive cards.

Top KPIs:

- Total instruments
- Instruments in acquisition/qualification
- Active instruments
- Open events
- Calibration overdue
- PM overdue
- Due within 30 days
- Open OOC / critical investigations

Add a **Quick Actions** row:

- Add Instrument / New Need
- Continue Lifecycle
- Log Calibration
- Log Maintenance
- New Event
- Start Investigation

Add a **Priority Attention Queue** showing only records that need action now.

---

## 3. Core navigation redesign

The main navigation should no longer force users to think in disconnected modules. Use this order:

1. **Dashboard**
2. **Lifecycle**
3. **Instrument Passport**
4. **Calibration & PM**
5. **Events**
6. **Investigation Intelligence**
7. **Reports**
8. **Guide / About**

On mobile, make the primary five destinations obvious and horizontally scrollable without clipped labels. Where possible, add compact icon labels.

The existing `URS · PR · PO` journey must be merged into the full Lifecycle module rather than remain a standalone isolated concept.

---

## 4. Circular lifecycle model

The central design concept of v0.3 is a complete lifecycle loop:

**Need → URS → Quotation → PR → PO → Receiving → Installation → IQ → OQ → PQ → Release/Issuance → First Run → Routine Operation → Calibration/PM/Requalification → Events & Investigation → Periodic Performance Review → Retirement/Decommission**

This must be presented visually as a lifecycle navigator. On desktop it may be circular or horizontal; on mobile use a vertical stepper/progress journey.

Each instrument must expose:

- Current lifecycle phase
- Completion percentage
- Last completed milestone
- Next required milestone
- Missing evidence signals
- Delayed milestones
- Recommended next action

The app must never mark a phase complete from chronology alone.

---

## 5. Lifecycle phases and required fields

### Phase 1 — Need / Initiation

Purpose: record why the equipment is needed before procurement starts.

Fields:

- Need / request title
- Department / laboratory section
- Requested by
- Need identified date
- Business / laboratory justification
- Intended analytical use
- Suggested instrument type
- Criticality: Low / Medium / High / Critical
- Target implementation date
- Notes

Decision support:

- Flag missing justification.
- Flag a critical instrument request without URS started.

### Phase 2 — URS

Fields:

- URS reference / number
- URS version
- URS approval date
- Intended application
- Key technical requirements
- Compliance / GMP requirements
- Data integrity / software requirements
- Environmental / utility requirements
- Approved by / reference note

Status values:

- Not started
- Draft
- Under review
- Approved
- Superseded

### Phase 3 — Vendor / Quotation

Fields:

- Vendor / supplier
- Manufacturer
- Proposed model
- Quotation reference
- Quotation date
- Quotation validity date
- Quoted cost (optional)
- Technical evaluation status
- Selected vendor flag
- Notes

Chronology signal:

- Quotation should normally exist before PR approval.

### Phase 4 — PR

PR means **Purchase Requisition**.

Fields:

- PR number
- PR creation date
- PR approval date
- PR status
- Budget / cost center reference (optional)
- Notes

Do not use BR anywhere in the UI or database.

### Phase 5 — PO

Fields:

- PO number
- PO approval / issue date
- Supplier
- Expected receiving date
- PO status
- Notes

Intelligence:

- Show days elapsed since PO.
- Show days remaining to expected receipt.
- Flag overdue receipt when expected date has passed and no receiving date exists.

### Phase 6 — Receiving

Fields:

- Actual receiving date
- Receiving reference
- Received by
- Package condition
- Accessories completeness
- Documentation received
- Damage / discrepancy flag
- Initial receiving notes

Optional checklist:

- Manuals
- Certificates
- Accessories
- Software/media/license
- Packing list

### Phase 7 — Installation

Fields:

- Installation date
- Installed by (vendor/internal)
- Installation report reference
- Site readiness confirmed
- Utilities confirmed
- Network / software installed
- Initial configuration notes

### Phase 8 — IQ

Fields:

- IQ protocol reference
- IQ execution date
- IQ result: Pass / Fail / Conditional
- IQ report reference
- IQ approval / closure date
- Deviations / notes

### Phase 9 — OQ

Same structure as IQ:

- OQ protocol
- OQ execution date
- OQ result
- OQ report
- Closure date
- Notes / deviations

### Phase 10 — PQ

Same structure:

- PQ protocol
- PQ execution date
- PQ result
- PQ report
- Closure date
- Notes / deviations

### Phase 11 — Release / Issuance

Fields:

- Issuance / release date
- Released to department
- Release reference
- Released / approved by
- Operational status after release
- SOP availability confirmed
- User training readiness confirmed

### Phase 12 — First Run

Fields:

- First approved / routine run date
- First method / use
- Performed by
- Initial performance comment
- Early issue observed? Yes/No
- Related event reference if applicable

### Phase 13 — Routine Operation

This is not a single completion event; it is the long-running operational state.

Display:

- Instrument ID
- Instrument type
- Manufacturer / model / serial
- Location
- Responsible team / owner
- Current status
- Software / firmware version (optional)
- Last calibration
- Next calibration
- Last PM
- Next PM
- Last qualification / next qualification
- Open events count
- Health score

### Phase 14 — Calibration / PM / Requalification / Components

Existing modules remain, but unify them under one operational control area.

Calibration must support:

- Calibration ID
- Performed date
- Next due
- Result
- As-found result
- As-left result
- Certificate reference
- Report reference
- Raw data reference
- SOP / procedure reference
- Acceptance criteria
- Standards used
- Traceability reference
- Internal/external provider
- Accreditation body / number
- Scope confirmed
- OOC status
- Impact assessment
- Investigation / deviation / CAPA references

Preventive maintenance must support:

- PM type
- Work order
- Date
- Provider
- Actions performed
- Parts replaced
- Result
- Next due
- Notes

Requalification should use lifecycle records with type IQ/OQ/PQ/Requalification as appropriate.

Components must support installed date, replacement due, status, part number, serial number, and history.

### Phase 15 — Events & Investigation

Event types should include:

- Breakdown
- Failure
- Alarm
- Out of Calibration
- Service Visit
- Unexpected Instrument Behavior
- Component Failure
- Data Integrity Concern
- Qualification Failure
- Other

Capture:

- What happened?
- When?
- Instrument state at time of event
- Observed facts
- Immediate action
- Was calibration valid?
- Was PM overdue?
- Recent component changes?
- Potentially affected results / products / batches
- Investigation reference
- Root cause status

Investigation Intelligence must show context from the instrument history, but label patterns as patterns, not confirmed causes.

### Phase 16 — Periodic Performance Review

Add a review module that calculates and displays a period summary, for example last 12 months:

- Calibration compliance %
- PM compliance %
- Number of failures
- Number of repeat subsystem events
- Downtime estimate (if available)
- Number of OOC events
- Components replaced
- Open investigations
- Health score trend

User decision field:

- Continue as-is
- Increased monitoring
- Major maintenance / upgrade
- Replacement planning
- Retirement recommended

### Phase 17 — Retirement / Decommission

Fields:

- Retirement request date
- Retirement reason
- Replacement instrument (optional)
- Retirement approval date
- Decommission date
- Final status
- Data archive completed
- User/access accounts disabled
- Software/data backup completed
- Calibration/qualification labels removed or voided
- Disposal / transfer method
- Disposal reference
- Final notes

Once retired, the instrument should remain searchable/history-visible but should not appear in normal active workload metrics.

---

## 6. New database design

Do not overload the `instruments` table with every lifecycle event. Keep stable identity fields in `instruments` and place process history in dedicated tables.

Recommended schema additions:

### `instrument_lifecycle_milestones`

Columns:

- id uuid PK
- user_id uuid
- instrument_id uuid FK
- phase_code text
- status text
- reference_no text
- planned_date date
- completed_date date
- result text
- evidence_reference text
- notes text
- created_at
- updated_at

Unique recommendation:

`(user_id, instrument_id, phase_code, id)` — allow repeated requalification milestones where needed; do not force only one historical row globally.

### `instrument_need_requests`

Store initiation/business need fields.

### `instrument_vendor_quotes`

Allow multiple vendor quotations per instrument/request, with one selected quote.

### `instrument_retirements`

Store retirement/decommission evidence and closure status.

### `instrument_performance_reviews`

Store periodic reviews and management decisions.

Keep existing:

- instruments
- instrument_events
- investigations
- maintenance_records
- lifecycle_records
- instrument_components
- calibration_records

Every new table must include `user_id`, FK ownership, RLS enabled, and CRUD policies that enforce `auth.uid() = user_id` and verify parent instrument ownership.

---

## 7. Lifecycle intelligence rules

Implement a rule engine that creates user-facing signals, not hidden automatic conclusions.

Examples:

- URS approved but no quotation after X days → "Procurement not progressed"
- PR approved but PO missing → "PO pending"
- Expected receiving date passed and receiving date missing → "Receiving overdue"
- Receiving completed but installation not started → "Installation pending"
- IQ pass but OQ missing → "OQ is the next controlled milestone"
- OQ pass but PQ missing → "PQ pending"
- PQ pass but issuance/release missing → "Instrument not yet released for routine use"
- First run recorded before PQ completion → chronology warning
- Calibration overdue → operational compliance signal
- OOC calibration → mandatory impact assessment queue
- PM overdue + related failure occurs → show as a **potential contributing condition**, not root cause
- Repeated subsystem events within 90 days → recurrence signal
- Retirement recommended but instrument remains Active → management attention signal

Every signal should include:

- What triggered it
- Evidence used
- Recommended next action
- Confidence wording where inference is involved

---

## 8. Instrument Health Score v3

Keep health scoring transparent and explainable.

Inputs may include:

- Operational status
- Calibration overdue / due soon
- PM overdue / due soon
- Qualification overdue
- Open Critical/High events
- Open OOC
- Repeated failures
- Overdue component replacement
- Unclosed qualification deviations
- Incomplete release evidence

Never produce a score without an explanation list.

The UI should show:

- Score
- State: Healthy / Attention / At Risk / Critical
- Top 3 reasons
- Best next action

---

## 9. Dashboard design details

### Lifecycle distribution card

Show counts by lifecycle macro-phase:

- Planning
- Procurement
- Qualification
- Active Operation
- Under Investigation
- Retirement

### Action queue

Sort by urgency:

1. Critical/OOC/open high-risk issue
2. Calibration/qualification overdue
3. PM overdue
4. Expected receipt overdue
5. Due within 30 days
6. Missing next lifecycle milestone

### Instrument cards

On mobile, prefer cards over wide tables. Each card should show:

- Instrument ID + name
- Type
- Current lifecycle phase
- Health badge
- Next due action
- One-tap "Open Passport"

---

## 10. Instrument Passport redesign

Create sections:

- Identity
- Lifecycle status
- Acquisition summary
- Qualification summary
- Calibration / PM status
- Components
- Open events
- Investigation history
- Documents / references
- Retirement status

Add a compact lifecycle timeline on each passport.

QR passport remains available, but QR should identify/open the instrument record only; do not encode sensitive database data directly inside the QR payload.

---

## 11. Reports module

Add export-ready views:

- Instrument master list
- Calibration due / overdue report
- PM due / overdue report
- Qualification due report
- Open OOC report
- Open events report
- Lifecycle stage report
- Procurement / receiving delay report
- Retirement list

For the MVP, CSV/XLSX export is sufficient. Clearly label exports as decision-support outputs rather than validated official records.

---

## 12. Welcome, guide, importance, CTA

### Welcome block

Use the signed-in user's display name when available.

Suggested copy:

> Welcome back. Every instrument has a history. This app turns that history into visible evidence, due-date control, and better laboratory decisions.

### Why this application matters

Explain briefly:

- Instrument decisions affect data reliability.
- A due date alone is not instrument control.
- Lifecycle history links procurement, qualification, calibration, maintenance, failures, and investigations.
- Better context reduces guessing and repeated troubleshooting.

### Quick guide

Keep a concise bilingual guide, with correct Arabic RTL.

### CTA logic

CTA should change by context:

- No instruments → "Add your first instrument / need"
- Acquisition incomplete → "Continue lifecycle"
- Overdue calibration → "Review calibration control"
- Open event → "Review evidence / start investigation"
- Healthy portfolio → "Review upcoming 30-day actions"

Keep external CTA to Yahia HPLC Investigation Assistant for HPLC troubleshooting.

---

## 13. File/module architecture target

Refactor progressively; avoid a single giant Streamlit file.

Suggested structure:

```text
app.py
instrument_supabase_app.py
modules/
  dashboard.py
  lifecycle.py
  passport.py
  calibration_pm.py
  events.py
  investigation.py
  reports.py
  guide.py
services/
  supabase_client.py
  lifecycle_engine.py
  health_score.py
  auth.py
assets/
  instrument_lifecycle_hero.png
migrations/
  v03_full_lifecycle.sql
```

Do not break the persistent-auth wrapper until auth behavior is covered by a regression test/checklist.

---

## 14. Migration strategy

Implement v0.3 in safe increments:

### Migration A — schema

Create new lifecycle/need/quote/performance-review/retirement tables with RLS and indexes.

### Migration B — compatibility

Read current acquisition fields already stored on `instruments` and display them in the new Lifecycle module. Do not delete legacy fields during first release.

### Migration C — optional backfill

Backfill existing URS/quotation/PR/PO/receiving/IQ/OQ/PQ/first-run values into lifecycle milestone rows only after verifying mapping.

### Migration D — deprecate legacy UI

After successful validation, stop writing new data into redundant legacy fields. Keep read compatibility until migration is confirmed.

No destructive migration in the first v0.3 deployment.

---

## 15. Acceptance criteria

v0.3 is acceptable only when all of the following are true:

1. Existing users remain logged in after normal refresh/reboot.
2. Account A cannot see Account B lifecycle, calibration, event, or retirement data.
3. Existing HPLC-001 / GC-001 test data remains accessible to its correct owner.
4. The complete lifecycle can be followed from Need to Retirement.
5. Current phase and next action are calculated correctly from recorded evidence.
6. A future date alone does not mark a milestone complete.
7. OOC calibration produces a visible impact-assessment action.
8. Retirement removes the instrument from Active portfolio counts but keeps history visible.
9. Mobile layout works without clipped core navigation labels.
10. Arabic guide text is RTL and English text remains LTR.
11. Background imagery never reduces form readability.
12. Health score provides reasons, not just a number.
13. Investigation Intelligence uses historical context without declaring unsupported root cause.
14. RLS is enabled on every new user-data table.
15. Supabase security advisor is checked after migrations and material findings are remediated.

---

## 16. Regression test scenarios

Run these before calling v0.3 stable:

- Create a new Need and move through URS → Quote → PR → PO.
- Record expected receiving date in the past without actual receipt; confirm overdue signal.
- Record receiving → installation → IQ pass → OQ pass → PQ pass → release → first run.
- Attempt first run before PQ; confirm chronology warning.
- Add calibration with next due; confirm dashboard and passport update.
- Record OOC calibration; confirm impact assessment queue.
- Add PM record and component replacement.
- Create repeated subsystem events and confirm recurrence signal.
- Sign in as second user and verify total isolation.
- Retire an instrument; verify history remains and active KPI drops.
- Refresh and reboot; verify login and data persist.

---

## 17. Delivery sequence

Recommended implementation order:

**Sprint 1 — Foundation & UI**

- Hero background asset integration
- Dashboard redesign
- New navigation
- Lifecycle navigator shell

**Sprint 2 — Full lifecycle data**

- Need through First Run
- Migrations + RLS
- Lifecycle progress and next-action engine

**Sprint 3 — Operational control**

- Calibration Control Center
- PM/Requalification/Components
- OOC impact workflow

**Sprint 4 — Intelligence**

- Health Score v3
- History-linked Investigation Intelligence
- Performance Review

**Sprint 5 — Closure & reporting**

- Retirement/Decommission
- Reports/exports
- Mobile polish
- Security + regression review

---

## 18. Coding-agent execution prompt

Use the following instruction when handing this spec to a coding agent:

> Implement `V03_IMPLEMENTATION_SPEC.md` on branch `instrument-lifecycle-standalone` incrementally without breaking existing authentication, encrypted persistent cookies, Supabase RLS, or current user data. Inspect the current application before editing. Use non-destructive migrations. Keep existing modules functional during transition. Prioritize mobile-first UI and a complete lifecycle navigator from Need through Retirement. After each schema change, verify RLS and ownership policies. After each UI change, preserve Streamlit stability and current login/session behavior. Do not infer GxP completion states without recorded evidence. Do not present historical patterns as confirmed root causes. Deliver changes in small, reviewable commits and include a concise validation checklist with each major commit.

---

## 19. Final product message

The v0.3 experience should communicate one idea clearly:

> **An instrument is not a record. It is a lifecycle.**
>
> From the first need, through qualification and routine control, to investigation and retirement — every important decision should be connected to the evidence that came before it.
>
> **DON’T GUESS. FOLLOW THE EVIDENCE.**

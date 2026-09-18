# Yahia HPLC Investigation Assistant — Verified Evidence Map

This document defines how external sources are used inside the assistant.

## Principle
**Case evidence comes first. Literature supports hypotheses; it does not prove the user's root cause.**

The assistant must never convert a vendor troubleshooting example or a general guideline into a case-specific conclusion without a discriminating test.

---

## Source hierarchy

### Tier A — Regulatory / compendial / harmonized guidance
Use primarily for GMP, system-suitability, analytical-procedure, validation, lifecycle, and documentation guardrails.

#### U.S. FDA
Source: *Investigating Out-of-Specification (OOS) Test Results for Pharmaceutical Production*.
Role in the assistant:
- preserve original results and investigation trail;
- avoid repeated testing simply to obtain a passing result;
- require evidence before assigning laboratory error;
- support documented, scientifically sound investigation behavior.

Evidence card: `FDA-OOS-12`

#### USP
Source: *USP <621> Chromatography*.
Role in the assistant:
- system-suitability concepts;
- chromatographic definitions and calculations;
- reminder that method-specific requirements and permitted adjustments must be checked in the applicable current chapter/monograph/procedure.

Evidence card: `USP-621-11`

#### ICH
Sources: Q2(R2) Validation of Analytical Procedures and Q14 Analytical Procedure Development.
Role in the assistant:
- analytical procedure lifecycle;
- scientific/risk-based consideration of method changes;
- distinction between diagnostic troubleshooting and validated routine analytical conditions.

Evidence card: `ICH-Q2Q14-13`

---

### Tier B — Manufacturer technical troubleshooting
Use for documented chromatographic mechanisms, symptom patterns, and discriminating troubleshooting approaches. These are not universal rules.

#### Waters
Current cards:
- `WATERS-PEAK-SHAPE-01` — peak-shape localization; all peaks vs selected peaks; guard-column example.
- `WATERS-CONNECTION-02` — extra-column dead volume / poor column connection example.
- `WATERS-AIR-06` — air bubbles can affect area, peak shape, RT, baseline, and pressure.

#### Agilent
Current card:
- `AGILENT-TROUBLESHOOT-03` — symptom-first troubleshooting categories: pressure, peak shape, retention/resolution, baseline.

#### Shimadzu
Current cards:
- `SHIMADZU-HIGH-PRESSURE-04` — separable high-pressure mechanisms.
- `SHIMADZU-CARRYOVER-08` — classic decaying carryover versus constant contamination behavior.
- `SHIMADZU-RT-14` — using combinations of changed/stable chromatographic metrics to localize problems.

#### Thermo Fisher Scientific
Current cards:
- `THERMO-RETENTION-05` — varying-retention mechanisms including equilibration, flow delivery, temperature, dwell volume, leaks, and air.
- `THERMO-AREA-PRECISION-07` — peak-area precision contributors.
- `THERMO-GHOST-09` — chemical contamination versus detector-setting possibilities for ghost peaks.
- `THERMO-BASELINE-10` — blank-based localization and baseline contamination/equilibration principles.

---

## Retrieval behavior
The application does not send the entire knowledge base with every API call.

`evidence_engine.py` performs lightweight local retrieval using:
- current investigation area;
- recent user messages;
- bilingual Arabic/English keywords;
- special regulatory triggers such as OOS, OOT, GMP, SOP, QA, investigation, and retesting.

Maximum default retrieval: **4 evidence cards per turn**.

Benefits:
- lower API token cost;
- less irrelevant context;
- reduced risk of forcing a generic source onto the wrong case;
- easier auditing of which source families can influence a response.

---

## Citation rules inside the assistant
1. Cite only evidence cards provided to the current model turn.
2. Preserve the exact evidence-card ID and source name.
3. Never invent page numbers, quotations, limits, acceptance criteria, or URLs.
4. A source citation may support a mechanism or test choice, but it does not change the root-cause confirmation standard.
5. Regulatory/compendial references never replace the laboratory's current approved SOP, applicable monograph, QA requirements, or manufacturer instructions.
6. If no card matches, the assistant should continue evidence-first reasoning without fabricating a reference.

---

## Current knowledge-base coverage
- Pressure: covered
- Retention time: covered
- Peak shape: covered
- Baseline: covered
- Carryover / ghost peaks: covered
- Peak-area precision: covered
- System suitability / chromatography framework: covered
- OOS / GMP investigation guardrails: covered
- Analytical procedure validation/lifecycle: covered

## Planned expansion
Next evidence modules should add:
1. injection solvent / injection-volume effects;
2. detector response and wavelength/acquisition diagnostics;
3. column care, washing, storage, and compatibility by chemistry;
4. HILIC-specific troubleshooting;
5. gradient dwell-volume and method-transfer evidence;
6. sample filtration / adsorption / extractables evidence;
7. autosampler precision and carryover isolation;
8. SST interpretation without testing-to-compliance.

Every new card should have a source URL, a concise evidence summary, a guardrail, bilingual retrieval keywords, and at least one validation case that challenges its misuse.

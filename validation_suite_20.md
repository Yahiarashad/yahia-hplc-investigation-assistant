# Yahia HPLC Investigation Assistant — 20-Case Validation Suite

Purpose: stress-test the assistant across different HPLC failure patterns while preserving the rule: **DON'T GUESS. FOLLOW THE EVIDENCE.**

## Status key
- LIVE PASS = tested interactively with a real user case.
- BLIND READY = synthetic challenge case prepared for future testing; not claimed to be a real laboratory event.

## Global pass rules
For every case, the assistant should:
1. Keep reported facts separate from inference.
2. Ask 1–2 high-value questions before broad checklists.
3. Use a change-delta check when a prior acceptable run exists.
4. Prefer one discriminating test at a time.
5. Preserve original data and GMP investigation logic.
6. Avoid testing-to-compliance behavior.
7. Confirm root cause only after a targeted intervention/test changes the symptom as predicted and competing explanations are materially weakened.

---

## Case 01 — Early distorted peak + resolution loss
Status: **LIVE PASS — 12/12**
Challenge: expected RT about 6 min becomes about 3 min; distorted main peak; resolution falls from NLT 4 to about 2.
Key behavior: compare last-known-good state and system/method equivalence; do not blame column or mobile phase prematurely.

## Case 02 — Selective broadening of low-concentration API
Status: **LIVE PASS — 12/12**
Challenge: one low-concentration API becomes broad while the second API remains normal.
Key behavior: use unaffected analyte as comparative evidence, not proof of system health; distinguish analyte-specific from system-wide causes.

## Case 03 — Three preservatives show lower repeated responses
Status: **LIVE PASS — 11/12**
Challenge: three preservative results shift from about 5/10/15% to about 4/6/12%.
Key learning: assistant should ask early what changed since the last acceptable analysis. This generated the v0.6 Change-Delta Check rule.

---

## Case 04 — Sudden high pressure at the first injection
Status: **BLIND READY**
Scenario: the method usually runs at about 170 bar. After setup today, pressure is immediately about 320 bar before any sample sequence history exists.
Expected first move: determine whether the pressure is already high with the column disconnected/bypassed or whether restriction is downstream of the injector/column path, following approved procedures.
Forbidden leap: “the column is blocked.”
Pass signal: localizes restriction with a controlled path test before recommending replacement.

## Case 05 — Pressure rises progressively through the sequence
Status: **BLIND READY**
Scenario: pressure begins near the historical value, then rises steadily over many injections while sample matrix is complex.
Expected first move: verify the actual pressure trend and identify whether the rise correlates with sample injections versus blanks/standards.
Forbidden leap: “pump failure.”
Pass signal: distinguishes progressive fouling/restriction patterns from sudden hardware failure without assuming either.

## Case 06 — Low pressure plus delayed retention times
Status: **BLIND READY**
Scenario: system pressure is lower than historical and all main peaks elute later than historical, with the same programmed flow setting.
Expected first move: verify actual delivered flow/leaks rather than trusting the setpoint alone.
Forbidden leap: “mobile phase is weaker.”
Pass signal: recognizes that low actual flow could explain both observations but requires measurement/confirmation.

## Case 07 — All peaks shift earlier after transfer to another LC system
Status: **BLIND READY**
Scenario: the same gradient method is transferred to another HPLC/UHPLC system and all peaks shift earlier, while peak order remains unchanged.
Expected first move: compare actual flow, dwell/system volume, gradient delivery, and method implementation between systems.
Forbidden leap: “column chemistry changed.”
Pass signal: treats cross-system configuration as a high-value delta and does not alter chemistry first.

## Case 08 — One ionizable analyte shifts; neutral analytes do not
Status: **BLIND READY**
Scenario: in a multicomponent method, one ionizable analyte changes RT while neutral analytes remain stable.
Expected first move: compare mobile-phase pH/buffer preparation and analyte-specific behavior while keeping detector/processing possibilities open.
Forbidden leap: “pump is unstable.”
Pass signal: uses selective RT behavior to favor analyte-specific chemistry hypotheses without declaring them confirmed.

## Case 09 — Split peak appears only at high injection volume
Status: **BLIND READY**
Scenario: a standard gives one sharp peak at a smaller injection volume but a split/distorted peak at a larger volume; RT region is unchanged.
Expected first move: treat injection volume/sample solvent mismatch or overload as testable hypotheses and compare under a single controlled condition.
Forbidden leap: “column void.”
Pass signal: recognizes injection-condition dependence and avoids changing column/mobile phase simultaneously.

## Case 10 — Basic analytes tail while neutral analytes remain symmetric
Status: **BLIND READY**
Scenario: only basic compounds show increased tailing; neutral compounds remain close to historical symmetry.
Expected first move: ask about pH/buffer/stationary-phase history and compare analyte classes.
Forbidden leap: “all column performance is bad.”
Pass signal: uses selective chemical behavior as evidence, but still requires a discriminating confirmation.

## Case 11 — All peaks broaden after the column was removed and reinstalled
Status: **BLIND READY**
Scenario: RT and area remain near historical values, but all peaks are broader after reconnection of a previously acceptable column.
Expected first move: inspect/reseat column connections according to approved procedure before replacing the column.
Forbidden leap: “stationary phase degraded.”
Pass signal: identifies extra-column dead volume/connection as a high-value hypothesis based on the change delta.

## Case 12 — Baseline drift starts after fresh mobile phase installation
Status: **BLIND READY**
Scenario: baseline was stable before solvent replacement; after fresh mobile phase installation it drifts, while pressure is stable.
Expected first move: compare equilibration, solvent preparation/composition, detector warm-up, and blank behavior.
Forbidden leap: “detector lamp is failing.”
Pass signal: uses a blank/equilibration check to discriminate chemical/background causes from detector failure.

## Case 13 — Repeating baseline spikes at irregular intervals
Status: **BLIND READY**
Scenario: chromatograms contain intermittent sharp spikes, but RT and system pressure are mostly stable.
Expected first move: establish whether spikes appear in blank runs and whether they coincide with detector/solvent/system events.
Forbidden leap: “electrical noise” without evidence.
Pass signal: localizes whether the event is chemical, detector/electrical, or flow-related before changing components.

## Case 14 — Peak appears in every blank and does not decay
Status: **BLIND READY**
Scenario: a small peak appears in every blank at nearly constant area, including before high-concentration sample injections.
Expected first move: question whether this is true carryover; prepare/compare a fresh blank or different blank source under controlled conditions.
Forbidden leap: “autosampler carryover.”
Pass signal: recognizes constant contamination pattern as different from classic carryover.

## Case 15 — Blank peak decays across consecutive blanks after a high sample
Status: **BLIND READY**
Scenario: after a high-concentration injection, a matching peak appears in the first blank and becomes progressively smaller in subsequent blanks.
Expected first move: classify the decay pattern and isolate needle/loop/injector versus column contributions with one controlled test.
Forbidden leap: “column memory effect.”
Pass signal: uses the decay pattern as evidence of classic carryover while preserving multiple possible locations.

## Case 16 — Peak areas vary together while RT and shape remain stable
Status: **BLIND READY**
Scenario: repeated standard injections show poor area repeatability for all analytes in roughly the same direction; RT and peak shape remain stable.
Expected first move: determine random versus sequential response behavior and compare injection precision/detector response/common-mode sample delivery.
Forbidden leap: “standard unstable.”
Pass signal: identifies common-mode response problem and avoids analyte-specific explanations without evidence.

## Case 17 — One standard analyte response decreases with autosampler time
Status: **BLIND READY**
Scenario: one analyte area decreases progressively across hours while the other standard components remain stable; RT remains constant.
Expected first move: compare solution age/autosampler time, analyte stability, vial/adsorption behavior, and detector selectivity using an approved stability/comparator approach.
Forbidden leap: “detector sensitivity is dropping.”
Pass signal: recognizes analyte-selective time dependence and asks for a time-linked comparator.

## Case 18 — Resolution falls while individual RTs move only slightly
Status: **BLIND READY**
Scenario: two critical peaks remain near their expected retention region but move closer together and resolution fails.
Expected first move: compare selectivity-related deltas such as mobile-phase composition/pH, temperature, column chemistry/history, and gradient implementation rather than focusing only on absolute RT.
Forbidden leap: “increase run time” as a root-cause solution.
Pass signal: treats resolution as a relationship between peaks and investigates selectivity/efficiency evidence.

## Case 19 — Pressure fluctuates and RT jitters run-to-run
Status: **BLIND READY**
Scenario: pressure oscillates more than historical and all peaks show small inconsistent RT changes.
Expected first move: look for common flow-delivery instability evidence such as bubbles, pump/check-valve behavior, leaks, or solvent-line restrictions using one discriminating observation/test.
Forbidden leap: “air bubble” as a confirmed cause.
Pass signal: connects common pressure/RT instability to flow delivery while requiring direct confirmation.

## Case 20 — Calculated assay changes after processing-method update, raw chromatograms look unchanged
Status: **BLIND READY**
Scenario: same raw chromatograms produce different reported assay values after a processing/integration method was edited; peak areas/integration boundaries or calculation settings may differ.
Expected first move: compare raw data and processing/calculation parameters before reinjection or changing chromatography.
Forbidden leap: “instrument problem.”
Pass signal: localizes the issue to data processing when supported and preserves audit trail/original results.

---

# Scoring rubric
Score each category 0–2:
1. Evidence discipline
2. Diagnostic value
3. Root-cause restraint
4. One-variable logic
5. GMP/data-integrity logic
6. Clarity

Maximum: 12. Suggested pass threshold: 10/12, with no zero in Evidence discipline, Root-cause restraint, or GMP/data-integrity logic.

# Current summary
- Live-tested: 3/20
- Live pass: 3/3
- Blind-ready challenge cases: 17
- Next validation target: Cases 04–06, because together they test high pressure, low pressure, and flow/retention coupling.

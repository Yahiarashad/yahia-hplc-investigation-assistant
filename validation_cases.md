# Yahia HPLC Investigation Assistant — Validation Suite v0.1

Purpose: test whether the assistant follows evidence before diagnosis.

Core pass rule for every case:
- Separate reported facts from inference.
- Ask only high-value questions that materially reduce uncertainty.
- Do not jump to a root cause.
- Prefer one discriminating test at a time.
- Preserve GMP/data-integrity logic.
- Do not recommend repeated trial-and-error injections just to obtain a passing result.

---

## CASE 01 — AMT: Early Distorted Main Peak + Resolution Loss

### User case
A new AMT product has an expected main peak RT around 6 minutes. The required resolution between the main peak and a secondary peak is NLT 4. The attached reference chromatogram shows a sharp main peak. In the current work, two different mobile phases were injected, but the main peak appears distorted around 3 minutes and resolution is about 2.

### Reported facts
- Product: AMT, new product/method context.
- Expected main-peak RT: about 6 min.
- Current observed main-peak RT: about 3 min.
- Expected reference peak shape: sharp.
- Current main peak: distorted.
- Required resolution main vs secondary peak: NLT 4.
- Current resolution: about 2.
- Two different mobile phases were tried.

### Critical unknowns
- What exactly differs between the two mobile phases and the approved/reference mobile phase?
- Are flow, column chemistry/dimensions, temperature, gradient/isocratic program, injection volume, diluent, wavelength, and system configuration confirmed against the method?
- Is the distorted peak seen in standard, sample, or both?
- Is the RT shift reproducible across injections?
- Was the same column used as in the reference method and is its orientation/history known?

### Expected first diagnostic behavior
The assistant should first recognize a major selectivity/retention mismatch rather than treating this as only a peak-shape problem.

High-value first questions should focus on confirming method/system equivalence and whether the phenomenon is standard-specific or universal.

### Forbidden premature conclusions
- "The column is bad."
- "The mobile phase is wrong."
- "The pump is faulty."
- "The method is not robust."
- "Replace the column."

### Pass criteria
PASS if the assistant:
1. States that RT ≈3 min vs expected ≈6 min is a major observed retention shift.
2. Keeps the distorted peak and resolution ≈2 as separate observed failures.
3. Does not infer a progressive trend or any unreported history.
4. Requests confirmation of the highest-value method/system variables before recommending changes.
5. Avoids naming a root cause without evidence.

### Blind test result — PASS (v0.5)
Observed investigation path during live testing:
- The assistant preserved the initial facts without inventing history or trend.
- It treated the RT shift, distorted peak, and resolution loss as separate observations.
- After two independently prepared mobile phases produced the same failure, it reduced support for a preparation-specific explanation without declaring a root cause.
- A cross-system comparison using the same sample/reference conditions showed the method passed on an Alliance system while failing on the ARC system, strongly localizing the issue to the ARC system/path rather than the sample, mobile phase, method, or column alone.
- The assistant then requested a discriminating check of actual flow and pressure rather than recommending immediate replacement of the column or method changes.
- The reported ARC actual flow and system pressure were approximately double the Alliance values under the same method conditions, while RT on ARC was approximately 3 min vs approximately 6 min on Alliance.
- The assistant connected the observed near-doubling of flow with the observed near-halving of RT, but still kept the conclusion provisional pending correction and confirmatory rerun.
- It recommended preserving chromatograms, instrument records, SST/investigation evidence, and following approved SOP/QA requirements.

### Case 01 score
- Evidence discipline: 2/2
- Diagnostic value: 2/2
- Root-cause restraint: 2/2
- One-variable logic: 2/2
- GMP / data-integrity logic: 2/2
- Clarity: 2/2

**Total: 12/12 — PASS**

### v0.5 UX checks during Case 01
- Arabic RTL rendering and mixed Arabic/English technical terminology: PASS
- Response readability on mobile: PASS
- Conversation persistence after accidental refresh: PASS

---

## CASE 02 — Selective Peak Broadening in a Two-API Product

### User case
A product contains two active ingredients. The lower-concentration API peak became broad, while the higher-concentration API peak retained its usual shape.

### Reported facts
- Two active ingredients are present.
- The lower-concentration API peak is now broad.
- The higher-concentration API peak remains normal in shape.
- The broadening is therefore selective, not reported as a global chromatogram-wide broadening phenomenon.

### Critical unknowns
- Is the lower-API RT still normal or has it shifted?
- Is the broadening present in standard, sample, or both?
- Did it appear suddenly or develop over a sequence?
- Is the low-concentration peak approaching the method's practical S/N or integration limits?
- Are both analytes detected under identical detector settings/wavelength conditions?
- Are diluent, injection volume, concentration, and sample/standard preparation unchanged?

### Expected first diagnostic behavior
The assistant should explicitly use the normal shape of the second API as evidence that the problem may be analyte-specific rather than automatically system-wide.

The next question/test should discriminate between:
- analyte-specific/sample/diluent effects,
- concentration/S:N/integration behavior,
- chromatographic interaction/selectivity,
- versus a broader hardware/system problem.

### Forbidden premature conclusions
- "The column is deteriorated."
- "The detector is faulty."
- "It is only because the API concentration is low."
- "The system is fine because the other peak is normal."

### Pass criteria
PASS if the assistant:
1. Recognizes the selective nature of the broadening.
2. Uses the unaffected API as comparative evidence, not proof of system health.
3. Asks whether standard/sample and RT are affected.
4. Does not equate low concentration with root cause.
5. Chooses a discriminating next step rather than multiple simultaneous changes.

### Blind test result — PASS (v0.5)
Observed investigation path during live testing:
- The assistant immediately treated the broadening as selective rather than as a universal chromatographic failure.
- It first asked whether the same broadening appeared in the standard or only in the sample, then used the repeated broadening in the standard as evidence against a sample-preparation-only explanation.
- It requested comparison with historical standard/SST chromatograms and asked whether RT or only peak width/shape had changed.
- The reported RT remained unchanged, historical chromatograms showed a sharp peak, repeat preparation did not restore the shape, mobile-phase pH was verified, and the method used a guard column.
- From those facts, the assistant kept multiple hypotheses open and did not claim that low concentration itself was the root cause.
- It proposed an isolated guard-column intervention as a discriminating test while explicitly avoiding simultaneous changes to the analytical column or mobile phase.
- When the user asked whether the guard column could be washed instead of replaced, the assistant correctly conditioned that action on the approved SOP and manufacturer instructions and explained how to interpret the result.
- After guard-column washing/reconditioning restored the sharp peak and the improvement persisted through the sequence, the assistant classified the guard column as a strongly supported probable cause rather than an absolutely confirmed contamination source.
- It distinguished evidence that the guard column was involved from evidence about the exact contamination/obstruction mechanism, and requested history/documentation before stronger attribution.
- It preserved GMP/data-integrity logic by asking for before/after chromatograms, wash details, SST/sequence results, and SOP/QA documentation where applicable.

### Case 02 score
- Evidence discipline: 2/2
- Diagnostic value: 2/2
- Root-cause restraint: 2/2
- One-variable logic: 2/2
- GMP / data-integrity logic: 2/2
- Clarity: 2/2

**Total: 12/12 — PASS**

---

## CASE 03 — Three Preservatives: Repeated Standard Injections Give Changing Results

### User case
A product contains three preservatives whose assay is tested by HPLC. On repeated injections of the same standard, the three reported values change. Example: instead of approximately 5%, 10%, and 15%, they become approximately 4%, 6%, and 12%.

### Reported facts
- Three preservative analytes are measured in the same method.
- Repeated injections of the standard do not give stable reported values.
- Example reported values change from 5/10/15% to 4/6/12%.
- All three analytes change, but not by the same relative amount.
- The second reported value shows the largest relative decrease in the given example.

### Critical unknowns
- Are 5/10/15 and 4/6/12 Peak Areas, Area Ratios, calculated assay results, or another reported metric?
- Is the change monotonic with injection order or random?
- Are the same standard vial and same preparation used for all injections?
- Are all three analytes measured at the same wavelength/detector settings?
- Is an internal standard used?
- Do RT, peak shape, baseline, and pressure remain stable while the response changes?
- Is the standard solution known to be stable for the elapsed autosampler time and temperature?

### Expected first diagnostic behavior
The assistant should recognize this first as a repeatability/reproducibility-of-response problem in repeated standard injections, while keeping open whether the source is common-mode or analyte-specific.

The first diagnostic move should clarify what metric is changing and whether the change follows injection order.

### Forbidden premature conclusions
- "The injector is faulty."
- "The standard is unstable."
- "The detector lamp is failing."
- "The standard preparation is wrong."
- "Prepare a new standard" as the first unqualified action.

### Pass criteria
PASS if the assistant:
1. Clarifies what the changing values actually represent before diagnosing.
2. Asks whether the change is sequential or random.
3. Recognizes that all three analytes are affected but to different extents.
4. Distinguishes common-mode causes from analyte-specific causes.
5. Avoids repeating injections simply to obtain acceptable numbers.
6. Recommends only one high-value discriminating check/test at a time.

---

# Scoring Rubric

Score each case from 0–2 in each category.

## 1. Evidence discipline
- 0: invents or assumes facts.
- 1: mostly evidence-based but mixes some inference into facts.
- 2: cleanly separates reported facts, inference, and unknowns.

## 2. Diagnostic value
- 0: generic troubleshooting list.
- 1: some useful questions but weak prioritization.
- 2: identifies the critical unknown and chooses the highest-value next question/test.

## 3. Root-cause restraint
- 0: declares a cause prematurely.
- 1: suggests causes too strongly without enough support.
- 2: keeps hypotheses provisional until a discriminating test confirms them.

## 4. One-variable logic
- 0: changes several variables at once.
- 1: mostly controlled but still suggests multiple simultaneous actions.
- 2: recommends one controlled, interpretable change/test at a time.

## 5. GMP / data-integrity logic
- 0: recommends retesting to pass, unofficial injections, or evidence-destructive actions.
- 1: neutral but does not protect the investigation trail.
- 2: explicitly preserves evidence and avoids testing-to-compliance behavior.

## 6. Clarity
- 0: confusing or excessively long.
- 1: understandable but not prioritized.
- 2: mobile-first, concise, and clearly ordered.

Maximum score per case: 12
Suggested pass threshold: 10/12 with no score of 0 in Evidence discipline, Root-cause restraint, or GMP/data-integrity logic.

---

# Validation Status

- Case 01: **PASS — 12/12 (v0.5 live test)**
- Case 02: **PASS — 12/12 (v0.5 live test)**
- Case 03: Ready for blind test

Next step: run Case 03 as a fresh investigation and score it with the same rubric before making any new core-prompt changes.

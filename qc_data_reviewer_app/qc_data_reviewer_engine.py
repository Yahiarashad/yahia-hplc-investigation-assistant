from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
import numpy as np


@dataclass
class Finding:
    severity: str
    category: str
    observation: str
    why_it_matters: str
    check: str
    decision: str
    evidence: str = "OBSERVED"

    def to_dict(self):
        return asdict(self)


ALIASES = {
    "injection_no": ["injection_no", "injection", "inj", "inj_no", "injection number", "injection #", "vial injection"],
    "injection_type": ["injection_type", "type", "sample type", "injection type", "function"],
    "sample_id": ["sample_id", "sample", "sample name", "sample id", "name", "sample_name"],
    "area": ["area", "peak area", "response", "main peak area", "area response"],
    "rt": ["rt", "retention time", "retention_time", "ret. time", "ret time"],
    "tailing": ["tailing", "tailing factor", "tailing_factor", "symmetry"],
    "plates": ["plates", "theoretical plates", "plate count", "n", "theoretical_plates"],
    "resolution": ["resolution", "rs", "resolution value"],
    "reported_result": ["reported_result", "result", "assay", "assay %", "% assay", "reported result"],
    "replicate_group": ["replicate_group", "replicate", "preparation", "prep", "replicate group"],
}

TYPE_MAP = {
    "STD": "STANDARD",
    "STANDARD": "STANDARD",
    "SYSTEM SUITABILITY": "SST",
    "SYSTEM SUITABILITY STANDARD": "SST",
    "SST": "SST",
    "SAMPLE": "SAMPLE",
    "UNKNOWN": "UNKNOWN",
    "BLANK": "BLANK",
    "DILUENT": "DILUENT",
    "WASH": "WASH",
    "BRACKET": "BRACKET",
    "BRACKETING STANDARD": "BRACKET",
    "BRACKET STD": "BRACKET",
    "BRACKET_STD": "BRACKET",
}


def _norm_header(value: Any) -> str:
    return " ".join(str(value).strip().lower().replace("_", " ").split())


def normalize_columns(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, str]]:
    work = df.copy()
    raw_cols = list(work.columns)
    normalized = {_norm_header(c): c for c in raw_cols}
    rename = {}
    mapping = {}
    for canonical, aliases in ALIASES.items():
        for alias in aliases:
            key = _norm_header(alias)
            if key in normalized:
                original = normalized[key]
                rename[original] = canonical
                mapping[canonical] = str(original)
                break
    work = work.rename(columns=rename)
    return work, mapping


def _safe_numeric(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce")


def _cv_percent(values: pd.Series) -> Optional[float]:
    vals = _safe_numeric(values).dropna()
    if len(vals) < 2 or vals.mean() == 0:
        return None
    return float(vals.std(ddof=1) / vals.mean() * 100)


def _coverage_score(work: pd.DataFrame) -> Tuple[int, List[str]]:
    weighted = {
        "injection_no": 12,
        "injection_type": 12,
        "sample_id": 10,
        "area": 18,
        "rt": 12,
        "tailing": 8,
        "plates": 8,
        "resolution": 8,
        "reported_result": 8,
        "replicate_group": 4,
    }
    available = []
    score = 0
    for col, weight in weighted.items():
        if col in work.columns and not work[col].isna().all():
            score += weight
            available.append(col)
    return min(100, int(score)), available


def review_hplc_assay(df: pd.DataFrame, rules: Dict[str, Any]) -> Dict[str, Any]:
    findings: List[Finding] = []
    work, mapping = normalize_columns(df)

    if work.empty:
        findings.append(Finding(
            "CRITICAL", "Data completeness",
            "The supplied dataset contains no rows.",
            "No analytical review can be performed without sequence data.",
            "Export the original analytical sequence and upload it again.",
            "REVIEW REQUIRED", "MISSING INFORMATION",
        ))
        return _build_summary(findings, 0, mapping, [], work)

    required = ["injection_no", "injection_type", "sample_id"]
    missing = [c for c in required if c not in work.columns]
    if missing:
        findings.append(Finding(
            "CRITICAL", "Data completeness",
            f"Required fields were not identified: {', '.join(missing)}.",
            "The reviewer cannot reliably reconstruct the analytical sequence without core identifiers.",
            "Map or restore the missing fields from the original analytical record/export.",
            "REVIEW REQUIRED", "MISSING INFORMATION",
        ))
        coverage, available = _coverage_score(work)
        return _build_summary(findings, coverage, mapping, available, work)

    work["injection_no"] = _safe_numeric(work["injection_no"])
    if work["injection_no"].isna().any():
        findings.append(Finding(
            "REVIEW", "Data integrity",
            "One or more injection numbers could not be interpreted as numeric values.",
            "Unclear injection numbering can prevent reliable reconstruction of sequence order.",
            "Reconcile injection numbering against the original CDS sequence table.",
            "REVIEW REQUIRED", "MISSING INFORMATION",
        ))

    work["injection_type"] = work["injection_type"].astype(str).str.strip().str.upper()
    work["injection_type"] = work["injection_type"].map(lambda x: TYPE_MAP.get(x, x))
    work["sample_id"] = work["sample_id"].fillna("").astype(str).str.strip()
    work = work.sort_values("injection_no", kind="stable", na_position="last").reset_index(drop=True)

    numeric_inj = work["injection_no"].dropna()
    if numeric_inj.duplicated().any():
        dups = sorted(set(numeric_inj[numeric_inj.duplicated(keep=False)].tolist()))
        findings.append(Finding(
            "REVIEW", "Sequence integrity",
            f"Duplicate injection numbers were identified: {', '.join(str(int(x)) if float(x).is_integer() else str(x) for x in dups[:8])}.",
            "Duplicate sequence positions may indicate export/mapping problems or ambiguous traceability.",
            "Verify sequence numbering against the source CDS record and confirm whether rows represent distinct injections.",
            "REVIEW REQUIRED",
        ))

    if (work["sample_id"] == "").any():
        findings.append(Finding(
            "REVIEW", "Data completeness",
            "One or more injections have a missing sample identifier.",
            "Missing identifiers weaken traceability of the analytical record.",
            "Reconcile injection identifiers against the source record and sequence table.",
            "REVIEW REQUIRED", "MISSING INFORMATION",
        ))

    sample_mask = work["injection_type"].isin(["SAMPLE", "UNKNOWN"])
    sample_positions = np.where(sample_mask)[0]
    sst_mask = work["injection_type"].isin(["SST", "STANDARD"])
    sst_rows = work[sst_mask]

    if len(sample_positions):
        first_sample_pos = int(sample_positions[0])
        prior = work.iloc[:first_sample_pos]
        if not prior["injection_type"].isin(["SST", "STANDARD"]).any():
            findings.append(Finding(
                "CRITICAL", "Sequence integrity",
                "A sample injection appears before any identified SST/standard injection.",
                "Where suitability is required, sample results should not be accepted before suitability evidence is established.",
                "Verify the approved sequence design and confirm whether SST acceptance was established before sample analysis.",
                "REVIEW REQUIRED",
            ))

        if rules.get("require_blank", True) and not prior["injection_type"].eq("BLANK").any():
            findings.append(Finding(
                "REVIEW", "Sequence integrity",
                "No identified blank was found before the first sample injection.",
                "Blank placement may be important for demonstrating absence of interference/carryover, depending on the approved method.",
                "Confirm the method/sequence requirement and review the original blank chromatogram if applicable.",
                "REVIEW REQUIRED",
            ))

    if rules.get("require_bracketing_standard", False):
        if not work["injection_type"].eq("BRACKET").any():
            findings.append(Finding(
                "REVIEW", "Sequence integrity",
                "No identified bracketing standard was found in the supplied sequence.",
                "If bracketing is required, sample quantitation may lack intended evidence of response stability across the sequence.",
                "Check the approved method/SOP and confirm whether a bracketing standard is required.",
                "REVIEW REQUIRED", "MISSING INFORMATION",
            ))

    if len(sst_rows) == 0:
        findings.append(Finding(
            "REVIEW", "System suitability",
            "No injections were identified as STANDARD or SST.",
            "Without identified suitability injections, configured SST checks cannot be evaluated.",
            "Confirm injection-type mapping and the approved method requirements.",
            "REVIEW REQUIRED", "MISSING INFORMATION",
        ))

    if "area" in work.columns:
        initial_std = work[work["injection_type"].isin(["SST", "STANDARD"])]
        trend_std = work[work["injection_type"].isin(["SST", "STANDARD", "BRACKET"])]
        rsd = _cv_percent(initial_std["area"]) if len(initial_std) else None
        if rsd is not None and rsd > float(rules.get("max_standard_area_rsd", 2.0)):
            findings.append(Finding(
                "CRITICAL", "System suitability",
                f"Standard response %RSD is {rsd:.2f}%, above the configured limit of {float(rules.get('max_standard_area_rsd', 2.0)):.2f}%.",
                "Excessive standard response variability can undermine reliability of quantitation.",
                "Review standard preparation, injection repeatability, instrument performance, and the approved SST criteria.",
                "REVIEW REQUIRED",
            ))

        if len(trend_std) >= 4:
            areas = _safe_numeric(trend_std["area"]).dropna()
            if len(areas) >= 4 and areas.iloc[0] != 0:
                drift_pct = float((areas.iloc[-1] - areas.iloc[0]) / areas.iloc[0] * 100)
                if abs(drift_pct) >= float(rules.get("response_drift_alert_pct", 5.0)):
                    direction = "increased" if drift_pct > 0 else "decreased"
                    findings.append(Finding(
                        "REVIEW", "Chromatographic behavior",
                        f"Standard response {direction} by approximately {abs(drift_pct):.2f}% from the first to the last identified standard/bracketing injection.",
                        "A directional response trend can affect confidence in quantitation across the sequence.",
                        "Review sequence timing, standard stability, injection performance, detector response, and other plausible causes. The data alone do not prove injector instability.",
                        "REVIEW REQUIRED", "OBSERVED + INFERRED RISK",
                    ))
    else:
        findings.append(Finding(
            "REVIEW", "Review coverage",
            "Peak area/response data were not identified.",
            "Standard precision and response-trend checks cannot be performed without response data.",
            "Include peak-area/response values in the export if these checks are expected.",
            "REVIEW REQUIRED", "MISSING INFORMATION",
        ))

    for col, rule_key, comparator, label in [
        ("tailing", "max_tailing", "max", "Tailing factor"),
        ("plates", "min_plates", "min", "Theoretical plates"),
        ("resolution", "min_resolution", "min", "Resolution"),
    ]:
        if col in work.columns and rules.get(rule_key) is not None and col in sst_rows.columns:
            vals = _safe_numeric(sst_rows[col]).dropna()
            if len(vals):
                limit = float(rules[rule_key])
                fail = (vals > limit).any() if comparator == "max" else (vals < limit).any()
                if fail:
                    observed = float(vals.max() if comparator == "max" else vals.min())
                    relation = "above" if comparator == "max" else "below"
                    findings.append(Finding(
                        "CRITICAL", "System suitability",
                        f"{label} includes a value of {observed:.3f}, {relation} the configured limit of {limit:.3f}.",
                        "Failure of a required SST criterion can invalidate acceptance of the analytical run.",
                        "Confirm the criterion in the approved method and review the corresponding chromatograms and calculations.",
                        "REVIEW REQUIRED",
                    ))

    if "rt" in work.columns and rules.get("target_rt") is not None:
        target = float(rules["target_rt"])
        tol = float(rules.get("rt_tolerance", 0.2))
        rt_rows = work[~work["injection_type"].isin(["BLANK", "DILUENT", "WASH"])]
        vals = _safe_numeric(rt_rows["rt"]).dropna()
        if len(vals):
            dev = (vals - target).abs()
            if (dev > tol).any():
                worst_idx = dev.idxmax()
                worst = float(vals.loc[worst_idx])
                findings.append(Finding(
                    "REVIEW", "Chromatographic behavior",
                    f"An observed retention time of {worst:.3f} min differs from the configured target {target:.3f} min by more than ±{tol:.3f} min.",
                    "A major RT shift can indicate changed chromatographic conditions, but RT alone does not identify the cause.",
                    "Check method conditions, mobile phase, flow, temperature, column identity/condition, and original chromatograms before drawing a conclusion.",
                    "REVIEW REQUIRED",
                ))

    if "reported_result" in work.columns:
        samples = work[sample_mask].copy()
        samples["reported_result"] = _safe_numeric(samples["reported_result"])
        low = rules.get("spec_low")
        high = rules.get("spec_high")
        if low is not None and high is not None:
            oos = samples[(samples["reported_result"] < float(low)) | (samples["reported_result"] > float(high))]
            for _, row in oos.iterrows():
                findings.append(Finding(
                    "CRITICAL", "Specification compliance",
                    f"Sample {row['sample_id']} has a reported result of {row['reported_result']:.3f}%, outside the configured specification {float(low):.3f}–{float(high):.3f}%.",
                    "An out-of-specification reported result requires controlled handling according to the applicable procedure.",
                    "Verify transcription/calculation and follow the site OOS procedure; do not invalidate or repeat testing without justified, documented evidence.",
                    "REVIEW REQUIRED",
                ))

        if "replicate_group" in samples.columns:
            max_diff = float(rules.get("max_duplicate_difference", 2.0))
            for grp, sub in samples.dropna(subset=["replicate_group"]).groupby("replicate_group"):
                vals = sub["reported_result"].dropna()
                if len(vals) >= 2:
                    diff = float(vals.max() - vals.min())
                    if diff > max_diff:
                        findings.append(Finding(
                            "REVIEW", "Data consistency",
                            f"Replicate group {grp} differs by {diff:.3f} percentage points, above the configured alert threshold of {max_diff:.3f}.",
                            "Poor replicate agreement may indicate preparation, sampling, injection, integration, or other variability that requires review.",
                            "Review the original preparations, injections, chromatograms, and method acceptance criteria before attributing a cause.",
                            "REVIEW REQUIRED",
                        ))
    else:
        findings.append(Finding(
            "REVIEW", "Review coverage",
            "Reported assay results were not identified.",
            "Specification compliance cannot be checked without reported sample results.",
            "Include reported assay results or use a later calculation-verification module.",
            "REVIEW REQUIRED", "MISSING INFORMATION",
        ))

    coverage, available = _coverage_score(work)

    if not findings:
        findings.append(Finding(
            "PASS", "Overall review",
            "No configured rule violations were detected in the supplied dataset.",
            "This means only that the available data passed the configured checks; it is not equivalent to batch approval.",
            "Complete the authorized human review against the approved method, SOPs, chromatograms, audit trail, calculations, and source records.",
            "READY FOR HUMAN REVIEW", "OBSERVED",
        ))

    return _build_summary(findings, coverage, mapping, available, work)


def _build_summary(findings: List[Finding], coverage: int, mapping: Dict[str, str], available: List[str], work: pd.DataFrame) -> Dict[str, Any]:
    critical = sum(f.severity == "CRITICAL" for f in findings)
    review = sum(f.severity == "REVIEW" for f in findings)
    passed = sum(f.severity == "PASS" for f in findings)
    decision = "REVIEW REQUIRED" if (critical or review) else "READY FOR HUMAN REVIEW"
    return {
        "decision": decision,
        "review_coverage": coverage,
        "counts": {"critical": critical, "review": review, "pass": passed},
        "findings": [f.to_dict() for f in findings],
        "column_mapping": mapping,
        "available_fields": available,
        "normalized_data": work,
    }

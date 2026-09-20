import io
from datetime import datetime
import pandas as pd
import streamlit as st
from qc_data_reviewer_engine import review_hplc_assay, normalize_columns

st.set_page_config(page_title="QC Data Reviewer", page_icon="🧪", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
.block-container {padding-top: 1.4rem; padding-bottom: 2rem; max-width: 1200px;}
.qc-hero {background: linear-gradient(135deg,#07111f,#101f36); border:1px solid #b88a2c; border-radius:18px; padding:24px 28px; margin-bottom:18px;}
.qc-hero h1 {color:#f5f7fb; margin:0; font-size:2.05rem;}
.qc-hero p {color:#d7c18a; margin:.45rem 0 0 0; font-size:1.02rem;}
.qc-law {border-left:4px solid #b88a2c; padding:.7rem 1rem; background:rgba(184,138,44,.08); border-radius:8px;}
.small-muted {opacity:.72; font-size:.9rem;}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="qc-hero">
  <h1>🧪 QC DATA REVIEWER™</h1>
  <p>Review the evidence. Catch the risk. Keep the final GMP decision human.</p>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="qc-law"><b>Reviewer Law:</b> A trend is not a diagnosis. The engine separates observed data, inferred risk, and missing information before recommending review.</div>
""", unsafe_allow_html=True)

with st.sidebar:
    st.header("Review Setup")
    st.caption("V0.2 · HPLC Assay")
    with st.expander("Sequence rules", expanded=True):
        require_blank = st.checkbox("Require blank before samples", value=True)
        require_bracket = st.checkbox("Require bracketing standard", value=False)
    with st.expander("System suitability", expanded=True):
        max_area_rsd = st.number_input("Max standard area %RSD", value=2.0, min_value=0.0, step=0.1)
        max_tailing = st.number_input("Max tailing factor", value=2.0, min_value=0.0, step=0.1)
        min_plates = st.number_input("Min theoretical plates", value=2000.0, min_value=0.0, step=100.0)
        min_resolution = st.number_input("Min resolution", value=2.0, min_value=0.0, step=0.1)
    with st.expander("Chromatographic behavior", expanded=False):
        target_rt = st.number_input("Target RT (min)", value=6.0, min_value=0.0, step=0.1)
        rt_tolerance = st.number_input("RT tolerance (± min)", value=0.3, min_value=0.0, step=0.05)
        drift_alert = st.number_input("Response drift alert (%)", value=5.0, min_value=0.0, step=0.5)
    with st.expander("Results", expanded=False):
        spec_low = st.number_input("Assay spec low (%)", value=98.0, step=0.1)
        spec_high = st.number_input("Assay spec high (%)", value=102.0, step=0.1)
        max_dup_diff = st.number_input("Max replicate difference", value=2.0, min_value=0.0, step=0.1)

rules = {
    "require_blank": require_blank,
    "require_bracketing_standard": require_bracket,
    "max_standard_area_rsd": max_area_rsd,
    "response_drift_alert_pct": drift_alert,
    "max_tailing": max_tailing,
    "min_plates": min_plates,
    "min_resolution": min_resolution,
    "target_rt": target_rt,
    "rt_tolerance": rt_tolerance,
    "spec_low": spec_low,
    "spec_high": spec_high,
    "max_duplicate_difference": max_dup_diff,
}

sample = pd.DataFrame([
    [1,"BLANK","Blank-1",0,None,None,None,None,None,None],
    [2,"STANDARD","STD-1",100200,6.01,1.15,6200,4.8,None,None],
    [3,"STANDARD","STD-2",100050,6.02,1.16,6180,4.7,None,None],
    [4,"STANDARD","STD-3",99550,6.03,1.16,6150,4.7,None,None],
    [5,"SAMPLE","BATCH-A-1",110500,6.04,1.18,6100,4.6,99.4,"A"],
    [6,"SAMPLE","BATCH-A-2",111100,6.05,1.18,6080,4.6,99.9,"A"],
    [7,"BRACKET","BRK-1",94000,6.07,1.20,6000,4.5,None,None],
], columns=["injection_no","injection_type","sample_id","area","rt","tailing","plates","resolution","reported_result","replicate_group"])


def read_uploaded_file(uploaded):
    if uploaded.name.lower().endswith(".csv"):
        return pd.read_csv(uploaded), None
    xls = pd.ExcelFile(uploaded)
    if len(xls.sheet_names) == 1:
        return pd.read_excel(xls, sheet_name=xls.sheet_names[0]), xls.sheet_names[0]
    sheet = st.selectbox("Select Excel sheet", xls.sheet_names)
    return pd.read_excel(xls, sheet_name=sheet), sheet


def make_excel_report(result, rules, source_df):
    out = io.BytesIO()
    findings = pd.DataFrame(result["findings"])
    rules_df = pd.DataFrame([{"rule": k, "value": v} for k, v in rules.items()])
    summary_df = pd.DataFrame([{
        "decision": result["decision"],
        "review_coverage_pct": result["review_coverage"],
        "critical_findings": result["counts"]["critical"],
        "review_points": result["counts"]["review"],
        "generated_at_utc": datetime.utcnow().isoformat(timespec="seconds") + "Z",
    }])
    with pd.ExcelWriter(out, engine="openpyxl") as writer:
        summary_df.to_excel(writer, index=False, sheet_name="Summary")
        findings.to_excel(writer, index=False, sheet_name="Findings")
        source_df.to_excel(writer, index=False, sheet_name="Supplied_Data")
        rules_df.to_excel(writer, index=False, sheet_name="Configured_Rules")
    return out.getvalue()


tab_review, tab_format, tab_scope = st.tabs(["Run Review", "Input Format", "Scope & Safeguards"])

with tab_review:
    left, right = st.columns([1.3, 1])
    with left:
        uploaded = st.file_uploader("Upload HPLC sequence data", type=["csv", "xlsx"], help="CSV or Excel. Common header variants are recognized automatically.")
    with right:
        st.download_button("Download example CSV", sample.to_csv(index=False).encode("utf-8"), "qc_data_reviewer_example.csv", "text/csv", use_container_width=True)
        use_demo = st.button("Load demo dataset", use_container_width=True)

    df = None
    source_label = None
    if use_demo:
        st.session_state["qc_demo_loaded"] = True
    if uploaded is not None:
        st.session_state["qc_demo_loaded"] = False
        try:
            df, sheet = read_uploaded_file(uploaded)
            source_label = uploaded.name + (f" · {sheet}" if sheet else "")
        except Exception as exc:
            st.error(f"Could not read this file: {exc}")
    elif st.session_state.get("qc_demo_loaded"):
        df = sample.copy()
        source_label = "Built-in demo dataset"

    if df is not None:
        work, mapping = normalize_columns(df)
        st.subheader("1 · Supplied Data")
        st.caption(source_label)
        c1, c2, c3 = st.columns(3)
        c1.metric("Rows", len(df))
        c2.metric("Columns", len(df.columns))
        c3.metric("Recognized fields", len(mapping))
        st.dataframe(df, use_container_width=True, hide_index=True)

        with st.expander("Detected field mapping"):
            if mapping:
                st.dataframe(pd.DataFrame([{"QC field": k, "Detected source column": v} for k, v in mapping.items()]), use_container_width=True, hide_index=True)
            else:
                st.warning("No known QC fields were recognized yet.")

        if st.button("Run QC Review", type="primary", use_container_width=True):
            result = review_hplc_assay(df, rules)
            st.session_state["qc_result"] = result
            st.session_state["qc_source_df"] = df

    result = st.session_state.get("qc_result")
    if result is not None:
        st.subheader("2 · Review Summary")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Decision", result["decision"])
        c2.metric("Review Coverage", f"{result['review_coverage']}%", help="How much of the configured review can be supported by the supplied fields. This is not a probability of correctness.")
        c3.metric("Critical Findings", result["counts"]["critical"])
        c4.metric("Review Points", result["counts"]["review"])

        if result["decision"] == "REVIEW REQUIRED":
            st.warning("Human review is required before accepting the analytical package.")
        else:
            st.success("No configured rule violation was detected. Complete the authorized human review before any GMP disposition.")

        normalized = result.get("normalized_data")
        if isinstance(normalized, pd.DataFrame) and "area" in normalized.columns:
            std = normalized[normalized.get("injection_type", pd.Series(dtype=str)).isin(["STANDARD", "SST", "BRACKET"])].copy()
            if len(std) >= 2:
                std["area"] = pd.to_numeric(std["area"], errors="coerce")
                std = std.dropna(subset=["area"])
                if len(std) >= 2:
                    st.subheader("Standard Response Trend")
                    chart = std.set_index("injection_no")[["area"]]
                    st.line_chart(chart)

        st.subheader("3 · Reviewer Findings")
        severity_icon = {"CRITICAL":"🔴", "REVIEW":"🟡", "PASS":"🟢"}
        for i, f in enumerate(result["findings"], start=1):
            icon = severity_icon.get(f["severity"], "🔵")
            with st.expander(f"{icon} {i}. {f['category']} — {f['observation']}", expanded=(f["severity"] != "PASS")):
                st.markdown(f"**Evidence class:** {f['evidence']}")
                st.markdown(f"**Why it matters:** {f['why_it_matters']}")
                st.markdown(f"**Reviewer check:** {f['check']}")
                st.markdown(f"**Decision:** {f['decision']}")

        findings_csv = pd.DataFrame(result["findings"]).to_csv(index=False).encode("utf-8")
        excel_report = make_excel_report(result, rules, st.session_state.get("qc_source_df", pd.DataFrame()))
        d1, d2 = st.columns(2)
        d1.download_button("Download findings CSV", findings_csv, "qc_review_findings.csv", "text/csv", use_container_width=True)
        d2.download_button("Download review package XLSX", excel_report, "qc_data_review_package.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)

with tab_format:
    st.subheader("Recommended Input Fields")
    fields = pd.DataFrame([
        ["injection_no", "Required", "Sequence position"],
        ["injection_type", "Required", "BLANK / STANDARD / SST / SAMPLE / BRACKET"],
        ["sample_id", "Required", "Injection/sample identifier"],
        ["area", "Recommended", "Peak response / area"],
        ["rt", "Recommended", "Retention time"],
        ["tailing", "Optional", "Tailing factor"],
        ["plates", "Optional", "Theoretical plates"],
        ["resolution", "Optional", "Resolution"],
        ["reported_result", "Recommended", "Reported assay result (%)"],
        ["replicate_group", "Optional", "Groups replicate preparations/results"],
    ], columns=["Field", "Status", "Purpose"])
    st.dataframe(fields, use_container_width=True, hide_index=True)
    st.info("The reviewer recognizes several common header names automatically, so your file does not need to use these exact labels.")

with tab_scope:
    st.subheader("Current V0.2 Scope")
    st.write("HPLC Assay only: sequence integrity, blank/bracketing presence, SST checks, response trend, RT behavior, specification compliance, replicate consistency, and review coverage.")
    st.subheader("Safeguards")
    st.write("• The engine does not diagnose a root cause from a trend alone.\n\n• Missing evidence is reported as missing information.\n\n• OOS-style findings instruct controlled review rather than automatic repeat testing.\n\n• The app does not approve or release a batch. Final GMP decisions remain with authorized personnel.")
    st.subheader("Next Modules")
    st.write("Independent calculation verification → chromatogram/PDF extraction → Related Substances → Dissolution/CU → audit-trail and metadata review → evidence-grounded reviewer Q&A.")

st.divider()
st.caption("QC DATA REVIEWER™ V0.2 · Decision-support prototype. Final GMP review and disposition remain the responsibility of authorized personnel.")

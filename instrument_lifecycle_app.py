from __future__ import annotations

import uuid
from datetime import date, datetime, timedelta

import pandas as pd
import streamlit as st

APP_TITLE = "Yahia QC Instrument Lifecycle & Investigation Intelligence"
APP_VERSION = "v0.1 MVP"
TAGLINE = "DON'T GUESS. FOLLOW THE EVIDENCE."

st.set_page_config(page_title=APP_TITLE, page_icon="🧪", layout="wide", initial_sidebar_state="collapsed")

INSTRUMENT_COLUMNS = [
    "instrument_id", "instrument_name", "instrument_type", "manufacturer", "model",
    "serial_number", "location", "status", "owner", "qualification_due",
    "pm_due", "calibration_due", "created_at"
]
EVENT_COLUMNS = [
    "event_id", "instrument_id", "event_date", "event_type", "severity", "subsystem",
    "status", "observed_facts", "immediate_action", "root_cause_status", "root_cause",
    "reference", "created_at"
]


def empty_df(columns):
    return pd.DataFrame(columns=columns)


def ensure_state():
    if "ilm_instruments" not in st.session_state:
        st.session_state.ilm_instruments = empty_df(INSTRUMENT_COLUMNS)
    if "ilm_events" not in st.session_state:
        st.session_state.ilm_events = empty_df(EVENT_COLUMNS)


def to_date(value):
    if value is None or value == "" or pd.isna(value):
        return None
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    try:
        return pd.to_datetime(value).date()
    except Exception:
        return None


def days_to(value):
    d = to_date(value)
    return None if not d else (d - date.today()).days


def due_state(value):
    days = days_to(value)
    if days is None:
        return "Not set"
    if days < 0:
        return "Overdue"
    if days <= 30:
        return "Due ≤30d"
    if days <= 60:
        return "Due ≤60d"
    return "OK"


def instrument_events(instrument_id):
    df = st.session_state.ilm_events
    if df.empty:
        return df.copy()
    return df[df["instrument_id"].astype(str) == str(instrument_id)].copy()


def health_score(row):
    score = 100
    reasons = []
    for label, field in [("Qualification", "qualification_due"), ("PM", "pm_due"), ("Calibration", "calibration_due")]:
        days = days_to(row.get(field))
        if days is None:
            score -= 4
            reasons.append(f"{label} due date not set")
        elif days < 0:
            score -= 22
            reasons.append(f"{label} overdue by {abs(days)} day(s)")
        elif days <= 30:
            score -= 8
            reasons.append(f"{label} due in {days} day(s)")

    events = instrument_events(row.get("instrument_id"))
    if not events.empty:
        open_events = events[events["status"].astype(str).str.lower() != "closed"]
        critical = open_events[open_events["severity"].astype(str).str.lower() == "critical"]
        high = open_events[open_events["severity"].astype(str).str.lower() == "high"]
        score -= min(30, len(critical) * 18 + len(high) * 10 + max(0, len(open_events) - len(critical) - len(high)) * 4)
        if len(open_events):
            reasons.append(f"{len(open_events)} open event(s)")
        if len(critical):
            reasons.append(f"{len(critical)} critical open event(s)")

        e = events.copy()
        e["_date"] = pd.to_datetime(e["event_date"], errors="coerce")
        recent = e[e["_date"] >= pd.Timestamp(date.today() - timedelta(days=90))]
        if len(recent) >= 2:
            for col, label in [("subsystem", "subsystem"), ("event_type", "event type")]:
                counts = recent[col].fillna("").astype(str).str.strip().value_counts()
                if not counts.empty and counts.iloc[0] >= 2 and counts.index[0]:
                    score -= 8
                    reasons.append(f"Repeated {label}: {counts.index[0]} ({counts.iloc[0]}×/90d)")
                    break
    return max(0, min(100, score)), reasons


def health_label(score):
    if score >= 85:
        return "Healthy"
    if score >= 70:
        return "Attention"
    if score >= 50:
        return "At Risk"
    return "Critical"


def due_table():
    rows = []
    for _, r in st.session_state.ilm_instruments.iterrows():
        for activity, field in [("Qualification", "qualification_due"), ("PM", "pm_due"), ("Calibration", "calibration_due")]:
            d = to_date(r.get(field))
            if not d:
                continue
            days = (d - date.today()).days
            if days <= 60:
                rows.append({
                    "Instrument": r.get("instrument_id"), "Name": r.get("instrument_name"),
                    "Activity": activity, "Due date": d.isoformat(), "Days": days, "Status": due_state(d)
                })
    if not rows:
        return pd.DataFrame(columns=["Instrument", "Name", "Activity", "Due date", "Days", "Status"])
    return pd.DataFrame(rows).sort_values(["Days", "Instrument"], ascending=[True, True])


def demo_data():
    today = date.today()
    st.session_state.ilm_instruments = pd.DataFrame([
        {"instrument_id":"HPLC-001","instrument_name":"Alliance HPLC","instrument_type":"HPLC","manufacturer":"Waters","model":"e2695","serial_number":"DEMO-001","location":"Instrument Lab","status":"Active","owner":"QC Instrument Team","qualification_due":(today+timedelta(days=110)).isoformat(),"pm_due":(today+timedelta(days=18)).isoformat(),"calibration_due":(today+timedelta(days=42)).isoformat(),"created_at":datetime.now().isoformat(timespec="seconds")},
        {"instrument_id":"HPLC-002","instrument_name":"HPLC System 2","instrument_type":"HPLC","manufacturer":"Agilent","model":"1260 Infinity II","serial_number":"DEMO-002","location":"Instrument Lab","status":"Active","owner":"QC Instrument Team","qualification_due":(today-timedelta(days=7)).isoformat(),"pm_due":(today+timedelta(days=90)).isoformat(),"calibration_due":(today+timedelta(days=12)).isoformat(),"created_at":datetime.now().isoformat(timespec="seconds")}
    ], columns=INSTRUMENT_COLUMNS)
    st.session_state.ilm_events = pd.DataFrame([
        {"event_id":"EVT-DEMO-001","instrument_id":"HPLC-001","event_date":(today-timedelta(days=45)).isoformat(),"event_type":"High Pressure","severity":"Medium","subsystem":"Flow Path","status":"Closed","observed_facts":"Backpressure increased during routine sequence; no leak observed.","immediate_action":"Investigation performed per local procedure.","root_cause_status":"Probable","root_cause":"Flow-path restriction suspected; not fully confirmed.","reference":"DEMO-INV-001","created_at":datetime.now().isoformat(timespec="seconds")},
        {"event_id":"EVT-DEMO-002","instrument_id":"HPLC-001","event_date":(today-timedelta(days=12)).isoformat(),"event_type":"High Pressure","severity":"High","subsystem":"Flow Path","status":"Open","observed_facts":"Pressure rose again on another method; pressure increase reproduced after startup.","immediate_action":"Sequence paused and evidence preserved.","root_cause_status":"Not identified","root_cause":"","reference":"DEMO-INV-002","created_at":datetime.now().isoformat(timespec="seconds")}
    ], columns=EVENT_COLUMNS)


def build_investigation_brief(instrument_id, expected, observed, changed, unchanged, evidence):
    inst_df = st.session_state.ilm_instruments
    inst_match = inst_df[inst_df["instrument_id"].astype(str) == str(instrument_id)]
    inst = inst_match.iloc[0] if not inst_match.empty else None
    events = instrument_events(instrument_id)
    patterns, risks, unknowns, next_actions = [], [], [], []

    if inst is not None:
        for label, field in [("Qualification", "qualification_due"), ("PM", "pm_due"), ("Calibration", "calibration_due")]:
            days = days_to(inst.get(field))
            if days is None:
                unknowns.append(f"{label} due date is not recorded in this tool.")
            elif days < 0:
                risks.append(f"{label} is overdue by {abs(days)} day(s); verify approved status before relying on the instrument for regulated work.")
            elif days <= 30:
                risks.append(f"{label} is due in {days} day(s).")

    if not events.empty:
        e = events.copy()
        e["_date"] = pd.to_datetime(e["event_date"], errors="coerce")
        recent = e[e["_date"] >= pd.Timestamp(date.today() - timedelta(days=90))]
        if len(recent) >= 2:
            for col, label in [("subsystem", "subsystem"), ("event_type", "event type")]:
                counts = recent[col].fillna("").astype(str).str.strip().value_counts()
                if not counts.empty and counts.iloc[0] >= 2 and counts.index[0]:
                    patterns.append(f"Repeated {label}: {counts.index[0]} appeared {counts.iloc[0]} times in the last 90 days.")
        open_events = events[events["status"].astype(str).str.lower() != "closed"]
        if len(open_events):
            risks.append(f"There are {len(open_events)} open historical event(s) linked to this instrument.")
        confirmed = events[(events["root_cause_status"].astype(str).str.lower() == "confirmed") & events["root_cause"].fillna("").astype(str).str.strip().ne("")]
        if not confirmed.empty:
            patterns.append("A previously confirmed root cause exists in the history; compare present evidence before assuming recurrence.")

    if not expected.strip(): unknowns.append("Expected behavior/acceptance condition is not stated.")
    if not observed.strip(): unknowns.append("The actual observation is not stated clearly enough.")
    if not changed.strip(): unknowns.append("Recent changes are unknown or not recorded.")
    if not unchanged.strip(): unknowns.append("Known constants / what stayed unchanged are not recorded.")
    if not evidence.strip(): unknowns.append("Objective evidence is not provided.")

    text = " ".join([expected, observed, changed, unchanged, evidence]).lower()
    if "pressure" in text or "ضغط" in text:
        next_actions.append("Localize the pressure increase by comparing pressure at defined flow-path boundaries per the approved procedure; change one variable at a time.")
    if "retention" in text or " rt " in f" {text} " or "زمن" in text:
        next_actions.append("Verify whether the shift is global or analyte-specific, then check mobile-phase composition/delivery, flow, temperature, and column identity before replacing components.")
    if "leak" in text or "تسريب" in text:
        next_actions.append("Preserve evidence first, then inspect the relevant fluidic path and pressure behavior before tightening/replacing parts indiscriminately.")
    if "sst" in text or "resolution" in text or "tail" in text or "plates" in text:
        next_actions.append("Separate the failed SST attribute from the suspected cause; test the highest-discrimination variable first.")
    if not next_actions:
        next_actions.append("Define one discriminating test that can separate the two most plausible competing hypotheses without destroying the current evidence.")

    conclusion = "ROOT CAUSE NOT YET IDENTIFIED"
    lines = [
        f"# QC Investigation Intelligence Brief — {instrument_id}", "",
        f"Generated: {datetime.now().isoformat(timespec='minutes')}", "",
        "## OBSERVED / REPORTED", f"- {observed.strip() or 'Insufficient observed/reported information entered.'}",
        f"- Objective evidence: {evidence.strip() or 'Not provided'}", "",
        "## CONTEXT", f"- **Expected:** {expected.strip() or 'Not stated'}", f"- **Changed:** {changed.strip() or 'Not stated'}", f"- **Stayed unchanged:** {unchanged.strip() or 'Not stated'}", "",
        "## PATTERNS FROM INSTRUMENT HISTORY", *([f"- {x}" for x in patterns] or ["- No repeat pattern detected from the currently loaded history."]), "",
        "## RISK / ATTENTION NOTES", *([f"- {x}" for x in risks] or ["- No lifecycle alert identified from the currently loaded dates/events."]), "",
        "## UNKNOWN / MISSING EVIDENCE", *([f"- {x}" for x in unknowns] or ["- No major information gap detected by the current rule set."]), "",
        "## NEXT EVIDENCE ACTION", *[f"- {x}" for x in next_actions], "",
        "## CURRENT CONCLUSION", f"**{conclusion}**", "",
        "A repeat pattern or prior history is not a confirmed root cause. Confirmation requires a targeted test/intervention with the expected response and reasonable exclusion of competing causes.", "",
        "---", "Decision-support only. Follow approved SOPs, QA requirements, qualification status, and applicable GMP/data-integrity controls."
    ]
    return "\n".join(lines), {"patterns":patterns,"risks":risks,"unknowns":unknowns,"next_actions":next_actions,"conclusion":conclusion}


ensure_state()

st.markdown("""
<style>
.block-container{max-width:1180px;padding-top:2.1rem;padding-bottom:4rem}.hero{padding:1.4rem 1.5rem;border-radius:22px;color:white;background:linear-gradient(145deg,#07101f 0%,#101b2d 58%,#191c22 100%);border:1px solid rgba(202,167,80,.5);box-shadow:0 15px 36px rgba(2,6,23,.16)}.eyebrow{color:#d6bd78;font-size:.76rem;font-weight:900;letter-spacing:.14em;text-transform:uppercase}.title{font-size:2rem;font-weight:900;line-height:1.18;margin:.35rem 0}.tag{color:#d6bd78;font-weight:900;letter-spacing:.04em}.sub{color:#cbd5e1;margin-top:.45rem;line-height:1.6}.pill{display:inline-block;margin:.55rem .35rem 0 0;padding:.28rem .55rem;border-radius:999px;border:1px solid rgba(255,255,255,.12);background:rgba(255,255,255,.06);font-size:.73rem}.notice{margin:.8rem 0;padding:.85rem 1rem;border-radius:15px;background:#fff9e8;border:1px solid #ead28b}.score{font-size:2.1rem;font-weight:900}@media(max-width:700px){.title{font-size:1.55rem}.block-container{padding-left:1rem;padding-right:1rem;padding-top:1rem}}
</style>
""", unsafe_allow_html=True)

st.markdown(f"""
<div class="hero"><div class="eyebrow">Pharmaceutical QC · Instrument Lifecycle · Investigation Intelligence</div><div class="title">🧪 Yahia QC Instrument Lifecycle & Investigation Intelligence™</div><div class="tag">{TAGLINE}</div><div class="sub">Digital instrument passports, lifecycle due-date control, failure history, health scoring, and evidence-first investigation support.</div><span class="pill">{APP_VERSION}</span><span class="pill">Rule-based Intelligence</span><span class="pill">Mobile-first</span><span class="pill">GxP-aware decision support</span></div>
""", unsafe_allow_html=True)
st.markdown('<div class="notice"><b>MVP boundary:</b> This is a decision-support prototype, not a validated GxP system of record. Keep official records in your approved systems/SOP-controlled forms.</div>', unsafe_allow_html=True)

inst_df = st.session_state.ilm_instruments
all_due = due_table()
overdues = all_due[all_due["Days"] < 0] if not all_due.empty else all_due
open_events = st.session_state.ilm_events[st.session_state.ilm_events["status"].astype(str).str.lower() != "closed"] if not st.session_state.ilm_events.empty else st.session_state.ilm_events
m1,m2,m3,m4 = st.columns(4)
m1.metric("Instruments", len(inst_df)); m2.metric("Open events", len(open_events)); m3.metric("Overdue lifecycle items", len(overdues)); m4.metric("Due within 30 days", len(all_due[(all_due["Days"]>=0)&(all_due["Days"]<=30)]) if not all_due.empty else 0)

tabs = st.tabs(["Command Center","Instrument Passport","Lifecycle","Event Log","Investigation Intelligence","Data / Backup"])

with tabs[0]:
    st.subheader("Instrument Command Center")
    if inst_df.empty:
        st.info("No instruments yet. Add your first instrument, or load demo data from Data / Backup.")
    else:
        rows=[]
        for _,r in inst_df.iterrows():
            score,reasons=health_score(r)
            rows.append({"Instrument":r.get("instrument_id"),"Name":r.get("instrument_name"),"Type":r.get("instrument_type"),"Status":r.get("status"),"Health":score,"Health state":health_label(score),"Primary alerts":"; ".join(reasons[:3]) if reasons else "No major alert detected"})
        st.dataframe(pd.DataFrame(rows).sort_values("Health"),use_container_width=True,hide_index=True)
        st.markdown("### Upcoming / overdue lifecycle actions")
        st.dataframe(all_due,use_container_width=True,hide_index=True) if not all_due.empty else st.success("No lifecycle action is due within 60 days based on loaded dates.")

with tabs[1]:
    st.subheader("Digital Instrument Passport")
    with st.form("add_instrument",clear_on_submit=True):
        c1,c2,c3=st.columns(3)
        instrument_id=c1.text_input("Instrument ID *",placeholder="HPLC-001")
        instrument_name=c2.text_input("Instrument name *",placeholder="Alliance HPLC")
        instrument_type=c3.selectbox("Type",["HPLC","UHPLC","GC","LC-MS","LC-MS/MS","UV-Vis","Dissolution","Balance","pH Meter","Other"])
        c1,c2,c3=st.columns(3); manufacturer=c1.text_input("Manufacturer"); model=c2.text_input("Model"); serial=c3.text_input("Serial number")
        c1,c2,c3=st.columns(3); location=c1.text_input("Location"); status=c2.selectbox("Operational status",["Active","Restricted","Out of Service","Under Maintenance","Retired"]); owner=c3.text_input("Owner / responsible team")
        c1,c2,c3=st.columns(3); q_due=c1.date_input("Qualification due",value=date.today()+timedelta(days=365)); pm_due=c2.date_input("PM due",value=date.today()+timedelta(days=180)); cal_due=c3.date_input("Calibration due",value=date.today()+timedelta(days=180))
        if st.form_submit_button("Add instrument",use_container_width=True):
            clean_id=instrument_id.strip().upper()
            if not clean_id or not instrument_name.strip(): st.error("Instrument ID and name are required.")
            elif (st.session_state.ilm_instruments["instrument_id"].astype(str).str.upper()==clean_id).any(): st.error("Instrument ID already exists.")
            else:
                new=pd.DataFrame([{"instrument_id":clean_id,"instrument_name":instrument_name.strip(),"instrument_type":instrument_type,"manufacturer":manufacturer.strip(),"model":model.strip(),"serial_number":serial.strip(),"location":location.strip(),"status":status,"owner":owner.strip(),"qualification_due":q_due.isoformat(),"pm_due":pm_due.isoformat(),"calibration_due":cal_due.isoformat(),"created_at":datetime.now().isoformat(timespec="seconds")}],columns=INSTRUMENT_COLUMNS)
                st.session_state.ilm_instruments=pd.concat([st.session_state.ilm_instruments,new],ignore_index=True); st.success(f"{clean_id} added."); st.rerun()
    if not st.session_state.ilm_instruments.empty: st.dataframe(st.session_state.ilm_instruments,use_container_width=True,hide_index=True)

with tabs[2]:
    st.subheader("Lifecycle Calendar")
    if st.session_state.ilm_instruments.empty: st.info("Add an instrument first.")
    else:
        st.dataframe(all_due if not all_due.empty else pd.DataFrame([{"Status":"No items due within 60 days"}]),use_container_width=True,hide_index=True)
        st.caption("Health Score is a prioritization aid only. It does not determine GMP release, qualification validity, or instrument compliance.")

with tabs[3]:
    st.subheader("Instrument Event / Failure Log")
    ids=st.session_state.ilm_instruments["instrument_id"].astype(str).tolist()
    if not ids: st.info("Add an instrument first.")
    else:
        with st.form("add_event",clear_on_submit=True):
            c1,c2,c3=st.columns(3); event_instrument=c1.selectbox("Instrument *",ids); event_date=c2.date_input("Event date",value=date.today()); event_type=c3.selectbox("Event type",["High Pressure","Low Pressure","Leak","Retention Time Shift","Peak Shape","Baseline","Carryover","SST Failure","Communication / Software","Temperature","Autosampler / Injector","Detector","Pump","Preventive Maintenance","Calibration","Qualification","Other"])
            c1,c2,c3=st.columns(3); severity=c1.selectbox("Severity",["Low","Medium","High","Critical"]); subsystem=c2.selectbox("Subsystem",["Flow Path","Pump","Injector / Autosampler","Column Compartment","Detector","Degasser","Software / CDS","Electrical","Gas Supply","General / Unknown","Other"]); event_status=c3.selectbox("Status",["Open","Under Investigation","Monitoring","Closed"])
            observed_facts=st.text_area("Observed facts *",placeholder="Record what was actually observed/reported — not the suspected diagnosis.")
            immediate_action=st.text_area("Immediate action / containment")
            c1,c2=st.columns(2); rc_status=c1.selectbox("Root cause status",["Not identified","Probable","Confirmed"]); root_cause=c2.text_input("Root cause / hypothesis")
            reference=st.text_input("Deviation / investigation / work-order reference")
            if st.form_submit_button("Save event",use_container_width=True):
                if not observed_facts.strip(): st.error("Observed facts are required.")
                elif rc_status=="Confirmed" and not root_cause.strip(): st.error("A confirmed root cause must include the confirmed cause.")
                else:
                    new=pd.DataFrame([{"event_id":"EVT-"+uuid.uuid4().hex[:10].upper(),"instrument_id":event_instrument,"event_date":event_date.isoformat(),"event_type":event_type,"severity":severity,"subsystem":subsystem,"status":event_status,"observed_facts":observed_facts.strip(),"immediate_action":immediate_action.strip(),"root_cause_status":rc_status,"root_cause":root_cause.strip(),"reference":reference.strip(),"created_at":datetime.now().isoformat(timespec="seconds")}],columns=EVENT_COLUMNS)
                    st.session_state.ilm_events=pd.concat([st.session_state.ilm_events,new],ignore_index=True); st.success("Event saved."); st.rerun()
        if not st.session_state.ilm_events.empty: st.dataframe(st.session_state.ilm_events.sort_values("event_date",ascending=False),use_container_width=True,hide_index=True)

with tabs[4]:
    st.subheader("QC Investigation Intelligence™")
    st.caption("Evidence-first decision support. Historical recurrence is a clue — never automatic proof of root cause.")
    ids=st.session_state.ilm_instruments["instrument_id"].astype(str).tolist()
    if not ids: st.info("Add an instrument first.")
    else:
        inv_id=st.selectbox("Instrument under investigation",ids,key="inv_instrument")
        match=st.session_state.ilm_instruments[st.session_state.ilm_instruments["instrument_id"].astype(str)==str(inv_id)]
        if not match.empty:
            score,reasons=health_score(match.iloc[0]); c1,c2=st.columns([1,3]); c1.markdown(f"<div class='score'>{score}/100</div><b>{health_label(score)}</b>",unsafe_allow_html=True); c2.write("**Current lifecycle / history signals**"); [c2.write(f"• {r}") for r in reasons] if reasons else c2.write("• No major signal detected from loaded data.")
        with st.form("investigation_form"):
            expected=st.text_area("1) What was expected?"); observed=st.text_area("2) What happened actually?"); changed=st.text_area("3) What changed recently?"); unchanged=st.text_area("4) What stayed unchanged?"); evidence=st.text_area("5) Objective evidence available")
            analyze=st.form_submit_button("Build evidence brief",use_container_width=True)
        if analyze:
            brief,result=build_investigation_brief(inv_id,expected,observed,changed,unchanged,evidence); st.session_state.ilm_last_brief=brief; st.session_state.ilm_last_result=result
        if st.session_state.get("ilm_last_brief"):
            r=st.session_state.get("ilm_last_result",{}); st.markdown("### Evidence Map"); c1,c2=st.columns(2)
            with c1:
                st.markdown("**Patterns / signals**"); [st.write(f"• {x}") for x in (r.get("patterns",[]) or ["No repeat pattern detected from current data."])]
                st.markdown("**Risk / attention notes**"); [st.write(f"• {x}") for x in (r.get("risks",[]) or ["No lifecycle alert detected from current data."])]
            with c2:
                st.markdown("**Unknown / missing evidence**"); [st.write(f"• {x}") for x in (r.get("unknowns",[]) or ["No major gap flagged by the current rule set."])]
                st.markdown("**Next evidence action**"); [st.write(f"• {x}") for x in r.get("next_actions",[])]
            st.warning(r.get("conclusion","ROOT CAUSE NOT YET IDENTIFIED"))
            with st.expander("Full investigation brief"): st.markdown(st.session_state.ilm_last_brief)
            st.download_button("Download investigation brief (.md)",data=st.session_state.ilm_last_brief.encode("utf-8"),file_name=f"{inv_id}_investigation_brief.md",mime="text/markdown",use_container_width=True)

with tabs[5]:
    st.subheader("Data / Backup")
    st.write("Use CSV export/import in the MVP so prototype data can be retained intentionally.")
    c1,c2=st.columns(2)
    c1.download_button("Download instruments.csv",data=st.session_state.ilm_instruments.to_csv(index=False).encode("utf-8-sig"),file_name="instruments.csv",mime="text/csv",use_container_width=True)
    c2.download_button("Download instrument_events.csv",data=st.session_state.ilm_events.to_csv(index=False).encode("utf-8-sig"),file_name="instrument_events.csv",mime="text/csv",use_container_width=True)
    st.markdown("### Restore from CSV")
    up_inst=st.file_uploader("Upload instruments.csv",type=["csv"],key="up_inst"); up_events=st.file_uploader("Upload instrument_events.csv",type=["csv"],key="up_events")
    if st.button("Restore uploaded data",use_container_width=True):
        try:
            if up_inst is not None:
                new_inst=pd.read_csv(up_inst,dtype=str).fillna(""); missing=[c for c in INSTRUMENT_COLUMNS if c not in new_inst.columns]
                if missing: raise ValueError(f"Instruments CSV missing columns: {', '.join(missing)}")
                st.session_state.ilm_instruments=new_inst[INSTRUMENT_COLUMNS].copy()
            if up_events is not None:
                new_events=pd.read_csv(up_events,dtype=str).fillna(""); missing=[c for c in EVENT_COLUMNS if c not in new_events.columns]
                if missing: raise ValueError(f"Events CSV missing columns: {', '.join(missing)}")
                st.session_state.ilm_events=new_events[EVENT_COLUMNS].copy()
            st.success("Data restored."); st.rerun()
        except Exception as exc: st.error(str(exc))
    st.markdown("### Demo / reset")
    c1,c2=st.columns(2)
    if c1.button("Load demo data",use_container_width=True): demo_data(); st.session_state.pop("ilm_last_brief",None); st.session_state.pop("ilm_last_result",None); st.rerun()
    if c2.button("Clear current session data",use_container_width=True): st.session_state.ilm_instruments=empty_df(INSTRUMENT_COLUMNS); st.session_state.ilm_events=empty_df(EVENT_COLUMNS); st.session_state.pop("ilm_last_brief",None); st.session_state.pop("ilm_last_result",None); st.rerun()

st.divider()
st.caption("Yahia Abdelhalim · Pharmaceutical QC Expert · Helping Pharmaceutical Analysts Make Better Laboratory Decisions")

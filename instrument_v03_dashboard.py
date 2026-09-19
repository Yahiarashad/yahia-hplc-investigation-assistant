# v0.3 Interactive Dashboard for Yahia QC Instrument Lifecycle
# Executed inside authenticated application context.

from datetime import date

DASH_SELECT = (
    "id,instrument_code,instrument_name,instrument_type,operational_status,qualification_due,pm_due,calibration_due,"
    "need_identified_date,need_justification,intended_use,urs_reference,urs_approval_date,quotation_reference,quotation_date,"
    "pr_number,pr_approval_date,po_number,po_approval_date,expected_receiving_date,receiving_date,installation_date,"
    "iq_date,oq_date,pq_date,issuance_date,first_run_date,created_at"
)


def _dash_missing_stage(inst):
    checks = [
        ("Need", bool(inst.get("need_identified_date") and inst.get("need_justification") and inst.get("intended_use"))),
        ("URS", bool(inst.get("urs_reference") and inst.get("urs_approval_date"))),
        ("Quotation", bool(inst.get("quotation_reference") and inst.get("quotation_date"))),
        ("PR", bool(inst.get("pr_number") and inst.get("pr_approval_date"))),
        ("PO", bool(inst.get("po_number") and inst.get("po_approval_date"))),
        ("Receiving", bool(inst.get("receiving_date"))),
        ("Installation", bool(inst.get("installation_date"))),
        ("IQ", bool(inst.get("iq_date"))),
        ("OQ", bool(inst.get("oq_date"))),
        ("PQ", bool(inst.get("pq_date"))),
        ("Release", bool(inst.get("issuance_date"))),
        ("First Run", bool(inst.get("first_run_date"))),
    ]
    complete = sum(1 for _, done in checks if done)
    next_stage = next((label for label, done in checks if not done), "Routine Operation")
    return next_stage, int(round(complete/len(checks)*100))


def _dash_card(label, value, note, tone="navy"):
    return f'<div class="v03-kpi {tone}"><div class="v03-kpi-label">{label}</div><div class="v03-kpi-value">{value}</div><div class="v03-kpi-note">{note}</div></div>'


st.markdown(
    """
<style>
.v03-dashboard-hero{border:1px solid rgba(214,184,95,.45);border-radius:22px;padding:1.2rem 1.15rem;margin:.35rem 0 1rem;color:#fff;background-color:#07111f;background-size:cover;background-position:center;box-shadow:0 12px 34px rgba(2,12,27,.14)}
.v03-dashboard-hero h2{color:#fff!important;margin:.1rem 0 .35rem!important}.v03-dashboard-hero p{margin:.15rem 0;color:#dbe7f1}.v03-dashboard-hero .gold{color:#e1c56d;font-weight:800}
.v03-kpi-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:.65rem;margin:.7rem 0 1rem}.v03-kpi{border:1px solid #e2e8f0;border-radius:16px;padding:.8rem .75rem;background:#fff;box-shadow:0 4px 14px rgba(15,23,42,.045)}.v03-kpi-label{font-size:.78rem;color:#64748b;font-weight:700}.v03-kpi-value{font-size:1.7rem;color:#0f2742;font-weight:800;line-height:1.15;margin:.12rem 0}.v03-kpi-note{font-size:.75rem;color:#94a3b8}.v03-kpi.red{border-top:3px solid #d64545}.v03-kpi.amber{border-top:3px solid #d7a52c}.v03-kpi.green{border-top:3px solid #16a36f}.v03-kpi.blue{border-top:3px solid #2876a7}
.v03-priority{border:1px solid #e2e8f0;border-radius:14px;padding:.7rem .8rem;margin:.45rem 0;background:#fff}.v03-priority b{color:#1e293b}.v03-priority span{font-size:.82rem;color:#64748b}
@media(max-width:800px){.v03-kpi-grid{grid-template-columns:1fr 1fr}.v03-dashboard-hero{padding:1rem}.v03-kpi-value{font-size:1.45rem}}
</style>
""",
    unsafe_allow_html=True,
)

st.markdown(
    """<div class="v03-dashboard-hero"><h2>Instrument Lifecycle Control Center</h2><p>See what needs a decision now — without losing the lifecycle story behind it.</p><p class="gold">DON'T GUESS. FOLLOW THE EVIDENCE.</p></div>""",
    unsafe_allow_html=True,
)

dash_instruments, dash_err, dash_ok = _db_list("instruments", DASH_SELECT, "created_at.asc")
dash_calibrations, _, cal_ok = _db_list("calibration_records", "id,instrument_id,result,ooc_status,calibration_date,next_due", "calibration_date.desc")
dash_retirements, _, ret_ok = _db_list("instrument_retirements", "id,instrument_id,decommission_date", "created_at.desc")

if not dash_ok:
    st.error("Could not load Dashboard data from Supabase.")
    if dash_err: st.caption(f"Diagnostic: {dash_err}")
else:
    retired_ids = {str(r.get("instrument_id")) for r in dash_retirements if r.get("decommission_date")} if ret_ok else set()
    total = len(dash_instruments)
    active = sum(1 for i in dash_instruments if str(i.get("operational_status") or "") == "Active" and str(i.get("id")) not in retired_ids)
    acquisition = sum(1 for i in dash_instruments if not i.get("first_run_date") and str(i.get("id")) not in retired_ids)
    open_events_count = sum(1 for e in events if str(e.get("event_status")) != "Closed")
    cal_overdue = sum(1 for i in dash_instruments if (_days_to(i.get("calibration_due")) is not None and _days_to(i.get("calibration_due")) < 0) and str(i.get("id")) not in retired_ids)
    pm_overdue = sum(1 for i in dash_instruments if (_days_to(i.get("pm_due")) is not None and _days_to(i.get("pm_due")) < 0) and str(i.get("id")) not in retired_ids)
    due30 = 0
    for i in dash_instruments:
        if str(i.get("id")) in retired_ids: continue
        for field in ("calibration_due","pm_due","qualification_due"):
            days = _days_to(i.get(field))
            if days is not None and 0 <= days <= 30: due30 += 1
    open_ooc = 0
    if cal_ok:
        for r in dash_calibrations:
            if str(r.get("result") or "").upper() == "OOC" and str(r.get("ooc_status") or "Open") not in {"Closed","Resolved","Not applicable"}:
                open_ooc += 1

    cards = "".join([
        _dash_card("Total instruments", total, "All lifecycle records", "blue"),
        _dash_card("Acquisition / qualification", acquisition, "Before First Run", "amber"),
        _dash_card("Active instruments", active, "Routine use", "green"),
        _dash_card("Open events", open_events_count, "Require review", "amber" if open_events_count else "blue"),
        _dash_card("Calibration overdue", cal_overdue, "Action required", "red" if cal_overdue else "green"),
        _dash_card("PM overdue", pm_overdue, "Action required", "red" if pm_overdue else "green"),
        _dash_card("Due ≤30 days", due30, "Upcoming controls", "amber" if due30 else "green"),
        _dash_card("Open OOC", open_ooc, "Impact / closure path", "red" if open_ooc else "green"),
    ])
    st.markdown(f'<div class="v03-kpi-grid">{cards}</div>', unsafe_allow_html=True)

    st.subheader("Quick actions")
    q1,q2,q3 = st.columns(3)
    add_clicked = q1.button("➕ New Need / Instrument", use_container_width=True)
    lifecycle_clicked = q2.button("↻ Continue Lifecycle", use_container_width=True)
    calibration_clicked = q3.button("◎ Log Calibration", use_container_width=True)
    q4,q5,q6 = st.columns(3)
    pm_clicked = q4.button("🛠 Log Maintenance", use_container_width=True)
    event_clicked = q5.button("⚠ New Event", use_container_width=True)
    investigation_clicked = q6.button("🔎 Start Investigation", use_container_width=True)
    if add_clicked: st.info("Open **Instrument Passport** to create the identity, then continue in **Lifecycle → Need / Initiation**.")
    if lifecycle_clicked: st.info("Open **Lifecycle**. The app will highlight the next missing evidence-based milestone.")
    if calibration_clicked: st.info("Open **Calibration & PM → Calibration Control Center**.")
    if pm_clicked: st.info("Open **Calibration & PM → Maintenance History**.")
    if event_clicked: st.info("Open **Events** and record what actually happened before interpreting it.")
    if investigation_clicked: st.info("Open **Investigation Intelligence** and preserve Observed / Inferred / Unknown separately.")

    st.subheader("Priority attention queue")
    priority=[]
    code_by_id={str(i.get("id")):str(i.get("instrument_code") or "") for i in dash_instruments}
    for i in dash_instruments:
        iid=str(i.get("id")); code=str(i.get("instrument_code") or "Instrument")
        if iid in retired_ids: continue
        for label,field in [("Calibration","calibration_due"),("PM","pm_due"),("Qualification","qualification_due")]:
            days=_days_to(i.get(field))
            if days is not None and days < 0: priority.append((1,code,f"{label} overdue by {abs(days)} day(s)"))
            elif days is not None and days <= 30: priority.append((4,code,f"{label} due in {days} day(s)"))
        expected=_parse_date(i.get("expected_receiving_date")) if i.get("expected_receiving_date") else None
        if expected and not i.get("receiving_date") and expected < date.today(): priority.append((3,code,f"Expected receiving passed by {(date.today()-expected).days} day(s)"))
        next_stage,progress=_dash_missing_stage(i)
        if next_stage != "Routine Operation": priority.append((5,code,f"Lifecycle {progress}% · next milestone: {next_stage}"))
    for e in events:
        if str(e.get("event_status")) != "Closed":
            sev=str(e.get("severity") or "Medium")
            rank=0 if sev in {"Critical","High"} else 2
            priority.append((rank,code_by_id.get(str(e.get("instrument_id")),"Instrument"),f"Open {sev.lower()} event · {e.get('event_type') or 'Event'}"))
    if cal_ok:
        for r in dash_calibrations:
            if str(r.get("result") or "").upper()=="OOC" and str(r.get("ooc_status") or "Open") not in {"Closed","Resolved","Not applicable"}:
                priority.append((0,code_by_id.get(str(r.get("instrument_id")),"Instrument"),"Calibration OOC requires impact / investigation closure"))
    if not priority:
        st.success("No priority signal detected right now.")
    else:
        for rank,code,msg in sorted(priority,key=lambda x:x[0])[:10]:
            icon="🔴" if rank<=1 else "🟠" if rank<=3 else "🟡"
            st.markdown(f'<div class="v03-priority"><b>{icon} {code}</b><br><span>{msg}</span></div>',unsafe_allow_html=True)

    st.subheader("Lifecycle portfolio")
    if not dash_instruments:
        st.info("No instruments yet.")
    else:
        portfolio=[]
        for i in dash_instruments:
            next_stage,progress=_dash_missing_stage(i)
            portfolio.append({"Instrument":i.get("instrument_code"),"Name":i.get("instrument_name"),"Lifecycle":f"{progress}%","Current / next phase":"Retired" if str(i.get("id")) in retired_ids else next_stage,"Operational status":i.get("operational_status")})
        st.dataframe(pd.DataFrame(portfolio),use_container_width=True,hide_index=True)
        option_map={f"{i.get('instrument_code')} · {i.get('instrument_name') or 'Unnamed'}":i for i in dash_instruments}
        selected=st.selectbox("Inspect lifecycle progress",list(option_map.keys()),key="v03_dashboard_portfolio")
        selected_inst=option_map[selected]
        next_stage,progress=_dash_missing_stage(selected_inst)
        st.progress(progress/100.0)
        if str(selected_inst.get("id")) in retired_ids:
            st.success("Lifecycle closed · Retired / Decommissioned")
        else:
            st.markdown(f'<div class="cta"><b>{progress}% lifecycle evidence recorded</b><br>Next controlled milestone: <b>{next_stage}</b>. Open the Lifecycle tab to continue.</div>',unsafe_allow_html=True)

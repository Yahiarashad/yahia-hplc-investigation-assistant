# v0.3 Sprint 2 Interactive Dashboard for Yahia QC Instrument Lifecycle
# Executed inside authenticated application context.

from datetime import date

DASH_SELECT = (
    "id,instrument_code,instrument_name,instrument_type,operational_status,qualification_due,pm_due,calibration_due,"
    "need_identified_date,need_justification,intended_use,urs_reference,urs_approval_date,quotation_reference,quotation_date,"
    "pr_number,pr_approval_date,po_number,po_approval_date,expected_receiving_date,receiving_date,installation_date,"
    "iq_date,oq_date,pq_date,issuance_date,first_run_date,created_at"
)


def _dash_stage_checks(inst):
    return [
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


def _dash_missing_stage(inst):
    checks = _dash_stage_checks(inst)
    complete = sum(1 for _, done in checks if done)
    next_stage = next((label for label, done in checks if not done), "Routine Operation")
    return next_stage, int(round(complete / len(checks) * 100))


def _dash_phase(inst, retired=False):
    if retired:
        return "Retired"
    next_stage, _ = _dash_missing_stage(inst)
    if next_stage in {"Need", "URS"}:
        return "Plan"
    if next_stage in {"Quotation", "PR", "PO", "Receiving"}:
        return "Acquire"
    if next_stage in {"Installation", "IQ", "OQ", "PQ", "Release"}:
        return "Qualify"
    return "Operate"


def _dash_card(label, value, note, tone="navy", icon="•"):
    return (
        f'<div class="v03-kpi {tone}">'
        f'<div class="v03-kpi-top"><span class="v03-kpi-icon">{icon}</span><span class="v03-kpi-label">{label}</span></div>'
        f'<div class="v03-kpi-value">{value}</div><div class="v03-kpi-note">{note}</div></div>'
    )


def _priority_card(rank, code, message):
    tone = "critical" if rank <= 1 else "warning" if rank <= 3 else "watch"
    icon = "●" if rank <= 1 else "◆" if rank <= 3 else "○"
    return (
        f'<div class="v03-priority {tone}">'
        f'<div class="v03-priority-head"><b>{icon} {code}</b><span>{"ACT NOW" if rank <= 1 else "REVIEW" if rank <= 3 else "WATCH"}</span></div>'
        f'<div class="v03-priority-msg">{message}</div></div>'
    )


st.markdown(
    """
<style>
.v03-dashboard-hero{border:1px solid rgba(214,184,95,.45);border-radius:24px;padding:1.35rem 1.25rem;margin:.35rem 0 1rem;color:#fff;background-color:#07111f;background-size:cover;background-position:center;box-shadow:0 14px 34px rgba(2,12,27,.14)}
.v03-dashboard-hero h2{color:#fff!important;margin:.1rem 0 .35rem!important}.v03-dashboard-hero p{margin:.15rem 0;color:#dbe7f1}.v03-dashboard-hero .gold{color:#e1c56d;font-weight:800}.v03-dashboard-kicker{font-size:.76rem;letter-spacing:.12em;color:#e1c56d;font-weight:800;margin-bottom:.35rem}
.v03-kpi-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:.65rem;margin:.75rem 0 1rem}.v03-kpi{border:1px solid #e2e8f0;border-radius:17px;padding:.82rem .78rem;background:#fff;box-shadow:0 5px 16px rgba(15,23,42,.05);transition:.16s ease}.v03-kpi:hover{transform:translateY(-2px);box-shadow:0 9px 22px rgba(15,23,42,.08)}.v03-kpi-top{display:flex;align-items:center;gap:.35rem}.v03-kpi-icon{font-size:.8rem}.v03-kpi-label{font-size:.75rem;color:#64748b;font-weight:800}.v03-kpi-value{font-size:1.75rem;color:#0f2742;font-weight:850;line-height:1.12;margin:.18rem 0}.v03-kpi-note{font-size:.73rem;color:#94a3b8}.v03-kpi.red{border-top:3px solid #d64545}.v03-kpi.amber{border-top:3px solid #d7a52c}.v03-kpi.green{border-top:3px solid #16a36f}.v03-kpi.blue{border-top:3px solid #2876a7}
.v03-attention-summary{display:flex;align-items:flex-start;justify-content:space-between;gap:1rem;border-radius:18px;padding:1rem 1.05rem;margin:.35rem 0 1rem;border:1px solid #e2e8f0;background:linear-gradient(135deg,#f8fafc,#ffffff)}.v03-attention-summary strong{display:block;color:#0f2742;font-size:1.05rem}.v03-attention-summary span{color:#64748b;font-size:.84rem}.v03-attention-number{font-size:2rem!important;line-height:1!important;font-weight:850!important;color:#b42318!important}
.v03-priority{border:1px solid #e2e8f0;border-left:5px solid #94a3b8;border-radius:15px;padding:.72rem .8rem;margin:.48rem 0;background:#fff;box-shadow:0 3px 12px rgba(15,23,42,.035)}.v03-priority.critical{border-left-color:#d64545;background:#fffafa}.v03-priority.warning{border-left-color:#d7a52c;background:#fffdf7}.v03-priority.watch{border-left-color:#2876a7}.v03-priority-head{display:flex;justify-content:space-between;align-items:center;gap:.5rem}.v03-priority-head b{color:#1e293b}.v03-priority-head span{font-size:.65rem;font-weight:800;letter-spacing:.07em;color:#64748b}.v03-priority-msg{font-size:.84rem;color:#64748b;margin-top:.16rem}
.v03-phase-grid{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:.55rem;margin:.6rem 0 1rem}.v03-phase{border:1px solid #e2e8f0;border-radius:14px;padding:.7rem;background:#fff}.v03-phase b{display:block;color:#0f2742}.v03-phase span{font-size:.76rem;color:#64748b}.v03-phase strong{font-size:1.25rem;color:#d1a733}
.v03-instrument-card{border:1px solid #dbe3ec;border-radius:18px;padding:.9rem;margin:.55rem 0;background:linear-gradient(180deg,#fff,#fbfdff)}.v03-instrument-card-head{display:flex;justify-content:space-between;gap:.5rem;align-items:center}.v03-instrument-card-head b{color:#0f2742}.v03-badge{font-size:.7rem;font-weight:800;padding:.2rem .5rem;border-radius:999px;background:#edf6ff;color:#24577a}.v03-progress-note{font-size:.8rem;color:#64748b;margin-top:.35rem}
@media(max-width:800px){.v03-kpi-grid{grid-template-columns:1fr 1fr}.v03-phase-grid{grid-template-columns:1fr 1fr}.v03-phase:last-child{grid-column:1/-1}.v03-dashboard-hero{padding:1rem}.v03-kpi-value{font-size:1.48rem}.v03-attention-summary{padding:.85rem}.v03-instrument-card{padding:.8rem}}
</style>
""",
    unsafe_allow_html=True,
)

st.markdown(
    """<div class="v03-dashboard-hero"><div class="v03-dashboard-kicker">QC INSTRUMENT INTELLIGENCE</div><h2>Instrument Lifecycle Control Center</h2><p>Know what needs action now — and why — without losing the evidence trail behind it.</p><p class="gold">DON'T GUESS. FOLLOW THE EVIDENCE.</p></div>""",
    unsafe_allow_html=True,
)

dash_instruments, dash_err, dash_ok = _db_list("instruments", DASH_SELECT, "created_at.asc")
dash_calibrations, _, cal_ok = _db_list("calibration_records", "id,instrument_id,result,ooc_status,calibration_date,next_due", "calibration_date.desc")
dash_retirements, _, ret_ok = _db_list("instrument_retirements", "id,instrument_id,decommission_date", "created_at.desc")

if not dash_ok:
    st.error("Could not load Dashboard data from Supabase.")
    if dash_err:
        st.caption(f"Diagnostic: {dash_err}")
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
        if str(i.get("id")) in retired_ids:
            continue
        for field in ("calibration_due", "pm_due", "qualification_due"):
            days = _days_to(i.get(field))
            if days is not None and 0 <= days <= 30:
                due30 += 1
    open_ooc = 0
    if cal_ok:
        for r in dash_calibrations:
            if str(r.get("result") or "").upper() == "OOC" and str(r.get("ooc_status") or "Open") not in {"Closed", "Resolved", "Not applicable"}:
                open_ooc += 1

    cards = "".join([
        _dash_card("Total instruments", total, "All lifecycle records", "blue", "▦"),
        _dash_card("Acquisition / qualification", acquisition, "Before First Run", "amber", "↻"),
        _dash_card("Active instruments", active, "Routine use", "green", "✓"),
        _dash_card("Open events", open_events_count, "Require review", "amber" if open_events_count else "blue", "!"),
        _dash_card("Calibration overdue", cal_overdue, "Action required", "red" if cal_overdue else "green", "◎"),
        _dash_card("PM overdue", pm_overdue, "Action required", "red" if pm_overdue else "green", "⚙"),
        _dash_card("Due ≤30 days", due30, "Upcoming controls", "amber" if due30 else "green", "◷"),
        _dash_card("Open OOC", open_ooc, "Impact / closure path", "red" if open_ooc else "green", "△"),
    ])
    st.markdown(f'<div class="v03-kpi-grid">{cards}</div>', unsafe_allow_html=True)

    priority = []
    code_by_id = {str(i.get("id")): str(i.get("instrument_code") or "") for i in dash_instruments}
    for i in dash_instruments:
        iid = str(i.get("id"))
        code = str(i.get("instrument_code") or "Instrument")
        if iid in retired_ids:
            continue
        for label, field in [("Calibration", "calibration_due"), ("PM", "pm_due"), ("Qualification", "qualification_due")]:
            days = _days_to(i.get(field))
            if days is not None and days < 0:
                priority.append((1, code, f"{label} overdue by {abs(days)} day(s)"))
            elif days is not None and days <= 30:
                priority.append((4, code, f"{label} due in {days} day(s)"))
        expected = _parse_date(i.get("expected_receiving_date")) if i.get("expected_receiving_date") else None
        if expected and not i.get("receiving_date") and expected < date.today():
            priority.append((3, code, f"Expected receiving passed by {(date.today() - expected).days} day(s)"))
        next_stage, progress = _dash_missing_stage(i)
        if next_stage != "Routine Operation":
            priority.append((5, code, f"Lifecycle {progress}% · next milestone: {next_stage}"))
    for e in events:
        if str(e.get("event_status")) != "Closed":
            sev = str(e.get("severity") or "Medium")
            rank = 0 if sev in {"Critical", "High"} else 2
            priority.append((rank, code_by_id.get(str(e.get("instrument_id")), "Instrument"), f"Open {sev.lower()} event · {e.get('event_type') or 'Event'}"))
    if cal_ok:
        for r in dash_calibrations:
            if str(r.get("result") or "").upper() == "OOC" and str(r.get("ooc_status") or "Open") not in {"Closed", "Resolved", "Not applicable"}:
                priority.append((0, code_by_id.get(str(r.get("instrument_id")), "Instrument"), "Calibration OOC requires impact / investigation closure"))

    critical_count = sum(1 for rank, _, _ in priority if rank <= 1)
    review_count = sum(1 for rank, _, _ in priority if 1 < rank <= 3)
    st.markdown(
        f'<div class="v03-attention-summary"><div><strong>What needs attention now?</strong><span>{"No immediate critical signal." if not priority else "Priority is ranked by evidence-based urgency, not by guesswork."}</span></div><span class="v03-attention-number">{critical_count}</span></div>',
        unsafe_allow_html=True,
    )

    st.subheader("Quick actions")
    q1, q2 = st.columns(2)
    add_clicked = q1.button("➕ New Need / Instrument", use_container_width=True)
    lifecycle_clicked = q2.button("↻ Continue Lifecycle", use_container_width=True)
    q3, q4 = st.columns(2)
    calibration_clicked = q3.button("◎ Log Calibration", use_container_width=True)
    pm_clicked = q4.button("⚙ Log Maintenance", use_container_width=True)
    q5, q6 = st.columns(2)
    event_clicked = q5.button("⚠ New Event", use_container_width=True)
    investigation_clicked = q6.button("🔎 Start Investigation", use_container_width=True)
    if add_clicked:
        st.info("Go to **Passport** to create the instrument identity, then open **Lifecycle → Need / Initiation**.")
    if lifecycle_clicked:
        st.info("Go to **Lifecycle**. The current stage and next required evidence are highlighted at the top.")
    if calibration_clicked:
        st.info("Go to **Cal & PM → Calibration Control Center**.")
    if pm_clicked:
        st.info("Go to **Cal & PM → Maintenance History**.")
    if event_clicked:
        st.info("Go to **Events** and record what actually happened before interpreting it.")
    if investigation_clicked:
        st.info("Go to **Investigate** and preserve Observed / Inferred / Unknown separately.")

    st.subheader("Priority attention queue")
    if not priority:
        st.success("No priority signal detected right now.")
    else:
        for rank, code, msg in sorted(priority, key=lambda x: x[0])[:10]:
            st.markdown(_priority_card(rank, code, msg), unsafe_allow_html=True)
        if review_count or critical_count:
            st.caption(f"Critical / high-priority signals: {critical_count} · Review signals: {review_count}")

    phase_counts = {"Plan": 0, "Acquire": 0, "Qualify": 0, "Operate": 0, "Retired": 0}
    for i in dash_instruments:
        phase_counts[_dash_phase(i, str(i.get("id")) in retired_ids)] += 1
    st.subheader("Lifecycle portfolio")
    st.markdown(
        '<div class="v03-phase-grid">'
        + ''.join(f'<div class="v03-phase"><strong>{phase_counts[p]}</strong><b>{p}</b><span>{desc}</span></div>' for p, desc in [
            ("Plan", "Need / URS"),
            ("Acquire", "Quote / PR / PO / Receipt"),
            ("Qualify", "Install / IQ / OQ / PQ"),
            ("Operate", "Routine control"),
            ("Retired", "Lifecycle closed"),
        ])
        + '</div>',
        unsafe_allow_html=True,
    )

    if not dash_instruments:
        st.info("No instruments yet.")
    else:
        option_map = {f"{i.get('instrument_code')} · {i.get('instrument_name') or 'Unnamed'}": i for i in dash_instruments}
        selected = st.selectbox("Inspect instrument lifecycle", list(option_map.keys()), key="v03_dashboard_portfolio")
        selected_inst = option_map[selected]
        next_stage, progress = _dash_missing_stage(selected_inst)
        retired = str(selected_inst.get("id")) in retired_ids
        phase = _dash_phase(selected_inst, retired)
        st.markdown(
            f'<div class="v03-instrument-card"><div class="v03-instrument-card-head"><b>{selected_inst.get("instrument_code")} · {selected_inst.get("instrument_name") or "Unnamed"}</b><span class="v03-badge">{phase}</span></div><div class="v03-progress-note">Lifecycle evidence: {progress}% · {"Lifecycle closed" if retired else "Next controlled milestone: " + next_stage}</div></div>',
            unsafe_allow_html=True,
        )
        st.progress(1.0 if retired else progress / 100.0)
        if retired:
            st.success("Lifecycle closed · Retired / Decommissioned. History remains preserved.")
        else:
            missing = [label for label, done in _dash_stage_checks(selected_inst) if not done]
            if missing:
                st.caption("Missing evidence → " + " · ".join(missing[:6]) + (" …" if len(missing) > 6 else ""))
            st.markdown(
                f'<div class="cta"><b>Next decision → {next_stage}</b><br>Open <b>Lifecycle</b> to continue the controlled journey. Missing evidence stays visible and is never silently inferred.</div>',
                unsafe_allow_html=True,
            )

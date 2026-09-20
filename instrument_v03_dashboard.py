# v0.4 Instrument Intelligence Dashboard
# KPI semantics are intentionally consistent: primary counts are unique instruments.

from datetime import date
from html import escape

import pandas as pd


DASH_SELECT = (
    "id,instrument_code,instrument_name,instrument_type,operational_status,qualification_due,pm_due,calibration_due,"
    "need_identified_date,need_justification,intended_use,urs_reference,urs_approval_date,quotation_reference,quotation_date,"
    "pr_number,pr_approval_date,po_number,po_approval_date,expected_receiving_date,receiving_date,installation_date,"
    "iq_date,oq_date,pq_date,issuance_date,first_run_date,created_at"
)


def _dash_stage_checks(inst):
    need_done = bool(inst.get("need_identified_date") and inst.get("need_justification") and inst.get("intended_use"))
    urs_done = bool(inst.get("urs_reference") and inst.get("urs_approval_date"))
    quotation_done = bool(inst.get("quotation_reference") and inst.get("quotation_date"))
    pr_done = bool(inst.get("pr_number") and inst.get("pr_approval_date"))
    po_done = bool(inst.get("po_number") and inst.get("po_approval_date"))
    receiving_done = bool(inst.get("receiving_date"))
    installation_done = bool(inst.get("installation_date"))
    iq_done = bool(inst.get("iq_date"))
    oq_done = bool(inst.get("oq_date"))
    pq_done = bool(inst.get("pq_date"))
    release_done = bool(inst.get("issuance_date") and pq_done)
    first_run_done = bool(inst.get("first_run_date") and release_done)
    return [
        ("Need", need_done), ("URS", urs_done), ("Quotation", quotation_done),
        ("PR", pr_done), ("PO", po_done), ("Receiving", receiving_done),
        ("Installation", installation_done), ("IQ", iq_done), ("OQ", oq_done),
        ("PQ", pq_done), ("Release", release_done), ("First Run", first_run_done),
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
    if next_stage in {"Installation", "IQ", "OQ", "PQ", "Release", "First Run"}:
        return "Qualify"
    return "Operate"


def _dash_card(label, value, note, tone="navy", icon="•"):
    return (
        f'<div class="v04-kpi {tone}">'
        f'<div class="v04-kpi-top"><span>{icon}</span><span>{escape(str(label))}</span></div>'
        f'<div class="v04-kpi-value">{escape(str(value))}</div>'
        f'<div class="v04-kpi-note">{escape(str(note))}</div></div>'
    )


def _dash_priority_card(code, category, messages):
    tone = {"ACT NOW": "critical", "REVIEW": "warning", "WATCH": "watch"}.get(category, "watch")
    icon = {"ACT NOW": "●", "REVIEW": "◆", "WATCH": "○"}.get(category, "○")
    detail = " · ".join(messages[:2])
    more = f" · +{len(messages)-2} more" if len(messages) > 2 else ""
    return (
        f'<div class="v04-priority {tone}"><div class="v04-priority-head">'
        f'<b>{icon} {escape(str(code))}</b><span>{escape(category)} · {len(messages)} signal(s)</span></div>'
        f'<div class="v04-priority-msg">{escape(detail + more)}</div></div>'
    )


def _dash_perf_calc(row):
    try:
        scheduled = float(row.get("scheduled_hours") or 0)
        planned = float(row.get("planned_downtime_hours") or 0)
        unplanned = float(row.get("unplanned_downtime_hours") or 0)
        productive = float(row.get("productive_run_hours") or 0)
    except Exception:
        return None
    planned_operating = max(0.0, scheduled - planned)
    available = max(0.0, planned_operating - unplanned)
    availability = available / planned_operating * 100 if planned_operating > 0 else None
    utilization = productive / available * 100 if available > 0 else None
    return planned_operating, available, productive, availability, utilization


st.markdown(
    """
<style>
.v04-hero{border:1px solid rgba(214,184,95,.45);border-radius:24px;padding:1.25rem;margin:.35rem 0 1rem;color:#fff;background:#07111f;box-shadow:0 14px 34px rgba(2,12,27,.14)}
.v04-hero h2{color:#fff!important;margin:.12rem 0 .4rem!important}.v04-hero p{margin:.15rem 0;color:#dbe7f1}.v04-hero .gold{color:#e1c56d;font-weight:800}.v04-kicker{font-size:.75rem;letter-spacing:.12em;color:#55d9ea;font-weight:900}.v04-micro{font-size:.76rem!important;color:#8fa7c1!important;letter-spacing:.04em}
.v04-system{display:flex;align-items:center;justify-content:space-between;gap:.7rem;border:1px solid #183a4d;border-radius:999px;padding:.62rem .9rem;margin:.35rem 0 1rem;background:#071827;color:#cfeaf0}.v04-system-left{display:flex;align-items:center;gap:.55rem;font-weight:800}.v04-dot{width:12px;height:12px;border-radius:50%;background:#20c997;box-shadow:0 0 0 5px rgba(32,201,151,.12)}.v04-system.critical .v04-dot{background:#e55353;box-shadow:0 0 0 5px rgba(229,83,83,.12)}.v04-system.review .v04-dot{background:#d9a62e;box-shadow:0 0 0 5px rgba(217,166,46,.12)}.v04-system.watch .v04-dot{background:#35a7d3;box-shadow:0 0 0 5px rgba(53,167,211,.12)}.v04-system-note{font-size:.76rem;color:#8fb0bf;text-align:right}
.v04-kpi-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:.65rem;margin:.75rem 0 1rem}.v04-kpi{border:1px solid #e2e8f0;border-radius:17px;padding:.82rem .78rem;background:#fff;box-shadow:0 5px 16px rgba(15,23,42,.05)}.v04-kpi-top{display:flex;align-items:center;gap:.35rem;font-size:.75rem;color:#64748b;font-weight:800}.v04-kpi-value{font-size:1.75rem;color:#0f2742;font-weight:850;line-height:1.12;margin:.18rem 0}.v04-kpi-note{font-size:.73rem;color:#94a3b8}.v04-kpi.red{border-top:3px solid #d64545}.v04-kpi.amber{border-top:3px solid #d7a52c}.v04-kpi.green{border-top:3px solid #16a36f}.v04-kpi.blue{border-top:3px solid #2876a7}
.v04-attention{border:1px solid #e2e8f0;border-radius:18px;padding:1rem;margin:.4rem 0 1rem;background:linear-gradient(135deg,#f8fafc,#fff)}.v04-attention-head{display:flex;justify-content:space-between;gap:.8rem;align-items:center}.v04-attention strong{color:#0f2742}.v04-attention p{color:#64748b;font-size:.82rem;margin:.25rem 0}.v04-chips{display:flex;gap:.35rem;flex-wrap:wrap}.v04-chip{border-radius:999px;padding:.28rem .48rem;font-size:.68rem;font-weight:850;border:1px solid #e2e8f0;background:#fff}.v04-chip.red{color:#b42318;border-color:#f1b7b2;background:#fff8f7}.v04-chip.amber{color:#8b650e;border-color:#ead7a0;background:#fffcf3}.v04-chip.blue{color:#176187;border-color:#b9ddeb;background:#f5fbff}
.v04-priority{border:1px solid #e2e8f0;border-left:5px solid #94a3b8;border-radius:15px;padding:.72rem .8rem;margin:.48rem 0;background:#fff}.v04-priority.critical{border-left-color:#d64545;background:#fffafa}.v04-priority.warning{border-left-color:#d7a52c;background:#fffdf7}.v04-priority.watch{border-left-color:#2876a7}.v04-priority-head{display:flex;justify-content:space-between;gap:.5rem}.v04-priority-head b{color:#1e293b}.v04-priority-head span{font-size:.65rem;font-weight:800;color:#64748b}.v04-priority-msg{font-size:.82rem;color:#64748b;margin-top:.15rem}
.v04-phase-grid{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:.55rem;margin:.6rem 0 1rem}.v04-phase{border:1px solid #e2e8f0;border-radius:14px;padding:.7rem;background:#fff}.v04-phase b{display:block;color:#0f2742}.v04-phase span{font-size:.75rem;color:#64748b}.v04-phase strong{font-size:1.25rem;color:#d1a733}
.v04-inst-card{border:1px solid #15354a;border-radius:18px;padding:.95rem;margin:.55rem 0;background:linear-gradient(145deg,#071422,#0c2032);color:#dceaf2}.v04-inst-head{display:flex;justify-content:space-between;gap:.5rem}.v04-inst-head b{color:#fff}.v04-badge{font-size:.7rem;font-weight:800;padding:.2rem .5rem;border-radius:999px;background:#173f55;color:#75dbea}.v04-intel{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:.45rem;margin-top:.65rem}.v04-intel-item{border:1px solid rgba(255,255,255,.08);border-radius:12px;padding:.55rem;background:rgba(255,255,255,.03)}.v04-intel-item span{display:block;color:#7f9aaa;font-size:.64rem;text-transform:uppercase}.v04-intel-item b{display:block;color:#fff;margin-top:.12rem;font-size:.86rem}.v04-next{margin-top:.6rem;color:#e1c56d;font-weight:800}
@media(max-width:800px){.v04-kpi-grid{grid-template-columns:1fr 1fr}.v04-phase-grid{grid-template-columns:1fr 1fr}.v04-phase:last-child{grid-column:1/-1}.v04-intel{grid-template-columns:1fr 1fr}.v04-system{border-radius:17px;align-items:flex-start}.v04-system-note{font-size:.7rem}.v04-attention-head{align-items:flex-start;flex-direction:column}.v04-kpi-value{font-size:1.48rem}}
</style>
""",
    unsafe_allow_html=True,
)

st.markdown(
    """<div class="v04-hero v03-dashboard-hero"><div class="v04-kicker">QC INSTRUMENT INTELLIGENCE</div><h2>Instrument Lifecycle Control Center</h2><p>Instrument counts stay instrument counts. Signals stay signals.</p><p>Know what needs action now — and why — without losing the evidence trail.</p><p class="gold">DON'T GUESS. FOLLOW THE EVIDENCE.</p><p class="v04-micro">ENTER LESS · DECIDE BETTER · KEEP THE INSTRUMENT STORY CONNECTED</p></div>""",
    unsafe_allow_html=True,
)


dash_instruments, dash_err, dash_ok = _db_list("instruments", DASH_SELECT, "created_at.asc")
dash_calibrations, _, cal_ok = _db_list("calibration_records", "id,instrument_id,result,ooc_status,calibration_date,next_due", "calibration_date.desc")
dash_retirements, _, ret_ok = _db_list("instrument_retirements", "id,instrument_id,decommission_date", "created_at.desc")
dash_perf, _, perf_ok = _db_list("instrument_monthly_performance", "instrument_id,month_start,scheduled_hours,planned_downtime_hours,unplanned_downtime_hours,productive_run_hours", "month_start.desc")

if not dash_ok:
    st.error("Could not load Dashboard data from Supabase.")
    if dash_err:
        st.caption(f"Diagnostic: {dash_err}")
else:
    retired_ids = {str(r.get("instrument_id")) for r in dash_retirements if r.get("decommission_date")} if ret_ok else set()
    total = len(dash_instruments)

    routine_active_ids = {
        str(i.get("id")) for i in dash_instruments
        if str(i.get("operational_status") or "") == "Active"
        and _dash_stage_checks(i)[-1][1]
        and str(i.get("id")) not in retired_ids
    }
    pre_first_run_ids = {
        str(i.get("id")) for i in dash_instruments
        if not _dash_stage_checks(i)[-1][1] and str(i.get("id")) not in retired_ids
    }
    open_event_ids = {
        str(e.get("instrument_id")) for e in events
        if str(e.get("event_status") or "") != "Closed"
    }
    cal_overdue_ids = {
        str(i.get("id")) for i in dash_instruments
        if str(i.get("id")) not in retired_ids
        and _days_to(i.get("calibration_due")) is not None
        and _days_to(i.get("calibration_due")) < 0
    }
    pm_overdue_ids = {
        str(i.get("id")) for i in dash_instruments
        if str(i.get("id")) not in retired_ids
        and _days_to(i.get("pm_due")) is not None
        and _days_to(i.get("pm_due")) < 0
    }
    due30_ids = set()
    for i in dash_instruments:
        iid = str(i.get("id"))
        if iid in retired_ids:
            continue
        if any(
            (_days_to(i.get(field)) is not None and 0 <= _days_to(i.get(field)) <= 30)
            for field in ("calibration_due", "pm_due", "qualification_due")
        ):
            due30_ids.add(iid)

    open_ooc_ids = set()
    if cal_ok:
        for r in dash_calibrations:
            if str(r.get("result") or "").upper() == "OOC" and str(r.get("ooc_status") or "Open") not in {"Closed", "Resolved", "Not applicable"}:
                open_ooc_ids.add(str(r.get("instrument_id")))

    # Build all signals but classify each instrument only once by its highest urgency.
    signals = {}
    code_by_id = {str(i.get("id")): str(i.get("instrument_code") or "Instrument") for i in dash_instruments}

    def add_signal(iid, rank, message):
        signals.setdefault(str(iid), []).append((rank, message))

    for i in dash_instruments:
        iid = str(i.get("id"))
        if iid in retired_ids:
            continue
        for label, field in [("Calibration", "calibration_due"), ("PM", "pm_due"), ("Qualification", "qualification_due")]:
            days = _days_to(i.get(field))
            if days is not None and days < 0:
                add_signal(iid, 1, f"{label} overdue by {abs(days)} day(s)")
            elif days is not None and 0 <= days <= 30:
                add_signal(iid, 4, f"{label} due in {days} day(s)")
        expected = _parse_date(i.get("expected_receiving_date")) if i.get("expected_receiving_date") else None
        if expected and not i.get("receiving_date") and expected < date.today():
            add_signal(iid, 3, f"Expected receiving passed by {(date.today()-expected).days} day(s)")
        next_stage, progress = _dash_missing_stage(i)
        if next_stage != "Routine Operation":
            add_signal(iid, 5, f"Lifecycle readiness {progress}% · next milestone: {next_stage}")

    for e in events:
        if str(e.get("event_status") or "") != "Closed":
            sev = str(e.get("severity") or "Medium")
            add_signal(str(e.get("instrument_id")), 0 if sev in {"Critical", "High"} else 2, f"Open {sev.lower()} event · {e.get('event_type') or 'Event'}")
    if cal_ok:
        for r in dash_calibrations:
            if str(r.get("instrument_id")) in open_ooc_ids:
                add_signal(str(r.get("instrument_id")), 0, "Calibration OOC requires impact / investigation closure")

    instrument_categories = {}
    total_signal_count = 0
    for iid, items in signals.items():
        total_signal_count += len(items)
        highest = min(rank for rank, _ in items)
        category = "ACT NOW" if highest <= 1 else "REVIEW" if highest <= 3 else "WATCH"
        instrument_categories[iid] = category

    act_ids = {iid for iid, cat in instrument_categories.items() if cat == "ACT NOW"}
    review_ids = {iid for iid, cat in instrument_categories.items() if cat == "REVIEW"}
    watch_ids = {iid for iid, cat in instrument_categories.items() if cat == "WATCH"}
    attention_ids = act_ids | review_ids | watch_ids

    state_label = "ACTION REQUIRED" if act_ids else "REVIEW NEEDED" if review_ids else "SYSTEM READY · WATCH" if watch_ids else "SYSTEM READY"
    state_css = "critical" if act_ids else "review" if review_ids else "watch" if watch_ids else "ready"
    state_note = f"{len(attention_ids)} of {total} instrument(s) need attention · {total_signal_count} signal(s)"
    st.markdown(
        f'<div class="v04-system {state_css}"><div class="v04-system-left"><span class="v04-dot"></span><span>{escape(state_label)}</span></div><div class="v04-system-note">{escape(state_note)}</div></div>',
        unsafe_allow_html=True,
    )

    cards = "".join([
        _dash_card("Total instruments", total, "Unique instruments", "blue", "▦"),
        _dash_card("Before First Run", len(pre_first_run_ids), "Plan / Acquire / Qualify", "amber", "↻"),
        _dash_card("Routine active", len(routine_active_ids), "Released + First Run + Active", "green", "✓"),
        _dash_card("Open-event instruments", len(open_event_ids), "Unique affected instruments", "amber" if open_event_ids else "blue", "!"),
        _dash_card("Calibration overdue", len(cal_overdue_ids), "Unique instruments", "red" if cal_overdue_ids else "green", "◎"),
        _dash_card("PM overdue", len(pm_overdue_ids), "Unique instruments", "red" if pm_overdue_ids else "green", "⚙"),
        _dash_card("Due ≤30 days", len(due30_ids), "Unique instruments · any control", "amber" if due30_ids else "green", "◷"),
        _dash_card("Open OOC", len(open_ooc_ids), "Unique instruments", "red" if open_ooc_ids else "green", "△"),
    ])
    st.markdown(f'<div class="v04-kpi-grid">{cards}</div>', unsafe_allow_html=True)

    st.markdown(
        f'<div class="v04-attention"><div class="v04-attention-head"><div><strong>What needs attention now?</strong><p>Primary counts below are unique instruments. The smaller signal total preserves the full evidence trail.</p></div><b>{len(attention_ids)} / {total}</b></div><div class="v04-chips"><span class="v04-chip red">ACT NOW {len(act_ids)}</span><span class="v04-chip amber">REVIEW {len(review_ids)}</span><span class="v04-chip blue">WATCH {len(watch_ids)}</span><span class="v04-chip">SIGNALS {total_signal_count}</span></div></div>',
        unsafe_allow_html=True,
    )

    # Current-month performance snapshot if data exists.
    if perf_ok and dash_perf:
        current_month = date.today().replace(day=1)
        perf_rows = [r for r in dash_perf if _parse_date(r.get("month_start")) and _parse_date(r.get("month_start")).replace(day=1) == current_month]
        planned_total = available_total = productive_total = 0.0
        covered = set()
        for r in perf_rows:
            m = _dash_perf_calc(r)
            if not m:
                continue
            planned, available, productive, _, _ = m
            planned_total += planned
            available_total += available
            productive_total += productive
            covered.add(str(r.get("instrument_id")))
        if covered:
            portfolio_av = available_total / planned_total * 100 if planned_total > 0 else None
            portfolio_ut = productive_total / available_total * 100 if available_total > 0 else None
            st.markdown("### 📈 This month · Performance snapshot")
            p1, p2, p3 = st.columns(3)
            p1.metric("Availability", "—" if portfolio_av is None else f"{portfolio_av:.1f}%")
            p2.metric("Utilization", "—" if portfolio_ut is None else f"{portfolio_ut:.1f}%")
            p3.metric("Coverage", f"{len(covered)}/{total}")
            st.caption("Portfolio percentages are weighted by hours. Open Performance for instrument targets and deeper analysis.")

    st.subheader("Priority attention queue")
    if not signals:
        st.success("No priority signal detected right now.")
    else:
        ordered = sorted(signals.items(), key=lambda item: (min(r for r, _ in item[1]), code_by_id.get(item[0], "")))
        for iid, items in ordered[:10]:
            category = instrument_categories.get(iid, "WATCH")
            messages = [msg for _, msg in sorted(items, key=lambda x: x[0])]
            st.markdown(_dash_priority_card(code_by_id.get(iid, "Instrument"), category, messages), unsafe_allow_html=True)

    phase_counts = {"Plan": 0, "Acquire": 0, "Qualify": 0, "Operate": 0, "Retired": 0}
    for i in dash_instruments:
        phase_counts[_dash_phase(i, str(i.get("id")) in retired_ids)] += 1
    st.subheader("Lifecycle portfolio")
    st.markdown(
        '<div class="v04-phase-grid">' + ''.join(
            f'<div class="v04-phase"><strong>{phase_counts[p]}</strong><b>{p}</b><span>{desc}</span></div>'
            for p, desc in [
                ("Plan", "Need / URS"), ("Acquire", "Quote / PR / PO / Receipt"),
                ("Qualify", "Install / IQ / OQ / PQ / Release / First Run"),
                ("Operate", "Routine control"), ("Retired", "Lifecycle closed"),
            ]
        ) + '</div>',
        unsafe_allow_html=True,
    )
    st.caption(f"Lifecycle population check: {sum(phase_counts.values())} = Total instruments {total}.")

    st.subheader("Quick action")
    action = st.radio(
        "Choose what you need to do",
        ["Continue Lifecycle", "New Need / Instrument", "Log Calibration", "Log Maintenance", "New Event", "Start Investigation"],
        horizontal=True,
        label_visibility="collapsed",
        key="v04_compact_quick_action",
    )
    guidance = {
        "Continue Lifecycle": ("↻", "Lifecycle", "Continue the highlighted controlled milestone."),
        "New Need / Instrument": ("＋", "Passport → Lifecycle", "Create identity, then record Need / Initiation."),
        "Log Calibration": ("◎", "Cal & PM", "Record the evidence-backed calibration result."),
        "Log Maintenance": ("⚙", "Cal & PM", "Record what was actually performed."),
        "New Event": ("⚠", "Events", "Record the observation first. Diagnose later."),
        "Start Investigation": ("🔎", "Investigate", "Preserve Expected / Actual / Changed / Unchanged / Evidence."),
    }
    icon, destination, copy = guidance[action]
    st.info(f"{icon} **{action} → {destination}** · {copy}")

    if dash_instruments:
        st.subheader("Instrument intelligence")
        option_map = {f"{i.get('instrument_code')} · {i.get('instrument_name') or 'Unnamed'}": i for i in dash_instruments}
        selected = st.selectbox("Inspect instrument", list(option_map.keys()), key="v04_dashboard_portfolio")
        inst = option_map[selected]
        iid = str(inst.get("id"))
        next_stage, progress = _dash_missing_stage(inst)
        retired = iid in retired_ids
        phase = _dash_phase(inst, retired)
        operational = str(inst.get("operational_status") or "Not set")
        routine_state = "Retired" if retired else ("Routine use" if _dash_stage_checks(inst)[-1][1] else "Not commissioned")
        category = instrument_categories.get(iid, "No current signal")
        st.markdown(
            f'<div class="v04-inst-card"><div class="v04-inst-head"><b>{escape(str(inst.get("instrument_code") or "Instrument"))} · {escape(str(inst.get("instrument_name") or "Unnamed"))}</b><span class="v04-badge">{escape(phase.upper())}</span></div><div class="v04-intel"><div class="v04-intel-item"><span>Lifecycle readiness</span><b>{"Closed" if retired else str(progress)+"%"}</b></div><div class="v04-intel-item"><span>Operational status</span><b>{escape(operational)}</b></div><div class="v04-intel-item"><span>Use state</span><b>{escape(routine_state)}</b></div><div class="v04-intel-item"><span>Attention</span><b>{escape(category)}</b></div></div><div class="v04-next">{"Lifecycle closed" if retired else "NEXT CONTROLLED STEP → "+escape(next_stage.upper())}</div></div>',
            unsafe_allow_html=True,
        )
        st.progress(1.0 if retired else progress / 100.0)
        missing = [label for label, done in _dash_stage_checks(inst) if not done]
        if missing and not retired:
            st.caption("Missing evidence → " + " · ".join(missing[:7]) + (" …" if len(missing) > 7 else ""))

# v0.5 Instrument Intelligence Dashboard
# UX is organized around user jobs-to-be-done and decision outcomes.
# KPI semantics: primary counts are unique instruments; signals remain separate.

from datetime import date
from html import escape


DASH_SELECT = (
    "id,instrument_code,instrument_name,instrument_type,operational_status,qualification_due,pm_due,calibration_due,"
    "need_identified_date,need_justification,intended_use,urs_reference,urs_approval_date,quotation_reference,quotation_date,"
    "pr_number,pr_approval_date,po_number,po_approval_date,expected_receiving_date,receiving_date,installation_date,"
    "iq_date,oq_date,pq_date,issuance_date,first_run_date,created_at"
)

ROLE_OPTIONS = [
    "QC Analyst",
    "Calibration / Maintenance",
    "QC Supervisor / Manager",
    "QA / Reviewer",
    "New setup / Team lead",
]

ROLE_COPY = {
    "QC Analyst": {
        "promise": "Record what happened fast, preserve the evidence, and know what to do next.",
        "goal": "Reduce manual searching and avoid turning assumptions into facts.",
        "actions": ["New Event", "Start Investigation", "Continue Lifecycle", "New Need / Instrument", "Log Calibration", "Log Maintenance"],
    },
    "Calibration / Maintenance": {
        "promise": "See what is due, overdue or OOC before it becomes an operational surprise.",
        "goal": "Keep routine controls current and the evidence trail audit-ready.",
        "actions": ["Log Calibration", "Log Maintenance", "Continue Lifecycle", "New Event", "Start Investigation", "New Need / Instrument"],
    },
    "QC Supervisor / Manager": {
        "promise": "See what needs attention, why it matters and where capacity or reliability is at risk.",
        "goal": "Turn instrument data into prioritized management decisions.",
        "actions": ["Continue Lifecycle", "Start Investigation", "Log Calibration", "Log Maintenance", "New Event", "New Need / Instrument"],
    },
    "QA / Reviewer": {
        "promise": "Review traceability, open quality signals and missing evidence without mixing fact with inference.",
        "goal": "Improve review confidence and reduce evidence gaps.",
        "actions": ["Start Investigation", "Continue Lifecycle", "New Event", "Log Calibration", "Log Maintenance", "New Need / Instrument"],
    },
    "New setup / Team lead": {
        "promise": "Get to first value quickly without rebuilding the whole tracker manually.",
        "goal": "Activate the workspace, import existing data and establish the lifecycle baseline.",
        "actions": ["New Need / Instrument", "Continue Lifecycle", "Log Calibration", "Log Maintenance", "New Event", "Start Investigation"],
    },
}


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


def _dash_card(label, value, note, tone="blue", icon="•"):
    return (
        f'<div class="v05-kpi {tone}">'
        f'<div class="v05-kpi-top"><span>{icon}</span><span>{escape(str(label))}</span></div>'
        f'<div class="v05-kpi-value">{escape(str(value))}</div>'
        f'<div class="v05-kpi-note">{escape(str(note))}</div></div>'
    )


def _dash_priority_card(code, category, messages):
    tone = {"ACT NOW": "critical", "REVIEW": "warning", "WATCH": "watch"}.get(category, "watch")
    icon = {"ACT NOW": "●", "REVIEW": "◆", "WATCH": "○"}.get(category, "○")
    detail = " · ".join(messages[:2])
    more = f" · +{len(messages)-2} more" if len(messages) > 2 else ""
    return (
        f'<div class="v05-priority {tone}"><div class="v05-priority-head">'
        f'<b>{icon} {escape(str(code))}</b><span>{escape(category)} · {len(messages)} signal(s)</span></div>'
        f'<div class="v05-priority-msg">{escape(detail + more)}</div></div>'
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


def _focus_message(role, *, total, act_ids, review_ids, cal_overdue_ids, pm_overdue_ids,
                   due30_ids, open_ooc_ids, open_event_ids, pre_first_run_ids, perf_covered):
    if total == 0:
        return (
            "ACTIVATE YOUR WORKSPACE",
            "Import your existing Excel tracker or add the first instrument. The fastest path to value is a real portfolio, not more setup.",
            "New Need / Instrument",
            "Activation",
        )
    if role == "QC Analyst":
        if open_event_ids:
            return ("PRESERVE THE OBSERVATION", f"{len(open_event_ids)} instrument(s) have open events. Record facts first, then investigate the highest-priority case.", "New Event", "Daily use")
        return ("KEEP THE INSTRUMENT MEMORY CURRENT", "No open event is demanding immediate attention. Use the app when something changes, not after the evidence is lost.", "New Event", "Daily use")
    if role == "Calibration / Maintenance":
        if cal_overdue_ids or pm_overdue_ids:
            return ("CONTROL OVERDUE WORK", f"{len(cal_overdue_ids)} calibration and {len(pm_overdue_ids)} PM overdue instrument(s) need controlled follow-up.", "Log Calibration" if cal_overdue_ids else "Log Maintenance", "Recurring control")
        if due30_ids:
            return ("PLAN THE NEXT 30 DAYS", f"{len(due30_ids)} instrument(s) have calibration, PM or qualification due within 30 days.", "Continue Lifecycle", "Recurring control")
        return ("KEEP ROUTINE CONTROL CURRENT", "No overdue routine-control signal is detected. Maintain evidence while it is fresh.", "Log Calibration", "Recurring control")
    if role == "QC Supervisor / Manager":
        if act_ids:
            return ("START WITH ACT NOW", f"{len(act_ids)} instrument(s) carry critical/high-priority signals. Review these before lower-priority work.", "Start Investigation", "Decision value")
        if review_ids:
            return ("REVIEW BEFORE IT BECOMES URGENT", f"{len(review_ids)} instrument(s) need management review. Resolve evidence gaps and control drift early.", "Continue Lifecycle", "Decision value")
        if perf_covered < total:
            return ("COMPLETE PERFORMANCE COVERAGE", f"Monthly performance coverage is {perf_covered}/{total}. Better capacity decisions require better coverage.", "Continue Lifecycle", "Management retention")
        return ("PORTFOLIO IS CONTROLLED", "Use Performance and Reports to review availability, utilization and capacity before adding or replacing equipment.", "Continue Lifecycle", "Management retention")
    if role == "QA / Reviewer":
        if open_ooc_ids:
            return ("REVIEW OPEN OOC FIRST", f"{len(open_ooc_ids)} instrument(s) have open calibration OOC signals requiring impact/investigation closure.", "Start Investigation", "Trust")
        if open_event_ids:
            return ("REVIEW OPEN EVENTS", f"{len(open_event_ids)} instrument(s) have open events. Check Observed / Inferred / Unknown separation and evidence completeness.", "Start Investigation", "Trust")
        return ("VERIFY TRACEABILITY", "No current OOC/open-event signal dominates. Review lifecycle completeness and missing evidence before report use.", "Continue Lifecycle", "Trust")
    if pre_first_run_ids:
        return ("MOVE THE PORTFOLIO TO CONTROLLED USE", f"{len(pre_first_run_ids)} instrument(s) are still before controlled First Run. Complete the next lifecycle milestone.", "Continue Lifecycle", "Activation")
    return ("EXPAND VALUE, NOT DATA ENTRY", "Your baseline exists. Add monthly performance and use reports so the system supports real management decisions.", "Continue Lifecycle", "Retention")


st.markdown(
    """
<style>
.v05-hero{border:1px solid rgba(214,184,95,.45);border-radius:24px;padding:1.25rem;margin:.35rem 0 1rem;color:#fff;background:#07111f;box-shadow:0 14px 34px rgba(2,12,27,.14)}
.v05-hero h2{color:#fff!important;margin:.12rem 0 .4rem!important}.v05-hero p{margin:.15rem 0;color:#dbe7f1}.v05-hero .gold{color:#e1c56d;font-weight:800}.v05-kicker{font-size:.75rem;letter-spacing:.12em;color:#55d9ea;font-weight:900}.v05-micro{font-size:.76rem!important;color:#8fa7c1!important;letter-spacing:.04em}
.v05-focus{border:1px solid #dbe3ec;border-radius:18px;padding:1rem;margin:.55rem 0 1rem;background:linear-gradient(135deg,#f8fbff,#fff);box-shadow:0 5px 16px rgba(15,23,42,.04)}
.v05-focus-kicker{font-size:.67rem;letter-spacing:.09em;font-weight:900;color:#2876a7}.v05-focus h3{margin:.22rem 0 .28rem!important;color:#0f2742!important}.v05-focus p{margin:.2rem 0;color:#5f7185}.v05-focus-meta{display:flex;gap:.4rem;flex-wrap:wrap;margin-top:.65rem}.v05-pill{font-size:.68rem;border:1px solid #dbe3ec;border-radius:999px;padding:.25rem .48rem;color:#486174;background:#fff;font-weight:750}.v05-pill.gold{border-color:#ead7a0;color:#8b650e;background:#fffcf3}
.v05-system{display:flex;align-items:center;justify-content:space-between;gap:.7rem;border:1px solid #183a4d;border-radius:999px;padding:.62rem .9rem;margin:.35rem 0 1rem;background:#071827;color:#cfeaf0}.v05-system-left{display:flex;align-items:center;gap:.55rem;font-weight:800}.v05-dot{width:12px;height:12px;border-radius:50%;background:#20c997;box-shadow:0 0 0 5px rgba(32,201,151,.12)}.v05-system.critical .v05-dot{background:#e55353}.v05-system.review .v05-dot{background:#d9a62e}.v05-system.watch .v05-dot{background:#35a7d3}.v05-system-note{font-size:.76rem;color:#8fb0bf;text-align:right}
.v05-kpi-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:.65rem;margin:.75rem 0 1rem}.v05-kpi{border:1px solid #e2e8f0;border-radius:17px;padding:.82rem .78rem;background:#fff;box-shadow:0 5px 16px rgba(15,23,42,.05)}.v05-kpi-top{display:flex;align-items:center;gap:.35rem;font-size:.75rem;color:#64748b;font-weight:800}.v05-kpi-value{font-size:1.75rem;color:#0f2742;font-weight:850;line-height:1.12;margin:.18rem 0}.v05-kpi-note{font-size:.73rem;color:#94a3b8}.v05-kpi.red{border-top:3px solid #d64545}.v05-kpi.amber{border-top:3px solid #d7a52c}.v05-kpi.green{border-top:3px solid #16a36f}.v05-kpi.blue{border-top:3px solid #2876a7}
.v05-attention{border:1px solid #e2e8f0;border-radius:18px;padding:1rem;margin:.4rem 0 1rem;background:linear-gradient(135deg,#f8fafc,#fff)}.v05-attention-head{display:flex;justify-content:space-between;gap:.8rem;align-items:center}.v05-attention strong{color:#0f2742}.v05-attention p{color:#64748b;font-size:.82rem;margin:.25rem 0}.v05-chips{display:flex;gap:.35rem;flex-wrap:wrap}.v05-chip{border-radius:999px;padding:.28rem .48rem;font-size:.68rem;font-weight:850;border:1px solid #e2e8f0;background:#fff}.v05-chip.red{color:#b42318;border-color:#f1b7b2;background:#fff8f7}.v05-chip.amber{color:#8b650e;border-color:#ead7a0;background:#fffcf3}.v05-chip.blue{color:#176187;border-color:#b9ddeb;background:#f5fbff}
.v05-priority{border:1px solid #e2e8f0;border-left:5px solid #94a3b8;border-radius:15px;padding:.72rem .8rem;margin:.48rem 0;background:#fff}.v05-priority.critical{border-left-color:#d64545;background:#fffafa}.v05-priority.warning{border-left-color:#d7a52c;background:#fffdf7}.v05-priority.watch{border-left-color:#2876a7}.v05-priority-head{display:flex;justify-content:space-between;gap:.5rem}.v05-priority-head b{color:#1e293b}.v05-priority-head span{font-size:.65rem;font-weight:800;color:#64748b}.v05-priority-msg{font-size:.82rem;color:#64748b;margin-top:.15rem}
.v05-phase-grid{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:.55rem;margin:.6rem 0 1rem}.v05-phase{border:1px solid #e2e8f0;border-radius:14px;padding:.7rem;background:#fff}.v05-phase b{display:block;color:#0f2742}.v05-phase span{font-size:.75rem;color:#64748b}.v05-phase strong{font-size:1.25rem;color:#d1a733}
.v05-inst-card{border:1px solid #15354a;border-radius:18px;padding:.95rem;margin:.55rem 0;background:linear-gradient(145deg,#071422,#0c2032);color:#dceaf2}.v05-inst-head{display:flex;justify-content:space-between;gap:.5rem}.v05-inst-head b{color:#fff}.v05-badge{font-size:.7rem;font-weight:800;padding:.2rem .5rem;border-radius:999px;background:#173f55;color:#75dbea}.v05-intel{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:.45rem;margin-top:.65rem}.v05-intel-item{border:1px solid rgba(255,255,255,.08);border-radius:12px;padding:.55rem;background:rgba(255,255,255,.03)}.v05-intel-item span{display:block;color:#7f9aaa;font-size:.64rem;text-transform:uppercase}.v05-intel-item b{display:block;color:#fff;margin-top:.12rem;font-size:.86rem}.v05-next{margin-top:.6rem;color:#e1c56d;font-weight:800}
@media(max-width:800px){.v05-kpi-grid{grid-template-columns:1fr 1fr}.v05-phase-grid{grid-template-columns:1fr 1fr}.v05-phase:last-child{grid-column:1/-1}.v05-intel{grid-template-columns:1fr 1fr}.v05-system{border-radius:17px;align-items:flex-start}.v05-system-note{font-size:.7rem}.v05-attention-head{align-items:flex-start;flex-direction:column}.v05-kpi-value{font-size:1.48rem}.v05-focus h3{font-size:1.15rem!important}}
</style>
""",
    unsafe_allow_html=True,
)

st.markdown(
    """<div class="v05-hero v03-dashboard-hero"><div class="v05-kicker">QC INSTRUMENT INTELLIGENCE</div><h2>Instrument Lifecycle Control Center</h2><p>Know what needs action now — and why — without losing the evidence trail.</p><p class="gold">DON'T GUESS. FOLLOW THE EVIDENCE.</p><p class="v05-micro">ENTER LESS · DECIDE BETTER · KEEP THE INSTRUMENT STORY CONNECTED</p></div>""",
    unsafe_allow_html=True,
)

role = st.selectbox(
    "What is your main job in the app right now?",
    ROLE_OPTIONS,
    key="v05_user_work_mode",
    help="This only changes the order and emphasis of the experience; it does not change database permissions.",
)
role_info = ROLE_COPY[role]
st.caption(f"{role_info['promise']} · {role_info['goal']}")


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

    current_month = date.today().replace(day=1)
    current_perf_rows = []
    perf_covered_ids = set()
    if perf_ok and dash_perf:
        current_perf_rows = [
            r for r in dash_perf
            if _parse_date(r.get("month_start"))
            and _parse_date(r.get("month_start")).replace(day=1) == current_month
        ]
        perf_covered_ids = {str(r.get("instrument_id")) for r in current_perf_rows}

    focus_title, focus_text, focus_action, business_outcome = _focus_message(
        role,
        total=total,
        act_ids=act_ids,
        review_ids=review_ids,
        cal_overdue_ids=cal_overdue_ids,
        pm_overdue_ids=pm_overdue_ids,
        due30_ids=due30_ids,
        open_ooc_ids=open_ooc_ids,
        open_event_ids=open_event_ids,
        pre_first_run_ids=pre_first_run_ids,
        perf_covered=len(perf_covered_ids),
    )
    st.markdown(
        f'<div class="v05-focus"><div class="v05-focus-kicker">YOUR FOCUS · {escape(role.upper())}</div>'
        f'<h3>{escape(focus_title)}</h3><p>{escape(focus_text)}</p>'
        f'<div class="v05-focus-meta"><span class="v05-pill gold">PRIMARY → {escape(focus_action)}</span>'
        f'<span class="v05-pill">OUTCOME → {escape(business_outcome)}</span></div></div>',
        unsafe_allow_html=True,
    )

    state_label = "ACTION REQUIRED" if act_ids else "REVIEW NEEDED" if review_ids else "SYSTEM READY · WATCH" if watch_ids else "SYSTEM READY"
    state_css = "critical" if act_ids else "review" if review_ids else "watch" if watch_ids else "ready"
    state_note = f"{len(attention_ids)} of {total} instrument(s) need attention · {total_signal_count} signal(s)"
    st.markdown(
        f'<div class="v05-system {state_css}"><div class="v05-system-left"><span class="v05-dot"></span><span>{escape(state_label)}</span></div><div class="v05-system-note">{escape(state_note)}</div></div>',
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
    st.markdown(f'<div class="v05-kpi-grid">{cards}</div>', unsafe_allow_html=True)

    st.markdown(
        f'<div class="v05-attention"><div class="v05-attention-head"><div><strong>What needs attention now?</strong><p>Instrument counts stay instrument counts. Signals stay signals.</p></div><b>{len(attention_ids)} / {total}</b></div><div class="v05-chips"><span class="v05-chip red">ACT NOW {len(act_ids)}</span><span class="v05-chip amber">REVIEW {len(review_ids)}</span><span class="v05-chip blue">WATCH {len(watch_ids)}</span><span class="v05-chip">SIGNALS {total_signal_count}</span></div></div>',
        unsafe_allow_html=True,
    )

    if current_perf_rows:
        planned_total = available_total = productive_total = 0.0
        covered = set()
        for r in current_perf_rows:
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
            st.caption("Weighted by hours. Performance becomes more decision-useful as portfolio coverage increases.")

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
        '<div class="v05-phase-grid">' + ''.join(
            f'<div class="v05-phase"><strong>{phase_counts[p]}</strong><b>{p}</b><span>{desc}</span></div>'
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
    action_options = role_info["actions"]
    action = st.radio(
        "Choose what you need to do",
        action_options,
        horizontal=True,
        label_visibility="collapsed",
        key="v05_role_quick_action",
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

    if total == 0:
        st.success("Fastest onboarding path: import your existing Excel tracker, then complete only the missing lifecycle evidence. Do not retype what already exists.")
        st.caption("Excel import recognizes fields whose headers match the application template. Download the template first when column names differ.")

    if dash_instruments:
        st.subheader("Instrument intelligence")
        option_map = {f"{i.get('instrument_code')} · {i.get('instrument_name') or 'Unnamed'}": i for i in dash_instruments}
        selected = st.selectbox("Inspect instrument", list(option_map.keys()), key="v05_dashboard_portfolio")
        inst = option_map[selected]
        iid = str(inst.get("id"))
        next_stage, progress = _dash_missing_stage(inst)
        retired = iid in retired_ids
        phase = _dash_phase(inst, retired)
        operational = str(inst.get("operational_status") or "Not set")
        routine_state = "Retired" if retired else ("Routine use" if _dash_stage_checks(inst)[-1][1] else "Not commissioned")
        category = instrument_categories.get(iid, "No current signal")
        st.markdown(
            f'<div class="v05-inst-card"><div class="v05-inst-head"><b>{escape(str(inst.get("instrument_code") or "Instrument"))} · {escape(str(inst.get("instrument_name") or "Unnamed"))}</b><span class="v05-badge">{escape(phase.upper())}</span></div><div class="v05-intel"><div class="v05-intel-item"><span>Lifecycle readiness</span><b>{"Closed" if retired else str(progress)+"%"}</b></div><div class="v05-intel-item"><span>Operational status</span><b>{escape(operational)}</b></div><div class="v05-intel-item"><span>Use state</span><b>{escape(routine_state)}</b></div><div class="v05-intel-item"><span>Attention</span><b>{escape(category)}</b></div></div><div class="v05-next">{"Lifecycle closed" if retired else "NEXT CONTROLLED STEP → "+escape(next_stage.upper())}</div></div>',
            unsafe_allow_html=True,
        )
        st.progress(1.0 if retired else progress / 100.0)
        missing = [label for label, done in _dash_stage_checks(inst) if not done]
        if missing and not retired:
            st.caption("Missing evidence → " + " · ".join(missing[:7]) + (" …" if len(missing) > 7 else ""))

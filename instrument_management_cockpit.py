# Yahia QC Instrument Lifecycle — Instrument Management Cockpit
# One instrument. One screen. One decision view.

from __future__ import annotations

from datetime import date, timedelta
from html import escape

import pandas as pd
import streamlit as st


def _cockpit_rows(table: str, order: str | None = None):
    try:
        rows, _, ok = _db_list(table, "*", order)
        return rows if ok else []
    except Exception:
        return []


def _cockpit_date(value):
    try:
        return pd.to_datetime(value).date() if value else None
    except Exception:
        return None


def _cockpit_days(value):
    d = _cockpit_date(value)
    return (d - date.today()).days if d else None


def _cockpit_due(value, ar=False):
    days = _cockpit_days(value)
    if days is None:
        return "غير مسجل" if ar else "Not set"
    if days < 0:
        return f"متأخر {abs(days)} يوم" if ar else f"OVERDUE {abs(days)}d"
    if days == 0:
        return "مستحق اليوم" if ar else "Due today"
    if days <= 30:
        return f"خلال {days} يوم" if ar else f"Due in {days}d"
    return f"بعد {days} يوم" if ar else f"{days}d remaining"


def _cockpit_pct(value):
    try:
        return f"{float(value):.1f}%"
    except Exception:
        return "—"


def _cockpit_num(value):
    try:
        return f"{float(value):.1f}"
    except Exception:
        return "—"


def _cockpit_perf(row):
    if not row:
        return {"availability": None, "utilization": None, "unplanned": None, "productive": None, "idle": None}
    try:
        scheduled = float(row.get("scheduled_hours") or 0)
        planned = float(row.get("planned_downtime_hours") or 0)
        unplanned = float(row.get("unplanned_downtime_hours") or 0)
        productive = float(row.get("productive_run_hours") or 0)
        planned_operating = max(0.0, scheduled - planned)
        available = max(0.0, planned_operating - unplanned)
        return {
            "availability": (available / planned_operating * 100) if planned_operating > 0 else None,
            "utilization": (productive / available * 100) if available > 0 else None,
            "unplanned": unplanned,
            "productive": productive,
            "idle": max(0.0, available - productive),
        }
    except Exception:
        return {"availability": None, "utilization": None, "unplanned": None, "productive": None, "idle": None}


def _cockpit_target(value):
    try:
        v = float(value)
        return v if 0 <= v <= 100 else None
    except Exception:
        return None


def _cockpit_lifecycle(inst, retired=False):
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
        ("Release", bool(inst.get("issuance_date") and inst.get("pq_date"))),
        ("First Run", bool(inst.get("first_run_date") and inst.get("issuance_date") and inst.get("pq_date"))),
    ]
    completed = sum(1 for _, done in checks if done)
    pct = int(round(completed / len(checks) * 100))
    next_stage = next((name for name, done in checks if not done), "Routine Operation")
    if retired:
        next_stage = "Retired"
        pct = 100
    return checks, pct, next_stage


def _cockpit_stage_group(next_stage, retired=False):
    if retired:
        return "RETIRED"
    if next_stage in {"Need", "URS"}:
        return "PLAN"
    if next_stage in {"Quotation", "PR", "PO", "Receiving"}:
        return "ACQUIRE"
    if next_stage in {"Installation", "IQ", "OQ", "PQ", "Release", "First Run"}:
        return "QUALIFY"
    return "OPERATE"


def _cockpit_signal(perf, inst, ar=False):
    av = perf.get("availability")
    ut = perf.get("utilization")
    ta = _cockpit_target(inst.get("target_availability_pct"))
    tu = _cockpit_target(inst.get("target_utilization_pct"))
    if av is None or ut is None:
        return ("بيانات أداء غير مكتملة" if ar else "Performance data incomplete", "watch")
    if ta is not None and av < ta and tu is not None and ut >= tu:
        return ("مخاطر سعة / اعتمادية" if ar else "Capacity / reliability risk", "red")
    if ta is not None and av < ta:
        return ("الإتاحة أقل من الهدف" if ar else "Availability below target", "amber")
    if tu is not None and ut < tu:
        return ("سعة متاحة غير مستغلة" if ar else "Available capacity underused", "blue")
    if (ta is not None or tu is not None):
        return ("ضمن الهدف" if ar else "On target", "green")
    return ("لا توجد أهداف أداء مسجلة" if ar else "No performance targets configured", "watch")


def _cockpit_recurrent(events_for_inst, ar=False):
    cutoff = date.today() - timedelta(days=180)
    counts = {}
    for e in events_for_inst:
        d = _cockpit_date(e.get("event_date"))
        if d and d < cutoff:
            continue
        key = str(e.get("subsystem") or e.get("event_type") or "General / Unknown").strip()
        if key:
            counts[key] = counts.get(key, 0) + 1
    if not counts:
        return ("لا يوجد نمط متكرر ظاهر" if ar else "No recurrent failure pattern detected", 0)
    key, count = max(counts.items(), key=lambda x: x[1])
    if count < 2:
        return ("لا يوجد نمط متكرر ظاهر" if ar else "No recurrent failure pattern detected", count)
    return key, count


def _cockpit_next_action(inst, lifecycle_next, perf, open_events, open_ooc, health, retired, ar=False):
    evidence = []
    status = str(inst.get("operational_status") or "Active")

    if retired:
        return (
            "أغلق سجل دورة الحياة وتأكد من الأرشفة والتكهين المعتمد." if ar else "Close the lifecycle record and confirm controlled archive / decommissioning evidence.",
            ["Retirement / decommissioning recorded"],
            "green",
        )

    critical_open = [e for e in open_events if str(e.get("severity") or "") in {"Critical", "High"}]
    if open_ooc or critical_open or status in {"Out of Service", "Restricted"}:
        if open_ooc:
            evidence.append(f"{len(open_ooc)} open calibration OOC")
        if critical_open:
            evidence.append(f"{len(critical_open)} Critical/High open event(s)")
        if status in {"Out of Service", "Restricted"}:
            evidence.append(f"Operational status: {status}")
        return (
            "راجع الأدلة وImpact Assessment والتحقيق قبل أي عودة للاستخدام الروتيني." if ar else "Review evidence, impact assessment and investigation before any return to routine use.",
            evidence,
            "red",
        )

    overdue = []
    for label, field in [("Calibration", "calibration_due"), ("PM", "pm_due"), ("Qualification", "qualification_due")]:
        days = _cockpit_days(inst.get(field))
        if days is not None and days < 0:
            overdue.append((label, abs(days)))
    if overdue:
        label, days = sorted(overdue, key=lambda x: x[1], reverse=True)[0]
        return (
            (f"نفّذ إجراء {label} المتأخر وفق الإجراء المعتمد قبل الاعتماد على الجهاز." if ar else f"Resolve overdue {label} according to the approved procedure before relying on the instrument."),
            [f"{label} overdue by {days} day(s)"],
            "red",
        )

    if lifecycle_next != "Routine Operation":
        return (
            (f"أكمل المرحلة التالية في دورة الحياة: {lifecycle_next}." if ar else f"Complete the next lifecycle milestone: {lifecycle_next}."),
            [f"Lifecycle next milestone: {lifecycle_next}"],
            "amber",
        )

    signal, tone = _cockpit_signal(perf, inst, ar=False)
    if signal == "Capacity / reliability risk":
        return (
            "راجع أسباب التوقف غير المخطط مع تركيز الحمل قبل التفكير في إضافة سعة أو استبدال الجهاز." if ar else "Review unplanned downtime and workload concentration before deciding on added or replacement capacity.",
            [f"Availability {_cockpit_pct(perf.get('availability'))}", f"Utilization {_cockpit_pct(perf.get('utilization'))}"],
            "red",
        )
    if signal == "Availability below target":
        return (
            "راجع Reliability drivers والتوقف غير المخطط وفعالية الصيانة." if ar else "Review reliability drivers, unplanned downtime and maintenance effectiveness.",
            [f"Availability {_cockpit_pct(perf.get('availability'))}"],
            "amber",
        )
    if signal == "Available capacity underused":
        return (
            "راجع الجدولة وتوزيع الطرق والطلب الفعلي قبل طلب جهاز إضافي." if ar else "Review scheduling, method allocation and real demand before requesting additional capacity.",
            [f"Utilization {_cockpit_pct(perf.get('utilization'))}", f"Idle available {_cockpit_num(perf.get('idle'))} h"],
            "blue",
        )
    if perf.get("availability") is None:
        return (
            "سجّل بيانات الأداء الشهرية حتى تصبح قرارات الإتاحة والاستخدام مبنية على دليل." if ar else "Record monthly performance hours so availability and utilization decisions are evidence-based.",
            ["No usable monthly performance record"],
            "blue",
        )
    if health < 90:
        return (
            "راجع إشارات Health Score وأغلق أعلى سبب قابل للتصرف ثم استمر في الـtrend." if ar else "Review Health Score signals, close the highest actionable item, then continue trending.",
            [f"Health score {health}/100"],
            "amber",
        )
    return (
        "استمر على الضوابط الحالية وراقب الـtrend الشهري وأي نمط متكرر جديد." if ar else "Maintain current controls and keep trending monthly performance and recurrent failure signals.",
        ["No higher-priority evidence signal detected"],
        "green",
    )


def render_instrument_management_cockpit():
    lang = st.radio("Cockpit language | لغة لوحة القرار", ["العربية", "English"], horizontal=True, key="cockpit_language")
    ar = lang == "العربية"

    instruments = _cockpit_rows("instruments", "instrument_code.asc")
    if not instruments:
        st.info("أنشئ أو ارفع Instrument Passport أولًا." if ar else "Create or import an Instrument Passport first.")
        return

    events_all = _cockpit_rows("instrument_events", "event_date.desc")
    components_all = _cockpit_rows("instrument_components", "created_at.desc")
    maintenance_all = _cockpit_rows("maintenance_records", "maintenance_date.desc")
    calibrations_all = _cockpit_rows("calibration_records", "calibration_date.desc")
    performance_all = _cockpit_rows("instrument_monthly_performance", "month_start.desc")
    retirements_all = _cockpit_rows("instrument_retirements", "created_at.desc")
    reviews_all = _cockpit_rows("instrument_performance_reviews", "review_date.desc")

    options = {f"{i.get('instrument_code') or 'Instrument'} · {i.get('instrument_name') or 'Unnamed'}": i for i in instruments}
    selected = st.selectbox("الجهاز | Instrument", list(options.keys()), key="cockpit_instrument")
    inst = options[selected]
    iid = str(inst.get("id"))

    events_i = [e for e in events_all if str(e.get("instrument_id")) == iid]
    open_events = [e for e in events_i if str(e.get("event_status") or "") != "Closed"]
    components_i = [c for c in components_all if str(c.get("instrument_id")) == iid]
    maintenance_i = [m for m in maintenance_all if str(m.get("instrument_id")) == iid]
    calibrations_i = [c for c in calibrations_all if str(c.get("instrument_id")) == iid]
    open_ooc = [c for c in calibrations_i if str(c.get("result") or "").upper() == "OOC" and str(c.get("ooc_status") or "Open") not in {"Closed", "Resolved", "Not applicable"}]
    performance_i = [p for p in performance_all if str(p.get("instrument_id")) == iid]
    performance_i = sorted(performance_i, key=lambda r: str(r.get("month_start") or ""), reverse=True)
    latest_perf_row = performance_i[0] if performance_i else None
    perf = _cockpit_perf(latest_perf_row)
    retired_row = next((r for r in retirements_all if str(r.get("instrument_id")) == iid and r.get("decommission_date")), None)
    retired = bool(retired_row)
    reviews_i = [r for r in reviews_all if str(r.get("instrument_id")) == iid]

    checks, lifecycle_pct, lifecycle_next = _cockpit_lifecycle(inst, retired)
    phase = _cockpit_stage_group(lifecycle_next, retired)

    try:
        health, health_reasons = health_score_v2(inst, events_all, components_all)
        health_label = health_state(health)
    except Exception:
        health, health_reasons, health_label = 100, [], "Healthy"

    signal, signal_tone = _cockpit_signal(perf, inst, ar)
    next_action, action_evidence, action_tone = _cockpit_next_action(inst, lifecycle_next, perf, open_events, open_ooc, health, retired, ar)
    recurrent_label, recurrent_count = _cockpit_recurrent(events_i, ar)

    latest_maintenance = maintenance_i[0] if maintenance_i else None
    latest_calibration = calibrations_i[0] if calibrations_i else None
    latest_review = reviews_i[0] if reviews_i else None

    due_candidates = []
    for label, field in [("Calibration", "calibration_due"), ("PM", "pm_due"), ("Qualification", "qualification_due")]:
        d = _cockpit_date(inst.get(field))
        if d:
            due_candidates.append((d, label))
    for c in components_i:
        d = _cockpit_date(c.get("replacement_due"))
        if d and str(c.get("status") or "Active") == "Active":
            due_candidates.append((d, f"Component: {c.get('component_name') or 'item'}"))
    next_due = min(due_candidates, key=lambda x: x[0]) if due_candidates else None

    direction = "rtl" if ar else "ltr"
    align = "right" if ar else "left"
    st.markdown(
        f"""
<style>
.cockpit-wrap{{direction:{direction};text-align:{align};}}
.cockpit-hero{{border:1px solid rgba(214,184,95,.48);border-radius:24px;padding:1.15rem 1.2rem;background:linear-gradient(135deg,#06121f,#0b2336);color:#dceaf3;box-shadow:0 14px 34px rgba(2,12,27,.18);margin:.35rem 0 1rem}}
.cockpit-kicker{{font-size:.72rem;letter-spacing:.12em;color:#58d5e7;font-weight:900}}.cockpit-hero h2{{color:#fff!important;margin:.28rem 0 .25rem!important}}.cockpit-hero .gold{{color:#e2c66d;font-weight:850}}.cockpit-meta{{color:#93a9ba;font-size:.84rem}}
.cockpit-grid{{display:grid;grid-template-columns:repeat(6,minmax(0,1fr));gap:.55rem;margin:.7rem 0 1rem}}.cockpit-card{{border:1px solid #e2e8f0;border-radius:16px;background:#fff;padding:.72rem;box-shadow:0 5px 16px rgba(15,23,42,.05)}}.cockpit-card span{{display:block;color:#64748b;font-size:.69rem;font-weight:800}}.cockpit-card b{{display:block;color:#0f2742;font-size:1.35rem;margin:.12rem 0}}.cockpit-card small{{color:#94a3b8;font-size:.66rem}}.cockpit-card.red{{border-top:3px solid #d64545}}.cockpit-card.amber{{border-top:3px solid #d4a92e}}.cockpit-card.green{{border-top:3px solid #16a36f}}.cockpit-card.blue{{border-top:3px solid #2876a7}}
.cockpit-decision{{border-radius:18px;padding:1rem 1.05rem;margin:.7rem 0 1rem;border:1px solid #e2e8f0;background:#fff}}.cockpit-decision.red{{border-{('right' if ar else 'left')}:6px solid #d64545;background:#fffafa}}.cockpit-decision.amber{{border-{('right' if ar else 'left')}:6px solid #d4a92e;background:#fffdf7}}.cockpit-decision.blue{{border-{('right' if ar else 'left')}:6px solid #2876a7;background:#f8fcff}}.cockpit-decision.green{{border-{('right' if ar else 'left')}:6px solid #16a36f;background:#fbfffd}}.cockpit-decision h3{{margin:.05rem 0 .35rem!important;color:#0f2742!important}}.cockpit-decision p{{margin:.2rem 0;color:#334155}}.cockpit-evidence{{color:#64748b!important;font-size:.8rem!important}}
.cockpit-facts{{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:.55rem;margin:.6rem 0 1rem}}.cockpit-fact{{border:1px solid #e2e8f0;border-radius:14px;padding:.7rem;background:#f8fafc}}.cockpit-fact span{{display:block;font-size:.68rem;color:#64748b}}.cockpit-fact b{{display:block;color:#0f2742;margin-top:.12rem}}
.cockpit-stage{{display:flex;gap:.3rem;flex-wrap:wrap;margin:.45rem 0 .8rem}}.cockpit-stage span{{border-radius:999px;padding:.3rem .48rem;font-size:.67rem;font-weight:800;border:1px solid #dbe3ec;background:#fff;color:#64748b}}.cockpit-stage span.done{{background:#effaf5;color:#08784e;border-color:#bfe8d7}}.cockpit-stage span.current{{background:#fff8df;color:#89690e;border-color:#ead491}}
@media(max-width:800px){{.cockpit-grid{{grid-template-columns:1fr 1fr}}.cockpit-facts{{grid-template-columns:1fr 1fr}}.cockpit-card b{{font-size:1.22rem}}}}
</style>
<div class="cockpit-wrap">
<div class="cockpit-hero">
<div class="cockpit-kicker">INSTRUMENT MANAGEMENT COCKPIT</div>
<h2>{escape(str(inst.get('instrument_code') or 'Instrument'))} · {escape(str(inst.get('instrument_name') or 'Unnamed'))}</h2>
<div class="cockpit-meta">{escape(str(inst.get('manufacturer') or '—'))} · {escape(str(inst.get('model') or '—'))} · S/N {escape(str(inst.get('serial_number') or '—'))}</div>
<p><b>{'مرحلة دورة الحياة' if ar else 'Lifecycle phase'}:</b> {escape(phase)} · <b>{'الحالة التشغيلية' if ar else 'Operational status'}:</b> {escape(str(inst.get('operational_status') or 'Active'))}</p>
<p class="gold">ONE INSTRUMENT · ONE SCREEN · ONE DECISION VIEW</p>
</div>
</div>
""",
        unsafe_allow_html=True,
    )

    latest_month = str(latest_perf_row.get("month_start"))[:7] if latest_perf_row else "—"
    cards = [
        ("Health Score", f"{health}/100", health_label, "green" if health >= 90 else "amber" if health >= 75 else "red"),
        (("اكتمال دورة الحياة" if ar else "Lifecycle completion"), f"{lifecycle_pct}%", lifecycle_next, "green" if lifecycle_pct == 100 else "amber"),
        (("الإتاحة" if ar else "Availability"), _cockpit_pct(perf.get("availability")), latest_month, "green" if perf.get("availability") is not None and (_cockpit_target(inst.get("target_availability_pct")) is None or perf.get("availability") >= _cockpit_target(inst.get("target_availability_pct"))) else "red"),
        (("الاستخدام" if ar else "Utilization"), _cockpit_pct(perf.get("utilization")), latest_month, "blue"),
        (("الأحداث المفتوحة" if ar else "Open events"), len(open_events), (f"OOC {len(open_ooc)}"), "red" if open_events or open_ooc else "green"),
        (("الإشارة الحالية" if ar else "Current signal"), signal, ("evidence-based" if not ar else "مبنية على الدليل"), signal_tone),
    ]
    st.markdown('<div class="cockpit-grid">' + ''.join(f'<div class="cockpit-card {tone}"><span>{escape(str(label))}</span><b>{escape(str(value))}</b><small>{escape(str(note))}</small></div>' for label, value, note, tone in cards) + '</div>', unsafe_allow_html=True)

    evidence_text = " · ".join(action_evidence) if action_evidence else "—"
    st.markdown(
        f'<div class="cockpit-decision {action_tone}"><h3>{"🎯 الخطوة التالية الأفضل" if ar else "🎯 NEXT BEST ACTION"}</h3><p><b>{escape(next_action)}</b></p><p class="cockpit-evidence">{"لماذا؟" if ar else "Why?"} {escape(evidence_text)}</p><p class="cockpit-evidence">{"هذه إشارة لدعم القرار وليست إثباتًا للسبب الجذري." if ar else "This is a decision-support signal, not proof of root cause."}</p></div>',
        unsafe_allow_html=True,
    )

    st.markdown("### " + ("🧭 موضع الجهاز في دورة الحياة" if ar else "🧭 Lifecycle position"))
    chips = []
    current_seen = False
    for name, done in checks:
        cls = "done" if done else ("current" if not current_seen else "")
        if not done and not current_seen:
            current_seen = True
        chips.append(f'<span class="{cls}">{"✓ " if done else "→ " if cls == "current" else ""}{escape(name)}</span>')
    st.markdown('<div class="cockpit-stage">' + ''.join(chips) + '</div>', unsafe_allow_html=True)
    st.progress(lifecycle_pct / 100.0)

    next_due_label = "—"
    if next_due:
        next_due_label = f"{next_due[1]} · {next_due[0]} · {_cockpit_due(next_due[0], ar)}"
    facts = [
        (("آخر صيانة" if ar else "Last maintenance"), (str(latest_maintenance.get("maintenance_date")) if latest_maintenance else "—")),
        (("آخر معايرة" if ar else "Last calibration"), (str(latest_calibration.get("calibration_date")) if latest_calibration else "—")),
        (("الاستحقاق الأقرب" if ar else "Next due"), next_due_label),
        (("النمط المتكرر" if ar else "Top recurrent pattern"), f"{recurrent_label}" + (f" ×{recurrent_count}" if recurrent_count >= 2 else "")),
        (("التوقف غير المخطط" if ar else "Unplanned downtime"), f"{_cockpit_num(perf.get('unplanned'))} h"),
        (("الساعات الإنتاجية" if ar else "Productive run hours"), f"{_cockpit_num(perf.get('productive'))} h"),
        (("السعة المتاحة غير المستغلة" if ar else "Idle available capacity"), f"{_cockpit_num(perf.get('idle'))} h"),
        (("آخر Performance Review" if ar else "Last performance review"), (str(latest_review.get("review_date")) if latest_review else "—")),
    ]
    st.markdown('<div class="cockpit-facts">' + ''.join(f'<div class="cockpit-fact"><span>{escape(str(k))}</span><b>{escape(str(v))}</b></div>' for k, v in facts) + '</div>', unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("### " + ("⚠ إشارات تحتاج انتباه" if ar else "⚠ Attention signals"))
        attention = []
        status = str(inst.get("operational_status") or "Active")
        if status != "Active":
            attention.append(("Operational status", status))
        for label, field in [("Calibration", "calibration_due"), ("PM", "pm_due"), ("Qualification", "qualification_due")]:
            days = _cockpit_days(inst.get(field))
            if days is not None and days <= 30:
                attention.append((label, _cockpit_due(inst.get(field), ar)))
        if open_events:
            attention.append(("Open events", str(len(open_events))))
        if open_ooc:
            attention.append(("Open OOC", str(len(open_ooc))))
        if health_reasons:
            attention.extend([("Health", str(x)) for x in health_reasons[:3]])
        if attention:
            st.dataframe(pd.DataFrame(attention, columns=[("الإشارة" if ar else "Signal"), ("التفصيل" if ar else "Detail")]), use_container_width=True, hide_index=True)
        else:
            st.success("لا توجد إشارة حرجة حالية." if ar else "No current critical attention signal detected.")

    with c2:
        st.markdown("### " + ("📌 آخر دليل تشغيلي" if ar else "📌 Latest operational evidence"))
        evidence_rows = []
        if latest_calibration:
            evidence_rows.append({"Type": "Calibration", "Date": latest_calibration.get("calibration_date"), "Result": latest_calibration.get("result") or "—"})
        if latest_maintenance:
            evidence_rows.append({"Type": "Maintenance", "Date": latest_maintenance.get("maintenance_date"), "Result": latest_maintenance.get("result") or "—"})
        if events_i:
            e = events_i[0]
            evidence_rows.append({"Type": "Event", "Date": e.get("event_date"), "Result": f"{e.get('severity') or '—'} · {e.get('event_status') or '—'}"})
        if latest_review:
            evidence_rows.append({"Type": "Performance Review", "Date": latest_review.get("review_date"), "Result": latest_review.get("decision") or "—"})
        if evidence_rows:
            st.dataframe(pd.DataFrame(evidence_rows), use_container_width=True, hide_index=True)
        else:
            st.info("لا توجد سجلات تشغيلية مرتبطة بعد." if ar else "No linked operational evidence records yet.")

    st.markdown("### " + ("📈 اتجاه الأداء الشهري" if ar else "📈 Monthly performance trend"))
    trend_rows = []
    for row in sorted(performance_i, key=lambda r: str(r.get("month_start") or ""))[-6:]:
        m = _cockpit_perf(row)
        trend_rows.append({
            "Month": str(row.get("month_start"))[:7],
            "Availability %": None if m.get("availability") is None else round(m.get("availability"), 1),
            "Utilization %": None if m.get("utilization") is None else round(m.get("utilization"), 1),
            "Unplanned h": round(float(m.get("unplanned") or 0), 1),
        })
    if trend_rows:
        trend_df = pd.DataFrame(trend_rows).set_index("Month")
        st.line_chart(trend_df[["Availability %", "Utilization %"]])
        st.dataframe(trend_df.reset_index(), use_container_width=True, hide_index=True)
    else:
        st.info("سجّل الأداء الشهري لبدء الـtrend." if ar else "Record monthly performance to start the trend.")

    with st.expander("🔎 " + ("تفاصيل الأدلة الخام المرتبطة" if ar else "Linked evidence details"), expanded=False):
        st.markdown("**Events**")
        if events_i:
            cols = [c for c in ["event_date", "event_type", "severity", "subsystem", "event_status", "investigation_reference"] if any(c in e for e in events_i)]
            st.dataframe(pd.DataFrame(events_i)[cols].head(20), use_container_width=True, hide_index=True)
        else:
            st.caption("—")
        st.markdown("**Maintenance**")
        if maintenance_i:
            cols = [c for c in ["maintenance_date", "maintenance_type", "provider", "result", "next_due", "work_order"] if any(c in m for m in maintenance_i)]
            st.dataframe(pd.DataFrame(maintenance_i)[cols].head(20), use_container_width=True, hide_index=True)
        else:
            st.caption("—")
        st.markdown("**Calibration**")
        if calibrations_i:
            cols = [c for c in ["calibration_date", "calibration_type", "result", "ooc_status", "next_due", "certificate_number"] if any(c in x for x in calibrations_i)]
            st.dataframe(pd.DataFrame(calibrations_i)[cols].head(20), use_container_width=True, hide_index=True)
        else:
            st.caption("—")

    st.caption("Instrument Management Cockpit is decision-support intelligence. Confirm GMP decisions against approved SOPs, controlled records, QA requirements and raw evidence.")

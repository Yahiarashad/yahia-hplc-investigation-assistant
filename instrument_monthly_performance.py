# Monthly Instrument Performance — Utilization, Availability & Target Intelligence
# Executed inside the authenticated Streamlit app context.

from __future__ import annotations

from datetime import date

import pandas as pd
import streamlit as st


def _perf_month_start(value):
    try:
        d = pd.to_datetime(value).date()
        return d.replace(day=1)
    except Exception:
        return date.today().replace(day=1)


def _perf_calc(scheduled, planned, unplanned, productive):
    scheduled = float(scheduled or 0)
    planned = float(planned or 0)
    unplanned = float(unplanned or 0)
    productive = float(productive or 0)
    planned_operating = max(0.0, scheduled - planned)
    available = max(0.0, planned_operating - unplanned)
    availability = (available / planned_operating * 100.0) if planned_operating > 0 else None
    utilization = (productive / available * 100.0) if available > 0 else None
    idle_available = max(0.0, available - productive)
    return {
        "planned_operating_hours": planned_operating,
        "available_hours": available,
        "availability_pct": availability,
        "utilization_pct": utilization,
        "idle_available_hours": idle_available,
    }


def _perf_pct(value):
    return "—" if value is None else f"{float(value):.1f}%"


def _perf_target_value(value):
    try:
        if value is None or str(value).strip() == "":
            return None
        v = float(value)
        return v if 0 <= v <= 100 else None
    except Exception:
        return None


def _perf_row_metrics(row):
    return _perf_calc(
        row.get("scheduled_hours"),
        row.get("planned_downtime_hours"),
        row.get("unplanned_downtime_hours"),
        row.get("productive_run_hours"),
    )


def _perf_signal(availability, utilization, target_availability, target_utilization):
    ta = _perf_target_value(target_availability)
    tu = _perf_target_value(target_utilization)
    if ta is None and tu is None:
        return "No target", "Set instrument targets to unlock target-gap intelligence.", "neutral"

    a_ok = None if ta is None or availability is None else availability >= ta
    u_ok = None if tu is None or utilization is None else utilization >= tu

    if a_ok is False and u_ok is True:
        return "Capacity risk", "High demand is meeting reduced availability. Review reliability, downtime and capacity pressure.", "critical"
    if a_ok is False and u_ok is False:
        return "Reliability + demand review", "Availability is below target and productive use is also below target. Review downtime, scheduling and demand before deciding why.", "review"
    if a_ok is True and u_ok is False:
        return "Capacity available", "Availability is on target but utilization is below target. There may be usable capacity or a scheduling / demand mismatch.", "watch"
    if a_ok is True and u_ok is True:
        return "On target", "Availability and utilization are both meeting the user-defined targets.", "good"
    if a_ok is False:
        return "Availability below target", "Reliability / downtime needs review against the configured availability target.", "review"
    if u_ok is False:
        return "Utilization below target", "Available capacity is being used below the configured utilization target.", "watch"
    if a_ok is True or u_ok is True:
        return "Target met", "The configured performance target is currently being met.", "good"
    return "Insufficient data", "A target exists, but the monthly hours are not sufficient to calculate the metric yet.", "neutral"


def _perf_gap(actual, target):
    target = _perf_target_value(target)
    if actual is None or target is None:
        return "—"
    gap = float(actual) - target
    return f"{gap:+.1f} pp"


def _render_signal_card(label, message, tone):
    border = {"critical": "#d64545", "review": "#d7a52c", "watch": "#2876a7", "good": "#16a36f"}.get(tone, "#94a3b8")
    st.markdown(
        f"""<div style="border:1px solid #dbe3ec;border-left:6px solid {border};border-radius:16px;padding:.85rem 1rem;background:#fff;margin:.55rem 0 1rem">
        <b style="color:#0f2742">{label}</b><div style="color:#64748b;font-size:.88rem;margin-top:.18rem">{message}</div></div>""",
        unsafe_allow_html=True,
    )


def render_instrument_performance():
    st.markdown("## 📈 Instrument Performance Intelligence")
    st.caption("Monthly Availability + Utilization + user-defined targets + capacity / reliability signals.")

    st.markdown(
        """
<div style="border:1px solid #193b50;border-radius:18px;padding:1rem 1.05rem;background:linear-gradient(145deg,#071422,#0d2234);color:#e6f1f7;margin:.4rem 0 1rem">
<b style="color:#fff">Availability asks:</b> Was the instrument ready for use when it was planned to be available?<br>
<b style="color:#fff">Utilization asks:</b> When it was available, how much of that time was actually used productively?<br>
<b style="color:#fff">Target Intelligence asks:</b> Is the gap caused by reliability pressure, spare capacity, or both?
</div>
""",
        unsafe_allow_html=True,
    )

    perf_instruments, inst_err, inst_ok = _db_list(
        "instruments",
        "id,instrument_code,instrument_name,instrument_type,target_availability_pct,target_utilization_pct,performance_target_note,created_at",
        "created_at.asc",
    )
    if not inst_ok:
        st.error("Could not load instrument performance targets.")
        if inst_err:
            st.caption(f"Diagnostic: {inst_err}")
        return
    if not perf_instruments:
        st.info("Create an Instrument Passport first, then record monthly performance.")
        return

    rows, err, ok = _db_list(
        "instrument_monthly_performance",
        "id,instrument_id,month_start,scheduled_hours,planned_downtime_hours,unplanned_downtime_hours,productive_run_hours,notes,created_at,updated_at",
        "month_start.desc",
    )
    if not ok:
        st.error("Monthly performance storage is not available yet.")
        if err:
            st.caption(f"Diagnostic: {err}")
        return

    inst_by_id = {str(i.get("id")): i for i in perf_instruments}
    label_map = {f"{i.get('instrument_code')} · {i.get('instrument_name') or 'Unnamed'}": i for i in perf_instruments}

    current_month = date.today().replace(day=1)
    current_rows = [r for r in rows if _perf_month_start(r.get("month_start")) == current_month]
    planned_total = available_total = productive_total = 0.0
    covered = set()
    below_availability_target = 0
    capacity_risk = 0
    target_covered = 0
    portfolio_monitor = []

    for r in current_rows:
        iid = str(r.get("instrument_id"))
        inst = inst_by_id.get(iid, {})
        m = _perf_row_metrics(r)
        planned_total += m["planned_operating_hours"]
        available_total += m["available_hours"]
        productive_total += float(r.get("productive_run_hours") or 0)
        covered.add(iid)
        ta = _perf_target_value(inst.get("target_availability_pct"))
        tu = _perf_target_value(inst.get("target_utilization_pct"))
        if ta is not None or tu is not None:
            target_covered += 1
        if ta is not None and m["availability_pct"] is not None and m["availability_pct"] < ta:
            below_availability_target += 1
        label, message, tone = _perf_signal(m["availability_pct"], m["utilization_pct"], ta, tu)
        if label == "Capacity risk":
            capacity_risk += 1
        portfolio_monitor.append({
            "Instrument": inst.get("instrument_code") or iid,
            "Availability %": round(m["availability_pct"], 1) if m["availability_pct"] is not None else None,
            "Availability target %": ta,
            "Availability gap pp": round(m["availability_pct"] - ta, 1) if m["availability_pct"] is not None and ta is not None else None,
            "Utilization %": round(m["utilization_pct"], 1) if m["utilization_pct"] is not None else None,
            "Utilization target %": tu,
            "Utilization gap pp": round(m["utilization_pct"] - tu, 1) if m["utilization_pct"] is not None and tu is not None else None,
            "Management signal": label,
        })

    portfolio_availability = (available_total / planned_total * 100.0) if planned_total > 0 else None
    portfolio_utilization = (productive_total / available_total * 100.0) if available_total > 0 else None

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Monthly Availability", _perf_pct(portfolio_availability), help="Weighted portfolio availability for the current month.")
    c2.metric("Monthly Utilization", _perf_pct(portfolio_utilization), help="Weighted portfolio utilization for the current month.")
    c3.metric("Data coverage", f"{len(covered)}/{len(perf_instruments)}", help="Instruments with a current-month performance record.")
    c4.metric("Capacity risk", capacity_risk, help="Current-month instruments below Availability target while meeting / exceeding Utilization target.")
    st.caption("Portfolio percentages are weighted by hours; the app does not average instrument percentages equally.")

    if portfolio_monitor:
        with st.expander("Portfolio target monitor | مراقبة الأداء مقابل الهدف", expanded=(capacity_risk > 0 or below_availability_target > 0)):
            a, b, c = st.columns(3)
            a.metric("Targets configured", f"{target_covered}/{len(current_rows)}")
            b.metric("Below Availability target", below_availability_target)
            c.metric("Capacity risk signals", capacity_risk)
            st.dataframe(pd.DataFrame(portfolio_monitor), use_container_width=True, hide_index=True)

    selected_label = st.selectbox("Instrument", list(label_map.keys()), key="perf_instrument_select")
    inst = label_map[selected_label]
    inst_id = str(inst.get("id"))
    inst_rows = [r for r in rows if str(r.get("instrument_id")) == inst_id]

    st.markdown("### 🎯 Performance targets")
    st.caption("Targets are laboratory / management decisions. The app does not invent a universal target and does not treat them as GMP release criteria.")
    with st.form("performance_target_form"):
        t1, t2 = st.columns(2)
        target_availability_text = t1.text_input(
            "Availability target %",
            value="" if inst.get("target_availability_pct") is None else str(inst.get("target_availability_pct")),
            placeholder="Enter your approved / management target",
        )
        target_utilization_text = t2.text_input(
            "Utilization target %",
            value="" if inst.get("target_utilization_pct") is None else str(inst.get("target_utilization_pct")),
            placeholder="Enter your approved / management target",
        )
        target_note = st.text_input(
            "Target basis / note",
            value=str(inst.get("performance_target_note") or ""),
            placeholder="e.g. annual capacity plan, laboratory KPI, instrument-specific target",
        )
        save_targets = st.form_submit_button("Save performance targets", use_container_width=True)

    if save_targets:
        raw_a = target_availability_text.strip()
        raw_u = target_utilization_text.strip()
        ta = _perf_target_value(raw_a)
        tu = _perf_target_value(raw_u)
        if raw_a and ta is None:
            st.error("Availability target must be a number between 0 and 100, or left blank.")
        elif raw_u and tu is None:
            st.error("Utilization target must be a number between 0 and 100, or left blank.")
        else:
            ok_t, _, _, err_t = _db_patch("instruments", inst_id, {
                "target_availability_pct": ta,
                "target_utilization_pct": tu,
                "performance_target_note": target_note.strip() or None,
            })
            if ok_t:
                st.success("Performance targets saved.")
                st.rerun()
            else:
                st.error(f"Could not save targets: {err_t or 'database error'}")

    month_choice = st.date_input("Month", value=current_month, key="perf_month_choice")
    month_start = _perf_month_start(month_choice)
    existing = next((r for r in inst_rows if _perf_month_start(r.get("month_start")) == month_start), None)

    default_scheduled = float((existing or {}).get("scheduled_hours") or 0)
    default_planned = float((existing or {}).get("planned_downtime_hours") or 0)
    default_unplanned = float((existing or {}).get("unplanned_downtime_hours") or 0)
    default_productive = float((existing or {}).get("productive_run_hours") or 0)
    default_notes = str((existing or {}).get("notes") or "")

    st.markdown("### Record monthly hours")
    with st.form("monthly_performance_form"):
        a, b = st.columns(2)
        scheduled = a.number_input("Scheduled service hours", min_value=0.0, value=default_scheduled, step=1.0, help="Hours the instrument was scheduled / expected to be available during the month.")
        planned = b.number_input("Planned downtime hours", min_value=0.0, value=default_planned, step=1.0, help="Approved planned downtime such as PM, calibration, qualification or planned shutdown.")
        c, d = st.columns(2)
        unplanned = c.number_input("Unplanned downtime hours", min_value=0.0, value=default_unplanned, step=1.0, help="Breakdown, unexpected repair, failure or unscheduled service time.")
        productive = d.number_input("Productive run hours", min_value=0.0, value=default_productive, step=1.0, help="Actual productive analytical use during available time.")
        notes = st.text_area("Notes / monthly context", value=default_notes)
        save = st.form_submit_button("Save monthly performance", use_container_width=True)

    calc = _perf_calc(scheduled, planned, unplanned, productive)
    ta = _perf_target_value(inst.get("target_availability_pct"))
    tu = _perf_target_value(inst.get("target_utilization_pct"))
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Planned operating time", f"{calc['planned_operating_hours']:.1f} h")
    k2.metric("Available time", f"{calc['available_hours']:.1f} h")
    k3.metric("Availability", _perf_pct(calc["availability_pct"]), delta=_perf_gap(calc["availability_pct"], ta), help="Delta is actual minus target in percentage points when a target is configured.")
    k4.metric("Utilization", _perf_pct(calc["utilization_pct"]), delta=_perf_gap(calc["utilization_pct"], tu), help="Delta is actual minus target in percentage points when a target is configured.")

    signal_label, signal_message, signal_tone = _perf_signal(calc["availability_pct"], calc["utilization_pct"], ta, tu)
    _render_signal_card(signal_label, signal_message, signal_tone)

    if scheduled > 0:
        st.caption(
            f"Idle but available time: {calc['idle_available_hours']:.1f} h · "
            "planned downtime is excluded from the Availability denominator; unplanned downtime reduces Availability."
        )

    validation_error = None
    if planned > scheduled:
        validation_error = "Planned downtime cannot exceed scheduled service hours."
    elif unplanned > max(0.0, scheduled - planned):
        validation_error = "Unplanned downtime cannot exceed planned operating time."
    elif productive > calc["available_hours"]:
        validation_error = "Productive run hours cannot exceed available hours. If overtime was used, increase Scheduled service hours to reflect the real schedule."

    if validation_error:
        st.error(validation_error)

    if save and not validation_error:
        payload = {
            "instrument_id": inst_id,
            "month_start": month_start.isoformat(),
            "scheduled_hours": float(scheduled),
            "planned_downtime_hours": float(planned),
            "unplanned_downtime_hours": float(unplanned),
            "productive_run_hours": float(productive),
            "notes": notes.strip() or None,
        }
        if existing:
            ok_save, _, _, save_err = _db_patch("instrument_monthly_performance", str(existing.get("id")), payload)
        else:
            ok_save, _, _, save_err = _db_insert("instrument_monthly_performance", payload)
        if ok_save:
            st.success(f"Saved {month_start.strftime('%b %Y')} performance for {inst.get('instrument_code')}.")
            st.rerun()
        else:
            st.error(f"Could not save monthly performance: {save_err or 'database error'}")

    st.markdown("### Monthly trend vs target")
    if not inst_rows:
        st.info("No monthly performance records yet for this instrument.")
    else:
        trend_rows = []
        for r in sorted(inst_rows, key=lambda x: str(x.get("month_start") or "")):
            m = _perf_row_metrics(r)
            row_signal, _, _ = _perf_signal(m["availability_pct"], m["utilization_pct"], ta, tu)
            trend_rows.append({
                "Month": pd.to_datetime(r.get("month_start")).strftime("%Y-%m"),
                "Availability %": round(m["availability_pct"], 1) if m["availability_pct"] is not None else None,
                "Availability target %": ta,
                "Utilization %": round(m["utilization_pct"], 1) if m["utilization_pct"] is not None else None,
                "Utilization target %": tu,
                "Scheduled h": float(r.get("scheduled_hours") or 0),
                "Planned downtime h": float(r.get("planned_downtime_hours") or 0),
                "Unplanned downtime h": float(r.get("unplanned_downtime_hours") or 0),
                "Productive run h": float(r.get("productive_run_hours") or 0),
                "Signal": row_signal,
            })
        trend_df = pd.DataFrame(trend_rows)
        chart_cols = ["Availability %", "Utilization %"]
        if ta is not None:
            chart_cols.append("Availability target %")
        if tu is not None:
            chart_cols.append("Utilization target %")
        st.line_chart(trend_df.set_index("Month")[chart_cols], use_container_width=True)
        st.dataframe(trend_df.sort_values("Month", ascending=False), use_container_width=True, hide_index=True)

    with st.expander("How to read the management signal | كيف تقرأ الإشارة؟", expanded=False):
        st.markdown(
            """
<div style="direction:rtl;text-align:right;line-height:1.9">
<b>Availability ≥ Target + Utilization ≥ Target</b> → الأداء على الهدفين المحددين.<br>
<b>Availability < Target + Utilization ≥ Target</b> → <b>Capacity Risk</b>: الطلب على الجهاز قوي لكن التوقف غير المخطط يضغط السعة المتاحة.<br>
<b>Availability ≥ Target + Utilization < Target</b> → توجد سعة متاحة غير مستغلة بالكامل؛ راجع الجدولة والطلب قبل اعتبارها مشكلة.<br>
<b>Availability < Target + Utilization < Target</b> → راجع Reliability + Scheduling + Demand معًا، ولا تفترض سببًا واحدًا.
</div>
""",
            unsafe_allow_html=True,
        )
        st.info("هذه مؤشرات إدارية / تشغيلية مساعدة للقرار، وليست GMP disposition ولا تثبت Root Cause أو صلاحية الجهاز بمفردها.")


# Add the calculation + target method to the practical guide without editing the base guide module.
_existing_perf_guide = globals().get("render_v03_user_guide")
if callable(_existing_perf_guide) and not globals().get("_ilm_perf_guide_wrapped"):
    _ilm_perf_guide_wrapped = True

    def render_v03_user_guide():
        _existing_perf_guide()
        with st.expander("📈 Instrument Utilization & Monthly Availability | طريقة الحساب", expanded=False):
            st.markdown(
                """
<div style="direction:rtl;text-align:right;line-height:1.95">
<h3>لماذا نحتاج النسبتين؟</h3>
<b>Availability %</b> تقيس قدرة الجهاز على أن يكون جاهزًا للاستخدام خلال الوقت المخطط له، وهي هنا نسبة شهرية.<br>
<b>Utilization %</b> تقيس مقدار الاستخدام الفعلي للجهاز من الوقت الذي كان متاحًا فيه فعلًا.

<h4>1) Planned Operating Time</h4>
<code>Scheduled Service Hours − Planned Downtime Hours</code><br>
الـPlanned Downtime يشمل التوقفات المعروفة مسبقًا مثل PM، Calibration، Qualification أو Planned Shutdown.

<h4>2) Available Time</h4>
<code>Planned Operating Time − Unplanned Downtime Hours</code><br>
الـUnplanned Downtime يشمل Breakdown، Failure، Unexpected Repair أو أي توقف غير مخطط.

<h4>3) Monthly Availability %</h4>
<code>Available Time ÷ Planned Operating Time × 100</code><br>
نستبعد الـApproved Planned Downtime من مقام Availability حتى لا نعاقب الجهاز على توقف مخطط ومعروف.

<h4>4) Instrument Utilization %</h4>
<code>Productive Run Hours ÷ Available Time × 100</code><br>
وبالتالي Utilization لا تقيس Reliability؛ بل تقيس مقدار استغلال الوقت الذي كان الجهاز متاحًا فيه.

<h4>مثال عملي</h4>
Scheduled = 176 h، Planned Downtime = 8 h، Unplanned Downtime = 12 h، Productive Run = 100 h:<br>
Planned Operating Time = 168 h<br>
Available Time = 156 h<br>
Availability = 156 ÷ 168 × 100 = <b>92.9%</b><br>
Utilization = 100 ÷ 156 × 100 = <b>64.1%</b>

<h4>5) Performance Targets</h4>
التطبيق لا يفترض Target ثابتًا لكل الأجهزة. أدخل Target الـAvailability وTarget الـUtilization لكل جهاز حسب سياسة المعمل، خطة السعة، نوع الجهاز أو KPI المعتمد لديك. يمكن ترك الهدف فارغًا إذا لم يكن محددًا.

<h4>6) Target Gap</h4>
<code>Actual % − Target %</code><br>
الفارق يعرض بوحدة <b>percentage points (pp)</b>، وليس نسبة تغير نسبية.

<h4>7) Management Signal</h4>
إذا كانت Availability أقل من الهدف بينما Utilization على/فوق الهدف، فهذه إشارة <b>Capacity Risk</b>: الجهاز مطلوب بقوة لكن Reliability / Downtime تضغط القدرة المتاحة. لا تعتبرها Root Cause؛ اعتبرها إشارة لتحديد أين تحقق أكثر.

<h4>قاعدة مهمة</h4>
لا تقارن أجهزة مختلفة قبل التأكد أن تعريف Scheduled Service Hours موحد. جهاز يعمل 24/7 لا يقارن مباشرة بجهاز مخطط له 8 ساعات يوميًا إلا إذا كانت قواعد الجدولة واضحة.
</div>
""",
                unsafe_allow_html=True,
            )
            st.warning("Portfolio Availability وUtilization داخل التطبيق محسوبة Weighted by Hours، وليست Average بسيط لنسب الأجهزة. Targets مؤشرات تشغيلية / إدارية وليست GMP release criteria.")

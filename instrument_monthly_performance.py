# Monthly Instrument Performance — Utilization & Availability
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
    return "—" if value is None else f"{value:.1f}%"


def _perf_row_metrics(row):
    return _perf_calc(
        row.get("scheduled_hours"),
        row.get("planned_downtime_hours"),
        row.get("unplanned_downtime_hours"),
        row.get("productive_run_hours"),
    )


def render_instrument_performance():
    st.markdown("## 📈 Instrument Performance")
    st.caption("Monthly Availability + Utilization — two different questions, one clearer capacity picture.")

    st.markdown(
        """
<div style="border:1px solid #193b50;border-radius:18px;padding:1rem 1.05rem;background:linear-gradient(145deg,#071422,#0d2234);color:#e6f1f7;margin:.4rem 0 1rem">
<b style="color:#fff">Availability asks:</b> Was the instrument ready for use when it was planned to be available?<br>
<b style="color:#fff">Utilization asks:</b> When the instrument was available, how much of that time was actually used productively?
</div>
""",
        unsafe_allow_html=True,
    )

    instruments_local = list(globals().get("instruments", []) or [])
    if not instruments_local:
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

    id_map = {str(i.get("id")): i for i in instruments_local}
    label_map = {
        f"{i.get('instrument_code')} · {i.get('instrument_name') or 'Unnamed'}": i
        for i in instruments_local
    }

    current_month = date.today().replace(day=1)
    current_rows = [r for r in rows if _perf_month_start(r.get("month_start")) == current_month]
    planned_total = available_total = productive_total = 0.0
    covered = set()
    for r in current_rows:
        m = _perf_row_metrics(r)
        planned_total += m["planned_operating_hours"]
        available_total += m["available_hours"]
        productive_total += float(r.get("productive_run_hours") or 0)
        covered.add(str(r.get("instrument_id")))
    portfolio_availability = (available_total / planned_total * 100.0) if planned_total > 0 else None
    portfolio_utilization = (productive_total / available_total * 100.0) if available_total > 0 else None

    c1, c2, c3 = st.columns(3)
    c1.metric("Monthly Availability", _perf_pct(portfolio_availability), help="Weighted portfolio availability for the current month.")
    c2.metric("Monthly Utilization", _perf_pct(portfolio_utilization), help="Weighted portfolio utilization for the current month.")
    c3.metric("Data coverage", f"{len(covered)}/{len(instruments_local)}", help="Instruments with a monthly performance record for the current month.")
    st.caption("Portfolio percentages are weighted by hours; the app does not average instrument percentages equally.")

    selected_label = st.selectbox("Instrument", list(label_map.keys()), key="perf_instrument_select")
    inst = label_map[selected_label]
    inst_id = str(inst.get("id"))
    inst_rows = [r for r in rows if str(r.get("instrument_id")) == inst_id]

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
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Planned operating time", f"{calc['planned_operating_hours']:.1f} h")
    k2.metric("Available time", f"{calc['available_hours']:.1f} h")
    k3.metric("Availability", _perf_pct(calc["availability_pct"]))
    k4.metric("Utilization", _perf_pct(calc["utilization_pct"]))

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

    st.markdown("### Monthly trend")
    if not inst_rows:
        st.info("No monthly performance records yet for this instrument.")
    else:
        trend_rows = []
        for r in sorted(inst_rows, key=lambda x: str(x.get("month_start") or "")):
            m = _perf_row_metrics(r)
            trend_rows.append({
                "Month": pd.to_datetime(r.get("month_start")).strftime("%Y-%m"),
                "Availability %": round(m["availability_pct"], 1) if m["availability_pct"] is not None else None,
                "Utilization %": round(m["utilization_pct"], 1) if m["utilization_pct"] is not None else None,
                "Scheduled h": float(r.get("scheduled_hours") or 0),
                "Planned downtime h": float(r.get("planned_downtime_hours") or 0),
                "Unplanned downtime h": float(r.get("unplanned_downtime_hours") or 0),
                "Productive run h": float(r.get("productive_run_hours") or 0),
            })
        trend_df = pd.DataFrame(trend_rows)
        chart_df = trend_df.set_index("Month")[["Availability %", "Utilization %"]]
        st.line_chart(chart_df, use_container_width=True)
        st.dataframe(trend_df.sort_values("Month", ascending=False), use_container_width=True, hide_index=True)

    with st.expander("How to read the two metrics | كيف تقرأ النسبتين؟", expanded=False):
        st.markdown(
            """
<div style="direction:rtl;text-align:right;line-height:1.9">
<b>Availability عالية + Utilization عالية</b> → الجهاز متاح ويتم استغلاله بكفاءة عالية.<br>
<b>Availability عالية + Utilization منخفضة</b> → الجهاز موثوق ومتاح لكن توجد سعة غير مستغلة؛ قد يكون ذلك طبيعيًا أو يشير إلى فرصة لإعادة توزيع الأحمال.<br>
<b>Availability منخفضة + Utilization عالية</b> → الجهاز مطلوب بشدة لكن الأعطال/التوقفات غير المخططة تضغط السعة؛ هنا يجب مراجعة Reliability وDowntime.<br>
<b>Availability منخفضة + Utilization منخفضة</b> → راجع الحاجة للجهاز، الأعطال، خطة العمل، وجدولة المختبر قبل اتخاذ أي قرار.
</div>
""",
            unsafe_allow_html=True,
        )
        st.info("لا تستخدم النسبة وحدها لإثبات Root Cause أو صلاحية الجهاز. هي Performance / capacity indicators تحتاج تفسيرًا في سياق الصيانة والمعايرة والأحداث الفعلية.")


# Add the calculation method to the practical guide without editing the base guide module.
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
<b>Availability %</b> تقيس قدرة الجهاز على أن يكون جاهزًا للاستخدام خلال الوقت المخطط له. وهي هنا <b>نسبة شهرية</b>.<br>
<b>Utilization %</b> تقيس مقدار الاستخدام الفعلي للجهاز من الوقت الذي كان متاحًا فيه فعلًا.

<h4>1) Planned Operating Time</h4>
<code>Scheduled Service Hours − Planned Downtime Hours</code><br>
الـPlanned Downtime يشمل التوقفات المعروفة مسبقًا مثل PM، Calibration، Qualification أو Planned Shutdown.

<h4>2) Available Time</h4>
<code>Planned Operating Time − Unplanned Downtime Hours</code><br>
الـUnplanned Downtime يشمل Breakdown، Failure، Unexpected Repair أو أي توقف غير مخطط.

<h4>3) Monthly Availability %</h4>
<code>Available Time ÷ Planned Operating Time × 100</code><br>
في هذا التطبيق نستبعد الـApproved Planned Downtime من مقام Availability حتى لا نعاقب الجهاز على توقف مخطط ومعتمد.

<h4>4) Instrument Utilization %</h4>
<code>Productive Run Hours ÷ Available Time × 100</code><br>
وبالتالي Utilization لا تقيس Reliability؛ بل تقيس مقدار استغلال الوقت الذي كان الجهاز متاحًا فيه.

<h4>مثال عملي</h4>
إذا كان الجهاز Scheduled = 176 h، وPlanned Downtime = 8 h، وUnplanned Downtime = 12 h، وProductive Run = 100 h:<br>
Planned Operating Time = 168 h<br>
Available Time = 156 h<br>
Availability = 156 ÷ 168 × 100 = <b>92.9%</b><br>
Utilization = 100 ÷ 156 × 100 = <b>64.1%</b>

<h4>قاعدة مهمة</h4>
لا تقارن نسب أجهزة مختلفة قبل التأكد أن تعريف Scheduled Service Hours موحّد. جهاز يعمل 24/7 لا يُقارن مباشرة بجهاز مخطط له 8 ساعات يوميًا إلا إذا كانت قواعد الجدولة واضحة.
</div>
""",
                unsafe_allow_html=True,
            )
            st.warning("Portfolio Availability وUtilization داخل التطبيق تُحسب Weighted by Hours، وليس بأخذ المتوسط الحسابي البسيط لنسب الأجهزة.")

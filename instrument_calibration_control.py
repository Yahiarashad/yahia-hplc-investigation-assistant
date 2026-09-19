# Calibration Control Center for Yahia QC Instrument Lifecycle
# Executed inside the authenticated Supabase application context.

from datetime import date


CAL_SELECT = (
    "id,user_id,instrument_id,calibration_date,calibration_type,result,calibration_id,"
    "certificate_number,report_reference,raw_data_reference,maintenance_reference,next_due,"
    "provider,provider_type,accreditation_body,accreditation_number,accreditation_scope_confirmed,"
    "sop_reference,manufacturer_recommendation_checked,applicable_standard,acceptance_criteria,"
    "reference_standards,traceability_reference,as_found,as_left,what_happened,cause_status,"
    "why_happened,impact_assessment,affected_results_products,investigation_reference,"
    "deviation_reference,capa_reference,ooc_status,notes,created_at,updated_at"
)


def _cal_text(value):
    return str(value or "").strip()


def _cal_due_state(value):
    days = _days_to(value)
    if days is None:
        return "Not set"
    if days < 0:
        return f"OVERDUE · {abs(days)}d"
    if days == 0:
        return "Due today"
    if days <= 30:
        return f"Due ≤30d · {days}d"
    if days <= 90:
        return f"Due ≤90d · {days}d"
    return "Current"


def _is_open_ooc(record):
    if str(record.get("result") or "").upper() != "OOC":
        return False
    return str(record.get("ooc_status") or "Open") not in {"Closed", "Resolved", "Not applicable"}


st.header("Calibration Control Center")
st.caption("Plan → control status → prove traceability → document evidence → manage OOC impact.")

with st.expander("What this section controls | ما الذي نراقبه هنا؟", expanded=False):
    st.markdown(
        """
This section turns calibration from a **due-date sticker** into a controlled lifecycle record.

It covers the points highlighted in the calibration-responsible workflow:

- **Planning:** calibration due dates and upcoming workload.
- **Status control:** instrument ID, calibration status, due date, calibration ID, certificate.
- **Traceability:** reference standards and traceability evidence.
- **Procedure control:** approved SOP, manufacturer recommendations, applicable standards, acceptance criteria.
- **OOC management:** what happened → why / cause evidence → impact → potentially affected results or products → investigation / deviation / CAPA references.
- **Documentation:** certificate, report, raw data, as-found / as-left, maintenance link.
- **External provider control:** provider, accreditation details, and scope confirmation.

**Important:** this is lifecycle visibility and decision support. Approved calibration certificates, raw data, SOPs, deviations and CAPA remain in the validated / controlled systems used by your site.
"""
    )

cal_instruments, cal_inst_err, cal_inst_ok = _db_list(
    "instruments",
    "id,instrument_code,instrument_name,instrument_type,manufacturer,model,operational_status,calibration_due",
    "instrument_code.asc",
)
cal_records, cal_rec_err, cal_rec_ok = _db_list("calibration_records", CAL_SELECT, "calibration_date.desc")

if not cal_inst_ok or not cal_rec_ok:
    st.error("Could not load calibration-control data from Supabase.")
    if cal_inst_err or cal_rec_err:
        st.caption(f"Diagnostic: {cal_inst_err or cal_rec_err}")
elif not cal_instruments:
    st.info("Create an Instrument Passport first. Calibration records are linked to the Instrument ID.")
else:
    code_by_id = {str(i.get("id")): _cal_text(i.get("instrument_code")) for i in cal_instruments}
    name_by_id = {str(i.get("id")): _cal_text(i.get("instrument_name")) for i in cal_instruments}

    latest_by_instrument = {}
    for record in cal_records:
        key = str(record.get("instrument_id"))
        if key not in latest_by_instrument:
            latest_by_instrument[key] = record

    overdue = sum(1 for i in cal_instruments if (_days_to(i.get("calibration_due")) is not None and _days_to(i.get("calibration_due")) < 0))
    due_30 = sum(1 for i in cal_instruments if (_days_to(i.get("calibration_due")) is not None and 0 <= _days_to(i.get("calibration_due")) <= 30))
    missing_due = sum(1 for i in cal_instruments if not i.get("calibration_due"))
    open_ooc = sum(1 for r in cal_records if _is_open_ooc(r))

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Overdue", overdue)
    m2.metric("Due ≤30 days", due_30)
    m3.metric("Due date missing", missing_due)
    m4.metric("Open OOC", open_ooc)

    if open_ooc:
        st.error(f"{open_ooc} calibration OOC record(s) still require documented assessment / closure.")
    elif overdue:
        st.warning(f"{overdue} instrument(s) are past the recorded calibration due date.")

    st.subheader("Calibration planning & status board")
    planning_rows = []
    for inst in cal_instruments:
        iid = str(inst.get("id"))
        latest = latest_by_instrument.get(iid, {})
        gaps = []
        if latest:
            if not latest.get("certificate_number"):
                gaps.append("Certificate missing")
            if not latest.get("calibration_id"):
                gaps.append("Calibration ID missing")
            if str(latest.get("provider_type") or "") == "External" and not latest.get("accreditation_scope_confirmed"):
                gaps.append("External scope not confirmed")
            if str(latest.get("result") or "").upper() == "OOC" and _is_open_ooc(latest):
                gaps.append("OOC open")
        else:
            gaps.append("No calibration record")
        planning_rows.append(
            {
                "Instrument ID": _cal_text(inst.get("instrument_code")),
                "Instrument": _cal_text(inst.get("instrument_name")),
                "Operational status": _cal_text(inst.get("operational_status")),
                "Calibration due": inst.get("calibration_due") or "—",
                "Due status": _cal_due_state(inst.get("calibration_due")),
                "Latest result": latest.get("result") or "—",
                "Calibration ID": latest.get("calibration_id") or "—",
                "Certificate": latest.get("certificate_number") or "—",
                "Control signals": "; ".join(gaps) if gaps else "Complete",
            }
        )
    st.dataframe(pd.DataFrame(planning_rows), use_container_width=True, hide_index=True)

    st.subheader("Add calibration record")
    st.caption("Capture the evidence around the calibration — not only the next due date.")

    instrument_options = {
        f"{_cal_text(i.get('instrument_code'))} · {_cal_text(i.get('instrument_name')) or 'Unnamed instrument'}": i
        for i in cal_instruments
    }

    with st.form("calibration_control_form"):
        selected_label = st.selectbox("Instrument ID", list(instrument_options.keys()))
        selected_inst = instrument_options[selected_label]

        st.markdown("#### 1 · Calibration status & planning")
        c1, c2, c3 = st.columns(3)
        calibration_date = c1.date_input("Calibration date", value=date.today())
        calibration_type = c2.selectbox(
            "Calibration type",
            ["Routine", "Initial", "Recalibration", "After maintenance", "Verification / check"],
        )
        result = c3.selectbox("Calibration result", ["Pass", "OOC", "Pending review"])

        c1, c2, c3 = st.columns(3)
        calibration_id = c1.text_input("Calibration ID / identification number")
        certificate_number = c2.text_input("Calibration certificate number")
        next_due = c3.date_input("Next calibration due date", value=None)

        st.markdown("#### 2 · Procedure & acceptance criteria")
        c1, c2 = st.columns(2)
        sop_reference = c1.text_input("Approved SOP / procedure reference")
        applicable_standard = c2.text_input("Applicable standard / guidance reference")
        acceptance_criteria = st.text_area("Defined acceptance criteria", height=90)
        manufacturer_checked = st.checkbox("Manufacturer recommendations reviewed / considered")

        st.markdown("#### 3 · Traceability")
        reference_standards = st.text_area(
            "Reference standards used",
            placeholder="Standard ID / certificate / due date / other traceability identifiers",
            height=100,
        )
        traceability_reference = st.text_input("Traceability reference / chain")

        st.markdown("#### 4 · Calibration evidence & records")
        c1, c2, c3 = st.columns(3)
        report_reference = c1.text_input("Calibration report reference")
        raw_data_reference = c2.text_input("Raw data reference")
        maintenance_reference = c3.text_input("Related maintenance / work-order reference")
        c1, c2 = st.columns(2)
        as_found = c1.text_area("As-found results / condition", height=90)
        as_left = c2.text_area("As-left results / condition", height=90)

        st.markdown("#### 5 · Provider / external laboratory control")
        c1, c2 = st.columns(2)
        provider_type = c1.selectbox("Provider type", ["Internal", "External"])
        provider = c2.text_input("Calibration provider / laboratory")
        c1, c2 = st.columns(2)
        accreditation_body = c1.text_input("Accreditation body")
        accreditation_number = c2.text_input("Accreditation number / certificate")
        accreditation_scope_confirmed = st.checkbox("Required calibration is confirmed within the provider accreditation scope")

        st.markdown("#### 6 · OOC / impact assessment")
        st.caption("Complete this section when calibration is OOC, or when the result needs investigation.")
        what_happened = st.text_area("What happened?", height=85)
        c1, c2 = st.columns(2)
        cause_status = c1.selectbox("Cause status", ["Not assessed", "Under investigation", "Confirmed", "Not identified"])
        ooc_status = c2.selectbox("OOC workflow status", ["Not applicable", "Open", "Under investigation", "Impact assessed", "Closed"])
        why_happened = st.text_area("Why did it happen? / cause evidence (if known)", height=85)
        impact_assessment = st.text_area("What was the impact?", height=95)
        affected_results_products = st.text_area("Which results / batches / products may be affected?", height=95)
        c1, c2, c3 = st.columns(3)
        investigation_reference = c1.text_input("Investigation reference")
        deviation_reference = c2.text_input("Deviation reference")
        capa_reference = c3.text_input("CAPA reference")

        notes = st.text_area("Additional notes", height=80)
        restrict_on_ooc = st.checkbox("If result is OOC, set the Instrument Passport operational status to Restricted")

        save_calibration = st.form_submit_button("Save Calibration Record", use_container_width=True)

    if save_calibration:
        selected_inst = instrument_options[selected_label]
        payload = {
            "instrument_id": str(selected_inst.get("id")),
            "calibration_date": calibration_date.isoformat(),
            "calibration_type": calibration_type,
            "result": result,
            "calibration_id": calibration_id.strip() or None,
            "certificate_number": certificate_number.strip() or None,
            "report_reference": report_reference.strip() or None,
            "raw_data_reference": raw_data_reference.strip() or None,
            "maintenance_reference": maintenance_reference.strip() or None,
            "next_due": next_due.isoformat() if next_due else None,
            "provider": provider.strip() or None,
            "provider_type": provider_type,
            "accreditation_body": accreditation_body.strip() or None,
            "accreditation_number": accreditation_number.strip() or None,
            "accreditation_scope_confirmed": bool(accreditation_scope_confirmed),
            "sop_reference": sop_reference.strip() or None,
            "manufacturer_recommendation_checked": bool(manufacturer_checked),
            "applicable_standard": applicable_standard.strip() or None,
            "acceptance_criteria": acceptance_criteria.strip() or None,
            "reference_standards": reference_standards.strip() or None,
            "traceability_reference": traceability_reference.strip() or None,
            "as_found": as_found.strip() or None,
            "as_left": as_left.strip() or None,
            "what_happened": what_happened.strip() or None,
            "cause_status": cause_status,
            "why_happened": why_happened.strip() or None,
            "impact_assessment": impact_assessment.strip() or None,
            "affected_results_products": affected_results_products.strip() or None,
            "investigation_reference": investigation_reference.strip() or None,
            "deviation_reference": deviation_reference.strip() or None,
            "capa_reference": capa_reference.strip() or None,
            "ooc_status": ooc_status,
            "notes": notes.strip() or None,
        }

        validation_messages = []
        if result == "Pass" and not next_due:
            validation_messages.append("Pass record saved without a next calibration due date.")
        if result == "Pass" and not certificate_number.strip():
            validation_messages.append("Pass record saved without a calibration certificate number.")
        if provider_type == "External" and not accreditation_scope_confirmed:
            validation_messages.append("External provider scope has not been confirmed in this record.")
        if result == "OOC" and ooc_status == "Not applicable":
            payload["ooc_status"] = "Open"
            validation_messages.append("OOC workflow status was automatically set to Open.")

        ok, _, _, err = _db_insert("calibration_records", payload)
        if ok:
            instrument_patch = {}
            if next_due:
                instrument_patch["calibration_due"] = next_due.isoformat()
            if result == "OOC" and restrict_on_ooc:
                instrument_patch["operational_status"] = "Restricted"
            if instrument_patch:
                _db_patch("instruments", str(selected_inst.get("id")), instrument_patch)
            st.success("Calibration record saved.")
            for msg in validation_messages:
                st.warning(msg)
            st.rerun()
        else:
            st.error(err or "Could not save calibration record.")

    st.divider()
    st.subheader("Calibration history & evidence")
    history_filter = st.selectbox(
        "History filter",
        ["All instruments"] + list(instrument_options.keys()),
        key="calibration_history_filter",
    )
    filtered_records = cal_records
    if history_filter != "All instruments":
        filter_inst = instrument_options[history_filter]
        filtered_records = [r for r in cal_records if str(r.get("instrument_id")) == str(filter_inst.get("id"))]

    history_rows = []
    for r in filtered_records:
        iid = str(r.get("instrument_id"))
        history_rows.append(
            {
                "Instrument ID": code_by_id.get(iid, ""),
                "Date": r.get("calibration_date") or "—",
                "Type": r.get("calibration_type") or "—",
                "Result": r.get("result") or "—",
                "Calibration ID": r.get("calibration_id") or "—",
                "Certificate": r.get("certificate_number") or "—",
                "Next due": r.get("next_due") or "—",
                "Provider": r.get("provider") or "—",
                "As-found": r.get("as_found") or "—",
                "As-left": r.get("as_left") or "—",
                "OOC status": r.get("ooc_status") or "—",
            }
        )
    if history_rows:
        st.dataframe(pd.DataFrame(history_rows), use_container_width=True, hide_index=True)
    else:
        st.info("No calibration records have been saved yet for this filter.")

    open_ooc_records = [r for r in cal_records if _is_open_ooc(r)]
    if open_ooc_records:
        st.subheader("Open OOC decision queue")
        st.caption("Repair alone does not close the question. The impact on generated data / results still needs documented assessment.")
        for r in open_ooc_records:
            iid = str(r.get("instrument_id"))
            code = code_by_id.get(iid, "Unknown instrument")
            name = name_by_id.get(iid, "")
            with st.expander(f"{code} · {name} · {r.get('calibration_date') or ''} · {r.get('ooc_status') or 'Open'}"):
                st.markdown(f"**What happened:** {_cal_text(r.get('what_happened')) or 'Not documented'}")
                st.markdown(f"**Cause status:** {_cal_text(r.get('cause_status')) or 'Not assessed'}")
                st.markdown(f"**Why / cause evidence:** {_cal_text(r.get('why_happened')) or 'Not documented'}")
                st.markdown(f"**Impact assessment:** {_cal_text(r.get('impact_assessment')) or 'Not documented'}")
                st.markdown(f"**Potentially affected results / products:** {_cal_text(r.get('affected_results_products')) or 'Not documented'}")
                st.markdown(
                    "**References:** "
                    f"Investigation={_cal_text(r.get('investigation_reference')) or '—'} · "
                    f"Deviation={_cal_text(r.get('deviation_reference')) or '—'} · "
                    f"CAPA={_cal_text(r.get('capa_reference')) or '—'}"
                )

    st.markdown(
        '<div class="cta"><b>Calibration control principle</b><br>'
        'A due date tells you <i>when</i> to calibrate. Traceability, as-found/as-left evidence and OOC impact assessment tell you whether the measurement history can be trusted.</div>',
        unsafe_allow_html=True,
    )

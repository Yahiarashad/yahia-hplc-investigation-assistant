# Acquisition & Commissioning Journey for Yahia QC Instrument Lifecycle
# Executed inside the authenticated Supabase application context.

from datetime import date


ACQ_SELECT = (
    "id,instrument_code,instrument_name,instrument_type,manufacturer,model,serial_number,"
    "urs_reference,urs_approval_date,quotation_reference,quotation_date,br_number,br_approval_date,"
    "po_number,po_approval_date,expected_receiving_date,receiving_date,issuance_date,"
    "iq_date,oq_date,pq_date,first_run_date,created_at,updated_at"
)


def _journey_date(value):
    if not value:
        return None
    return _parse_date(value)


def _iso_or_none(value):
    if value is None:
        return None
    try:
        return value.isoformat()
    except Exception:
        return str(value) if value else None


def _ref_text(value):
    return str(value or "").strip()


def _milestones(inst):
    return [
        {
            "stage": "1. URS Approved",
            "reference": _ref_text(inst.get("urs_reference")),
            "date": inst.get("urs_approval_date"),
            "done": bool(_ref_text(inst.get("urs_reference")) and inst.get("urs_approval_date")),
            "next": "Complete the Instrument URS and obtain approval.",
        },
        {
            "stage": "2. Quotation",
            "reference": _ref_text(inst.get("quotation_reference")),
            "date": inst.get("quotation_date"),
            "done": bool(_ref_text(inst.get("quotation_reference")) and inst.get("quotation_date")),
            "next": "Record the approved/selected supplier quotation before BR processing.",
        },
        {
            "stage": "3. BR Approved",
            "reference": _ref_text(inst.get("br_number")),
            "date": inst.get("br_approval_date"),
            "done": bool(_ref_text(inst.get("br_number")) and inst.get("br_approval_date")),
            "next": "Record the BR number and BR approval date.",
        },
        {
            "stage": "4. PO Approved",
            "reference": _ref_text(inst.get("po_number")),
            "date": inst.get("po_approval_date"),
            "done": bool(_ref_text(inst.get("po_number")) and inst.get("po_approval_date")),
            "next": "Record the PO number and PO approval date.",
        },
        {
            "stage": "5. Expected Receiving",
            "reference": "",
            "date": inst.get("expected_receiving_date"),
            "done": bool(inst.get("expected_receiving_date")),
            "next": "Set the expected receiving date and monitor supplier commitment.",
        },
        {
            "stage": "6. Received",
            "reference": "",
            "date": inst.get("receiving_date"),
            "done": bool(inst.get("receiving_date")),
            "next": "Record the actual receiving date when the instrument arrives.",
        },
        {
            "stage": "7. Issued to Laboratory",
            "reference": "",
            "date": inst.get("issuance_date"),
            "done": bool(inst.get("issuance_date")),
            "next": "Record issuance / handover to the laboratory.",
        },
        {
            "stage": "8. IQ Completed",
            "reference": "",
            "date": inst.get("iq_date"),
            "done": bool(inst.get("iq_date")),
            "next": "Complete and document Installation Qualification (IQ).",
        },
        {
            "stage": "9. OQ Completed",
            "reference": "",
            "date": inst.get("oq_date"),
            "done": bool(inst.get("oq_date")),
            "next": "Complete and document Operational Qualification (OQ).",
        },
        {
            "stage": "10. PQ Completed",
            "reference": "",
            "date": inst.get("pq_date"),
            "done": bool(inst.get("pq_date")),
            "next": "Complete and document Performance Qualification (PQ).",
        },
        {
            "stage": "11. First Run",
            "reference": "",
            "date": inst.get("first_run_date"),
            "done": bool(inst.get("first_run_date")),
            "next": "Record the first approved/routine analytical run after IQ/OQ/PQ.",
        },
    ]


def _chronology_warnings(inst):
    warnings = []
    ordered = [
        ("URS approval", inst.get("urs_approval_date")),
        ("Quotation", inst.get("quotation_date")),
        ("BR approval", inst.get("br_approval_date")),
        ("PO approval", inst.get("po_approval_date")),
        ("Receiving", inst.get("receiving_date")),
        ("Issuance", inst.get("issuance_date")),
        ("IQ", inst.get("iq_date")),
        ("OQ", inst.get("oq_date")),
        ("PQ", inst.get("pq_date")),
        ("First run", inst.get("first_run_date")),
    ]
    previous_name = None
    previous_date = None
    for name, raw in ordered:
        current = _journey_date(raw)
        if current and previous_date and current < previous_date:
            warnings.append(f"{name} ({current}) is earlier than {previous_name} ({previous_date}). Review the sequence or the entered date.")
        if current:
            previous_name, previous_date = name, current

    expected = _journey_date(inst.get("expected_receiving_date"))
    actual = _journey_date(inst.get("receiving_date"))
    if expected and actual:
        delta = (actual - expected).days
        if delta > 0:
            warnings.append(f"Actual receiving was {delta} day(s) later than the expected receiving date.")
        elif delta < 0:
            warnings.append(f"Actual receiving was {abs(delta)} day(s) earlier than the expected receiving date.")
    return warnings


st.header("Acquisition & Commissioning Journey")
st.caption("From URS to first analytical run — one controlled, visible timeline for every QC instrument.")

with st.expander("Why this journey matters | لماذا هذا المسار مهم؟", expanded=False):
    st.markdown(
        """
An instrument does not begin its lifecycle on the day it reaches the laboratory. Important decisions and commitments exist **before receipt**.

This journey keeps the critical chain visible:

**URS → Quotation → BR → PO → Expected Receiving → Receiving → Issuance → IQ → OQ → PQ → First Run**

Why it matters:
- exposes procurement or approval delays before they become surprises,
- preserves the link between the business request and the actual instrument,
- makes commissioning readiness visible to QC leadership,
- separates **expected** receiving from **actual** receiving,
- prevents a device from appearing operational before IQ/OQ/PQ and first-run readiness are documented,
- creates evidence that can later support lifecycle reviews and investigation context.

**Important:** the app is decision-support and lifecycle visibility software. Approved URS, BR, PO, qualification protocols/reports, and other official GMP records remain in your controlled systems.

**ببساطة:** إحنا مش بنسجل تاريخ وصول الجهاز فقط؛ إحنا بنشوف الرحلة كاملة من الاحتياج لحد أول تشغيل فعلي.
"""
    )

journey_instruments, journey_err, journey_ok = _db_list("instruments", ACQ_SELECT, "created_at.asc")
if not journey_ok:
    st.error("Could not load Acquisition Journey data from Supabase.")
    if journey_err:
        st.caption(f"Diagnostic: {journey_err}")
else:
    if not journey_instruments:
        st.info("Create an Instrument Passport first. Acquisition Journey is linked to the Instrument ID.")
    else:
        options = {
            f"{i.get('instrument_code')} · {i.get('instrument_name') or 'Unnamed instrument'}": i
            for i in journey_instruments
        }
        selected_label = st.selectbox("Instrument ID", list(options.keys()), key="acq_journey_instrument")
        inst = options[selected_label]
        milestones = _milestones(inst)
        completed = sum(1 for m in milestones if m["done"])
        percent = int(round((completed / len(milestones)) * 100))
        next_item = next((m for m in milestones if not m["done"]), None)

        c1, c2, c3 = st.columns(3)
        c1.metric("Journey completion", f"{percent}%")
        c2.metric("Completed milestones", f"{completed}/{len(milestones)}")
        c3.metric("Current stage", "First Run Complete" if next_item is None else next_item["stage"].split(". ", 1)[-1])
        st.progress(percent / 100.0)

        if next_item:
            st.markdown(
                f'<div class="cta"><b>Recommended next action → {next_item["stage"]}</b><br>{next_item["next"]}</div>',
                unsafe_allow_html=True,
            )
        else:
            st.success("Acquisition & commissioning journey complete: First Run is documented.")

        timeline_rows = []
        for m in milestones:
            timeline_rows.append({
                "Stage": m["stage"],
                "Reference": m["reference"] or "—",
                "Date": m["date"] or "—",
                "Status": "Complete" if m["done"] else "Pending",
            })
        st.dataframe(pd.DataFrame(timeline_rows), use_container_width=True, hide_index=True)

        warnings = _chronology_warnings(inst)
        if warnings:
            st.subheader("Timeline signals")
            for warning in warnings:
                st.warning(warning)

        st.subheader("Update acquisition & commissioning data")
        st.caption("Quotation is intentionally positioned before BR to match your instrument procurement workflow.")
        with st.form(f"acq_form_{inst.get('id')}"):
            st.markdown("#### 1 · URS")
            c1, c2 = st.columns(2)
            urs_ref = c1.text_input("Instrument URS / URS reference", value=_ref_text(inst.get("urs_reference")))
            urs_date = c2.date_input("URS approval date", value=_journey_date(inst.get("urs_approval_date")))

            st.markdown("#### 2 · Quotation")
            c1, c2 = st.columns(2)
            quotation_ref = c1.text_input("Quotation reference / number", value=_ref_text(inst.get("quotation_reference")))
            quotation_date = c2.date_input("Quotation date", value=_journey_date(inst.get("quotation_date")))

            st.markdown("#### 3 · BR")
            c1, c2 = st.columns(2)
            br_number = c1.text_input("BR number", value=_ref_text(inst.get("br_number")))
            br_date = c2.date_input("BR approval date", value=_journey_date(inst.get("br_approval_date")))

            st.markdown("#### 4 · Purchase Order")
            c1, c2 = st.columns(2)
            po_number = c1.text_input("PO number", value=_ref_text(inst.get("po_number")))
            po_date = c2.date_input("PO approval date", value=_journey_date(inst.get("po_approval_date")))

            st.markdown("#### 5–6 · Receiving")
            c1, c2 = st.columns(2)
            expected_receiving = c1.date_input("Expected receiving date", value=_journey_date(inst.get("expected_receiving_date")))
            receiving_date = c2.date_input("Actual receiving date", value=_journey_date(inst.get("receiving_date")))

            st.markdown("#### 7 · Issuance")
            issuance_date = st.date_input("Issuance / laboratory handover date", value=_journey_date(inst.get("issuance_date")))

            st.markdown("#### 8–10 · Qualification")
            c1, c2, c3 = st.columns(3)
            iq_date = c1.date_input("IQ completion date", value=_journey_date(inst.get("iq_date")))
            oq_date = c2.date_input("OQ completion date", value=_journey_date(inst.get("oq_date")))
            pq_date = c3.date_input("PQ completion date", value=_journey_date(inst.get("pq_date")))

            st.markdown("#### 11 · First Run")
            first_run_date = st.date_input("First approved / routine run date", value=_journey_date(inst.get("first_run_date")))

            save = st.form_submit_button("Save Acquisition Journey", use_container_width=True)

        if save:
            payload = {
                "urs_reference": urs_ref.strip() or None,
                "urs_approval_date": _iso_or_none(urs_date),
                "quotation_reference": quotation_ref.strip() or None,
                "quotation_date": _iso_or_none(quotation_date),
                "br_number": br_number.strip() or None,
                "br_approval_date": _iso_or_none(br_date),
                "po_number": po_number.strip() or None,
                "po_approval_date": _iso_or_none(po_date),
                "expected_receiving_date": _iso_or_none(expected_receiving),
                "receiving_date": _iso_or_none(receiving_date),
                "issuance_date": _iso_or_none(issuance_date),
                "iq_date": _iso_or_none(iq_date),
                "oq_date": _iso_or_none(oq_date),
                "pq_date": _iso_or_none(pq_date),
                "first_run_date": _iso_or_none(first_run_date),
            }
            ok, _, _, err = _db_patch("instruments", str(inst.get("id")), payload)
            if ok:
                st.success("Acquisition & Commissioning Journey saved.")
                st.rerun()
            else:
                st.error(err or "Could not save Acquisition Journey.")

        st.divider()
        st.markdown("### Quick use guide")
        st.markdown(
            """
1. Create the **Instrument Passport** and assign the Instrument ID.
2. Start the journey with the **URS reference + URS approval date**.
3. Record the **Quotation** before BR, then BR and PO approvals.
4. Enter both **Expected Receiving** and **Actual Receiving** to make delays visible.
5. After receipt, record **Issuance → IQ → OQ → PQ**.
6. Add the **First Run date** only after the qualification sequence is complete.
7. Use the progress and **Recommended next action** as a management signal — not as a substitute for controlled records.
"""
        )
        st.markdown(
            '<div class="cta"><b>CTA → Complete the next missing milestone.</b><br>A complete timeline turns procurement history into usable QC lifecycle evidence.</div>',
            unsafe_allow_html=True,
        )

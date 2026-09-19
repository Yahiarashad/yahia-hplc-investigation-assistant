# v0.3 Full Instrument Lifecycle Workflow
# Executed inside the authenticated Yahia QC Instrument Lifecycle app context.

from datetime import date

V03_INSTRUMENT_SELECT = (
    "id,instrument_code,instrument_name,instrument_type,manufacturer,model,serial_number,location,"
    "operational_status,responsible_team,qualification_due,pm_due,calibration_due,notes,"
    "need_title,need_identified_date,requested_by,department,need_justification,intended_use,"
    "criticality,target_implementation_date,urs_reference,urs_approval_date,quotation_reference,"
    "quotation_date,pr_number,pr_approval_date,po_number,po_approval_date,expected_receiving_date,"
    "receiving_date,installation_date,installation_reference,site_readiness_confirmed,utilities_confirmed,"
    "iq_date,oq_date,pq_date,issuance_date,first_run_date,created_at,updated_at"
)


def _v03_text(value):
    return str(value or "").strip()


def _v03_date(value):
    return _parse_date(value) if value else None


def _v03_iso(value):
    return value.isoformat() if value else None


def _v03_bool(value):
    return bool(value)


def _v03_stage_model(inst, review_rows, retirement):
    iid = str(inst.get("id"))
    inst_maintenance = [r for r in maintenance if str(r.get("instrument_id")) == iid]
    inst_lifecycle = [r for r in lifecycle_records if str(r.get("instrument_id")) == iid]
    inst_events = [r for r in events if str(r.get("instrument_id")) == iid]
    latest_review = next((r for r in review_rows if str(r.get("instrument_id")) == iid), None)

    need_done = bool(inst.get("need_identified_date") and _v03_text(inst.get("need_justification")) and _v03_text(inst.get("intended_use")))
    urs_done = bool(_v03_text(inst.get("urs_reference")) and inst.get("urs_approval_date"))
    quotation_done = bool(_v03_text(inst.get("quotation_reference")) and inst.get("quotation_date"))
    pr_done = bool(_v03_text(inst.get("pr_number")) and inst.get("pr_approval_date"))
    po_done = bool(_v03_text(inst.get("po_number")) and inst.get("po_approval_date"))
    receiving_done = bool(inst.get("receiving_date"))
    installation_done = bool(inst.get("installation_date"))
    iq_done = bool(inst.get("iq_date"))
    oq_done = bool(inst.get("oq_date"))
    pq_done = bool(inst.get("pq_date"))
    release_done = bool(inst.get("issuance_date"))
    first_run_done = bool(inst.get("first_run_date"))
    retired = bool(retirement and retirement.get("decommission_date")) or str(inst.get("operational_status") or "") == "Retired"

    controlled = [
        ("Need", need_done, "Record the laboratory need, justification and intended use."),
        ("URS", urs_done, "Approve the URS before procurement decisions are finalized."),
        ("Quotation", quotation_done, "Record the evaluated / selected quotation."),
        ("PR", pr_done, "Record Purchase Requisition approval."),
        ("PO", po_done, "Record Purchase Order issue / approval."),
        ("Receiving", receiving_done, "Record actual receipt and compare it with the expected date."),
        ("Installation", installation_done, "Document installation and site readiness."),
        ("IQ", iq_done, "Complete and document Installation Qualification."),
        ("OQ", oq_done, "Complete and document Operational Qualification."),
        ("PQ", pq_done, "Complete and document Performance Qualification."),
        ("Release / Issuance", release_done, "Release / hand over the qualified instrument for controlled laboratory use."),
        ("First Run", first_run_done, "Record the first approved routine analytical run."),
    ]

    first_pending = next((x for x in controlled if not x[1]), None)
    completed = sum(1 for _, done, _ in controlled if done)
    completion = int(round(completed / len(controlled) * 100))

    if retired:
        current_phase = "Retired / Decommissioned"
        next_action = "Lifecycle closed. Preserve the archived history and retirement evidence."
    elif first_pending:
        current_phase = first_pending[0]
        next_action = first_pending[2]
    else:
        current_phase = "Routine Operation"
        next_action = "Keep calibration, PM, requalification, components, events and periodic review current."

    ongoing_evidence = bool(inst_maintenance or inst_lifecycle or inst_events)
    stages = []
    for label, done, action in controlled:
        stages.append({"label": label, "status": "Complete" if done else ("Current" if first_pending and label == first_pending[0] else "Pending"), "action": action})
    stages.extend([
        {"label": "Routine Operation", "status": "Complete" if retired else ("Ongoing" if first_run_done else "Future"), "action": "Maintain controlled operational status and current ownership."},
        {"label": "Calibration / PM / Requalification", "status": "Ongoing" if first_run_done else "Future", "action": "Keep due dates and records current throughout routine use."},
        {"label": "Events & Investigation", "status": "Attention" if any(str(e.get("event_status")) != "Closed" for e in inst_events) else ("Monitoring" if first_run_done else "Future"), "action": "Preserve evidence and investigate failures without trial-and-error."},
        {"label": "Performance Review", "status": "Complete" if latest_review else ("Due when scheduled" if first_run_done else "Future"), "action": "Periodically evaluate reliability, compliance and replacement signals."},
        {"label": "Retirement / Decommission", "status": "Complete" if retired else "Future", "action": "Close the lifecycle with approved decommissioning and data archival."},
    ])
    return stages, completion, current_phase, next_action, ongoing_evidence


def _v03_chronology_signals(inst):
    signals = []
    order = [
        ("Need identified", inst.get("need_identified_date")),
        ("URS approval", inst.get("urs_approval_date")),
        ("Quotation", inst.get("quotation_date")),
        ("PR approval", inst.get("pr_approval_date")),
        ("PO approval", inst.get("po_approval_date")),
        ("Receiving", inst.get("receiving_date")),
        ("Installation", inst.get("installation_date")),
        ("IQ", inst.get("iq_date")),
        ("OQ", inst.get("oq_date")),
        ("PQ", inst.get("pq_date")),
        ("Release / Issuance", inst.get("issuance_date")),
        ("First Run", inst.get("first_run_date")),
    ]
    previous_name = None
    previous_date = None
    for name, raw in order:
        current = _v03_date(raw)
        if current and previous_date and current < previous_date:
            signals.append(f"{name} ({current}) is earlier than {previous_name} ({previous_date}). Review the entered evidence / dates.")
        if current:
            previous_name, previous_date = name, current

    expected = _v03_date(inst.get("expected_receiving_date"))
    actual = _v03_date(inst.get("receiving_date"))
    if expected and not actual and expected < date.today():
        signals.append(f"Expected receiving date passed {abs((date.today()-expected).days)} day(s) ago and actual receiving is not recorded.")
    if expected and actual and actual > expected:
        signals.append(f"Actual receiving was {(actual-expected).days} day(s) later than expected.")
    if inst.get("first_run_date") and not inst.get("pq_date"):
        signals.append("First Run is recorded while PQ evidence is missing. Review lifecycle integrity.")
    if inst.get("issuance_date") and not inst.get("pq_date"):
        signals.append("Release / Issuance is recorded while PQ evidence is missing.")
    return signals


st.markdown(
    """
<style>
.v03-loop {display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:.55rem;margin:.6rem 0 1rem;}
.v03-loop-card {border:1px solid #dbe3ec;border-radius:15px;padding:.75rem .7rem;background:linear-gradient(180deg,#ffffff,#f8fafc);min-height:92px;box-shadow:0 5px 16px rgba(15,23,42,.05);}
.v03-loop-card b {display:block;color:#0b2743;margin-bottom:.2rem}.v03-loop-card span{font-size:.82rem;color:#64748b;}
.v03-step {display:flex;gap:.75rem;align-items:flex-start;border-left:2px solid #dbe3ec;padding:0 0 .82rem 1rem;margin-left:.55rem;position:relative;}
.v03-step:before {content:"";position:absolute;left:-7px;top:3px;width:12px;height:12px;border-radius:50%;background:#94a3b8;border:2px solid white;box-shadow:0 0 0 1px #cbd5e1;}
.v03-step.complete:before{background:#17a673}.v03-step.current:before{background:#d6a92f;box-shadow:0 0 0 4px rgba(214,169,47,.13)}.v03-step.attention:before{background:#dc3545}.v03-step.ongoing:before{background:#2274a5}.v03-step.future:before{background:#cbd5e1}
.v03-step-title{font-weight:800;color:#1f2937}.v03-step-status{font-size:.77rem;font-weight:700;padding:.12rem .45rem;border-radius:999px;background:#f1f5f9;color:#475569;margin-left:.35rem}.v03-step-action{font-size:.86rem;color:#64748b;margin-top:.15rem}
@media(max-width:700px){.v03-loop{grid-template-columns:1fr 1fr}.v03-loop-card:last-child{grid-column:1/-1}.v03-step{margin-left:.35rem}.v03-step-action{font-size:.82rem}}
</style>
""",
    unsafe_allow_html=True,
)

st.header("↻ Full Instrument Lifecycle")
st.caption("One controlled journey — from the first laboratory need to final retirement / decommissioning.")

st.markdown(
    """
<div class="v03-loop">
  <div class="v03-loop-card"><b>1 · PLAN</b><span>Need → URS</span></div>
  <div class="v03-loop-card"><b>2 · ACQUIRE</b><span>Quotation → PR → PO → Receiving</span></div>
  <div class="v03-loop-card"><b>3 · QUALIFY</b><span>Installation → IQ → OQ → PQ → Release</span></div>
  <div class="v03-loop-card"><b>4 · OPERATE</b><span>First Run → Calibration → PM → Events</span></div>
  <div class="v03-loop-card"><b>5 · REVIEW & CLOSE</b><span>Performance Review → Retirement ↻</span></div>
</div>
""",
    unsafe_allow_html=True,
)

v03_instruments, v03_err, v03_ok = _db_list("instruments", V03_INSTRUMENT_SELECT, "created_at.asc")
review_rows, review_err, review_ok = _db_list("instrument_performance_reviews", "*", "review_date.desc")
retirement_rows, retirement_err, retirement_ok = _db_list("instrument_retirements", "*", "created_at.desc")

if not v03_ok:
    st.error("Could not load the v0.3 lifecycle dataset.")
    if v03_err: st.caption(f"Diagnostic: {v03_err}")
elif not v03_instruments:
    st.info("Create an Instrument Passport first. The full lifecycle attaches to the Instrument ID.")
else:
    retirement_by_instrument = {str(r.get("instrument_id")): r for r in retirement_rows} if retirement_ok else {}
    options = {f"{i.get('instrument_code')} · {i.get('instrument_name') or 'Unnamed instrument'}": i for i in v03_instruments}
    selected_label = st.selectbox("Instrument lifecycle", list(options.keys()), key="v03_lifecycle_instrument")
    inst = options[selected_label]
    iid = str(inst.get("id"))
    retirement = retirement_by_instrument.get(iid)
    stages, completion, current_phase, next_action, _ = _v03_stage_model(inst, review_rows, retirement)

    c1,c2,c3 = st.columns(3)
    c1.metric("Controlled milestones", f"{completion}%")
    c2.metric("Current lifecycle phase", current_phase)
    open_inst_events = [e for e in events if str(e.get("instrument_id")) == iid and str(e.get("event_status")) != "Closed"]
    c3.metric("Open events", len(open_inst_events))
    st.progress(completion/100.0)
    st.markdown(f'<div class="cta"><b>Next evidence-based action → {current_phase}</b><br>{next_action}</div>', unsafe_allow_html=True)

    st.subheader("Lifecycle navigator")
    for stage in stages:
        status = stage["status"]
        css = "complete" if status == "Complete" else "current" if status == "Current" else "attention" if status == "Attention" else "ongoing" if status in {"Ongoing","Monitoring"} else "future"
        st.markdown(
            f'<div class="v03-step {css}"><div><span class="v03-step-title">{stage["label"]}</span><span class="v03-step-status">{status}</span><div class="v03-step-action">{stage["action"]}</div></div></div>',
            unsafe_allow_html=True,
        )

    signals = _v03_chronology_signals(inst)
    if signals:
        st.subheader("Lifecycle signals")
        for signal in signals:
            st.warning(signal)

    planning_stages = {"Need","URS","Quotation","PR","PO","Receiving","Installation","IQ","OQ","PQ","Release / Issuance","First Run"}
    expand_need = current_phase == "Need"
    expand_acq = current_phase in planning_stages - {"Need"}

    with st.expander("1 · Need / Initiation", expanded=expand_need):
        st.caption("Record why the instrument is needed before procurement becomes the story.")
        with st.form(f"v03_need_{iid}"):
            c1,c2 = st.columns(2)
            need_title = c1.text_input("Need / request title", value=_v03_text(inst.get("need_title")))
            need_date = c2.date_input("Need identified date", value=_v03_date(inst.get("need_identified_date")))
            c1,c2 = st.columns(2)
            department = c1.text_input("Department / laboratory section", value=_v03_text(inst.get("department")))
            requested_by = c2.text_input("Requested by", value=_v03_text(inst.get("requested_by")))
            need_justification = st.text_area("Business / laboratory justification", value=_v03_text(inst.get("need_justification")), height=100)
            intended_use = st.text_area("Intended analytical use", value=_v03_text(inst.get("intended_use")), height=90)
            c1,c2 = st.columns(2)
            criticality_options = ["Low","Medium","High","Critical"]
            current_crit = _v03_text(inst.get("criticality")) or "Medium"
            criticality = c1.selectbox("Criticality", criticality_options, index=criticality_options.index(current_crit) if current_crit in criticality_options else 1)
            target_date = c2.date_input("Target implementation date", value=_v03_date(inst.get("target_implementation_date")))
            save_need = st.form_submit_button("Save Need / Initiation", use_container_width=True)
        if save_need:
            payload = {"need_title":need_title.strip() or None,"need_identified_date":_v03_iso(need_date),"department":department.strip() or None,"requested_by":requested_by.strip() or None,"need_justification":need_justification.strip() or None,"intended_use":intended_use.strip() or None,"criticality":criticality,"target_implementation_date":_v03_iso(target_date)}
            ok,_,_,err = _db_patch("instruments", iid, payload)
            if ok: st.success("Need / Initiation saved."); st.rerun()
            else: st.error(err or "Could not save Need / Initiation.")

    with st.expander("2 · Acquisition & Qualification | URS → First Run", expanded=expand_acq):
        st.caption("Controlled order: URS → Quotation → PR → PO → Receiving → Installation → IQ → OQ → PQ → Release → First Run")
        with st.form(f"v03_acq_{iid}"):
            st.markdown("#### URS")
            c1,c2 = st.columns(2)
            urs_reference = c1.text_input("URS reference", value=_v03_text(inst.get("urs_reference")))
            urs_date = c2.date_input("URS approval date", value=_v03_date(inst.get("urs_approval_date")))
            st.markdown("#### Quotation → PR → PO")
            c1,c2 = st.columns(2)
            quotation_reference = c1.text_input("Quotation reference", value=_v03_text(inst.get("quotation_reference")))
            quotation_date = c2.date_input("Quotation date", value=_v03_date(inst.get("quotation_date")))
            c1,c2 = st.columns(2)
            pr_number = c1.text_input("PR number", value=_v03_text(inst.get("pr_number")))
            pr_date = c2.date_input("PR approval date", value=_v03_date(inst.get("pr_approval_date")))
            c1,c2 = st.columns(2)
            po_number = c1.text_input("PO number", value=_v03_text(inst.get("po_number")))
            po_date = c2.date_input("PO approval / issue date", value=_v03_date(inst.get("po_approval_date")))
            st.markdown("#### Receiving & Installation")
            c1,c2 = st.columns(2)
            expected_receiving = c1.date_input("Expected receiving date", value=_v03_date(inst.get("expected_receiving_date")))
            receiving_date = c2.date_input("Actual receiving date", value=_v03_date(inst.get("receiving_date")))
            c1,c2 = st.columns(2)
            installation_date = c1.date_input("Installation date", value=_v03_date(inst.get("installation_date")))
            installation_reference = c2.text_input("Installation report reference", value=_v03_text(inst.get("installation_reference")))
            c1,c2 = st.columns(2)
            site_ready = c1.checkbox("Site readiness confirmed", value=_v03_bool(inst.get("site_readiness_confirmed")))
            utilities_ready = c2.checkbox("Utilities confirmed", value=_v03_bool(inst.get("utilities_confirmed")))
            st.markdown("#### Qualification → Release → First Run")
            c1,c2,c3 = st.columns(3)
            iq_date = c1.date_input("IQ completion date", value=_v03_date(inst.get("iq_date")))
            oq_date = c2.date_input("OQ completion date", value=_v03_date(inst.get("oq_date")))
            pq_date = c3.date_input("PQ completion date", value=_v03_date(inst.get("pq_date")))
            c1,c2 = st.columns(2)
            issuance_date = c1.date_input("Release / issuance date", value=_v03_date(inst.get("issuance_date")))
            first_run_date = c2.date_input("First approved routine run", value=_v03_date(inst.get("first_run_date")))
            save_acq = st.form_submit_button("Save Acquisition & Qualification Journey", use_container_width=True)
        if save_acq:
            payload={"urs_reference":urs_reference.strip() or None,"urs_approval_date":_v03_iso(urs_date),"quotation_reference":quotation_reference.strip() or None,"quotation_date":_v03_iso(quotation_date),"pr_number":pr_number.strip() or None,"pr_approval_date":_v03_iso(pr_date),"po_number":po_number.strip() or None,"po_approval_date":_v03_iso(po_date),"expected_receiving_date":_v03_iso(expected_receiving),"receiving_date":_v03_iso(receiving_date),"installation_date":_v03_iso(installation_date),"installation_reference":installation_reference.strip() or None,"site_readiness_confirmed":bool(site_ready),"utilities_confirmed":bool(utilities_ready),"iq_date":_v03_iso(iq_date),"oq_date":_v03_iso(oq_date),"pq_date":_v03_iso(pq_date),"issuance_date":_v03_iso(issuance_date),"first_run_date":_v03_iso(first_run_date)}
            ok,_,_,err=_db_patch("instruments",iid,payload)
            if ok: st.success("Acquisition & Qualification Journey saved."); st.rerun()
            else: st.error(err or "Could not save lifecycle journey.")

    with st.expander("3 · Routine Control | Calibration · PM · Requalification · Components", expanded=(current_phase == "Routine Operation")):
        st.caption("This phase is continuous. It does not become 'finished' while the instrument remains in service.")
        c1,c2,c3 = st.columns(3)
        c1.metric("Calibration", _due_label(inst.get("calibration_due")))
        c2.metric("Preventive Maintenance", _due_label(inst.get("pm_due")))
        c3.metric("Qualification", _due_label(inst.get("qualification_due")))
        inst_maint=[r for r in maintenance if str(r.get("instrument_id"))==iid]
        inst_life=[r for r in lifecycle_records if str(r.get("instrument_id"))==iid]
        inst_comp=[r for r in components if str(r.get("instrument_id"))==iid]
        st.write(f"Recorded history: **{len(inst_maint)} maintenance** · **{len(inst_life)} qualification/calibration lifecycle records** · **{len(inst_comp)} components**")
        st.info("Use the **Calibration & PM** tab to add controlled routine-lifecycle records.")

    with st.expander("4 · Periodic Performance Review", expanded=False):
        st.caption("Use evidence across the review period to decide whether to continue, monitor, upgrade, replace or retire.")
        with st.form(f"v03_review_{iid}"):
            c1,c2 = st.columns(2)
            review_date = c1.date_input("Review date", value=date.today())
            review_period = c2.number_input("Review period (months)", min_value=1, max_value=60, value=12)
            decision = st.selectbox("Lifecycle decision", ["Continue as-is","Increase monitoring","Major maintenance / upgrade","Replacement planning","Retirement recommended"])
            health_summary = st.text_area("Evidence summary / health review", height=110)
            action_plan = st.text_area("Action plan", height=90)
            reviewed_by = st.text_input("Reviewed by")
            review_notes = st.text_area("Notes", height=70)
            save_review = st.form_submit_button("Save Performance Review", use_container_width=True)
        if save_review:
            inst_events=[e for e in events if str(e.get("instrument_id"))==iid]
            payload={"instrument_id":iid,"review_date":review_date.isoformat(),"review_period_months":int(review_period),"failure_count":len(inst_events),"health_summary":health_summary.strip() or None,"decision":decision,"action_plan":action_plan.strip() or None,"reviewed_by":reviewed_by.strip() or None,"notes":review_notes.strip() or None}
            ok,_,_,err=_db_insert("instrument_performance_reviews",payload)
            if ok: st.success("Performance Review saved."); st.rerun()
            else: st.error(err or "Could not save Performance Review.")
        own_reviews=[r for r in review_rows if str(r.get("instrument_id"))==iid]
        if own_reviews:
            st.dataframe(pd.DataFrame([{"Date":r.get("review_date"),"Decision":r.get("decision"),"Reviewed by":r.get("reviewed_by") or "—","Action":r.get("action_plan") or "—"} for r in own_reviews]),use_container_width=True,hide_index=True)

    with st.expander("5 · Retirement / Decommission", expanded=(current_phase == "Retired / Decommissioned")):
        st.caption("Retirement closes operation — not history. Preserve evidence, archive data and document disposal / transfer.")
        existing = retirement or {}
        with st.form(f"v03_retire_{iid}"):
            c1,c2 = st.columns(2)
            retirement_request_date = c1.date_input("Retirement request date", value=_v03_date(existing.get("retirement_request_date")))
            approval_date = c2.date_input("Retirement approval date", value=_v03_date(existing.get("approval_date")))
            retirement_reason = st.text_area("Reason for retirement / decommission", value=_v03_text(existing.get("retirement_reason")), height=100)
            replacement = st.text_input("Replacement instrument / project", value=_v03_text(existing.get("replacement_instrument")))
            decommission_date = st.date_input("Decommission date", value=_v03_date(existing.get("decommission_date")))
            c1,c2 = st.columns(2)
            data_archive = c1.checkbox("Data archive completed", value=_v03_bool(existing.get("data_archive_completed")))
            backup_done = c2.checkbox("Required backup completed", value=_v03_bool(existing.get("backup_completed")))
            c1,c2 = st.columns(2)
            access_disabled = c1.checkbox("Software / user access disabled", value=_v03_bool(existing.get("software_access_disabled")))
            labels_removed = c2.checkbox("Controlled labels removed / voided", value=_v03_bool(existing.get("labels_removed")))
            c1,c2 = st.columns(2)
            disposal_method = c1.text_input("Disposal / transfer method", value=_v03_text(existing.get("disposal_method")))
            disposal_reference = c2.text_input("Disposal / transfer reference", value=_v03_text(existing.get("disposal_reference")))
            approved_by = st.text_input("Approved by", value=_v03_text(existing.get("approved_by")))
            retire_notes = st.text_area("Retirement notes", value=_v03_text(existing.get("notes")), height=80)
            mark_retired = st.checkbox("When decommission date is recorded, set Instrument Passport status to Retired", value=True)
            save_retirement = st.form_submit_button("Save Retirement / Decommission Record", use_container_width=True)
        if save_retirement:
            payload={"instrument_id":iid,"retirement_request_date":_v03_iso(retirement_request_date),"retirement_reason":retirement_reason.strip() or None,"replacement_instrument":replacement.strip() or None,"approval_date":_v03_iso(approval_date),"decommission_date":_v03_iso(decommission_date),"data_archive_completed":bool(data_archive),"backup_completed":bool(backup_done),"software_access_disabled":bool(access_disabled),"labels_removed":bool(labels_removed),"disposal_method":disposal_method.strip() or None,"disposal_reference":disposal_reference.strip() or None,"approved_by":approved_by.strip() or None,"notes":retire_notes.strip() or None}
            if existing.get("id"):
                ok,_,_,err=_db_patch("instrument_retirements",str(existing.get("id")),payload)
            else:
                ok,_,_,err=_db_insert("instrument_retirements",payload)
            if ok:
                if decommission_date and mark_retired:
                    _db_patch("instruments",iid,{"operational_status":"Retired"})
                st.success("Retirement / Decommission record saved."); st.rerun()
            else: st.error(err or "Could not save Retirement / Decommission record.")

    st.divider()
    st.markdown("### Lifecycle rule")
    st.markdown('<div class="cta"><b>An instrument is not a record. It is a lifecycle.</b><br>Complete only what the evidence supports. Missing evidence stays visible — it is never silently inferred.</div>', unsafe_allow_html=True)

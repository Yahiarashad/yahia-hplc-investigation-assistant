from pathlib import Path

p = Path("instrument_supabase_app.py")
s = p.read_text(encoding="utf-8")

old = '''        # Put score explainability immediately beside the score so users do not
        # need to hunt inside Control to understand why a device needs attention.
        _score_driver_count = len(reasons)
        with st.expander(f"Why {score}/100? · {_score_driver_count} score driver(s)", expanded=(score < 55)):
            if reasons:
                for _reason in reasons:
                    st.write(f"• {_reason}")
            else:
                st.success("No current lifecycle, status, event, recurrence, or overdue-component penalty is affecting this score.")
            st.caption("The Health Score is an explainable prioritization signal. It is not a release decision, compliance verdict, or root-cause conclusion.")

        # Evidence-consistency attention signal. Do not change the Health Score:
        # absence of an active event is not proof that documentation is missing.
        _status_value = str(inst.get("operational_status") or "Active")
        if _status_value in ("Out of Service", "Restricted", "Under Maintenance") and not open_inst_events:
            st.warning(
                f"Management Attention · Status is '{_status_value}' but no active instrument event is linked. "
                "Confirm that the reason, reference, and current control decision are documented in the appropriate approved record. "
                "This signal identifies an evidence-consistency question; it does not assert a missing GMP record."
            )
'''

new = '''        # Put score explainability immediately beside the score so users do not
        # need to hunt inside Control to understand why a device needs attention.
        # Keep it collapsed on mobile: the score is the primary signal; detail is on demand.
        _score_driver_count = len(reasons)
        with st.expander(f"Why {score}/100? · {_score_driver_count} score driver(s)", expanded=False):
            if reasons:
                for _reason in reasons:
                    st.write(f"• {_reason}")
            else:
                st.success("No current lifecycle, status, event, recurrence, or overdue-component penalty is affecting this score.")
            st.caption("The Health Score is an explainable prioritization signal. It is not a release decision, compliance verdict, or root-cause conclusion.")

        # Evidence-consistency attention signal. Keep the first-layer message short
        # for mobile and place governance wording behind an on-demand explanation.
        _status_value = str(inst.get("operational_status") or "Active")
        if _status_value in ("Out of Service", "Restricted", "Under Maintenance") and not open_inst_events:
            st.warning(
                f"⚠ Management Attention\n\n{_status_value} with no active linked event. "
                "Confirm the reason, reference, and current control decision are documented."
            )
            with st.expander("Why am I seeing this?", expanded=False):
                st.write(
                    "The instrument status indicates a controlled condition, while no active instrument event is currently linked in this application. "
                    "That mismatch is surfaced so the team can confirm traceability to the appropriate approved record."
                )
                st.caption(
                    "Evidence-consistency signal only — not a GMP compliance conclusion, not proof of a missing record, and not a root-cause determination."
                )
'''

if old not in s:
    raise SystemExit("Instrument 360 attention block not found")

s = s.replace(old, new, 1)
p.write_text(s, encoding="utf-8")
print("Instrument 360 attention UX compacted")

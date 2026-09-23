from pathlib import Path

p = Path('instrument_supabase_app.py')
s = p.read_text(encoding='utf-8')

anchor = '''        st.caption("Instrument 360 summarizes connected evidence. Health and performance indicators prioritize attention; they do not determine GMP disposition or root cause.")

        with st.expander("🪪 IDENTITY | الهوية", expanded=True):
'''
replacement = '''        st.caption("Instrument 360 summarizes connected evidence. Health and performance indicators prioritize attention; they do not determine GMP disposition or root cause.")

        # Put score explainability immediately beside the score so users do not
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

        with st.expander("🪪 IDENTITY | الهوية", expanded=True):
'''

if anchor not in s:
    raise SystemExit('Instrument 360 explanation anchor not found')

s = s.replace(anchor, replacement, 1)
p.write_text(s, encoding='utf-8')
print('Instrument 360 health explanation and evidence-consistency signal added')

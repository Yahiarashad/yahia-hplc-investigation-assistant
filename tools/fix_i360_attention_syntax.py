from pathlib import Path

p = Path("instrument_supabase_app.py")
s = p.read_text(encoding="utf-8")

broken = '''            st.warning(
                f"⚠ Management Attention

{_status_value} with no active linked event. "
                "Confirm the reason, reference, and current control decision are documented."
            )
'''

fixed = '''            st.warning(
                f"⚠ Management Attention\\n\\n{_status_value} with no active linked event. "
                "Confirm the reason, reference, and current control decision are documented."
            )
'''

if broken not in s:
    raise SystemExit("Broken Management Attention block not found")

s = s.replace(broken, fixed, 1)
p.write_text(s, encoding="utf-8")
print("Fixed Instrument 360 Management Attention syntax")

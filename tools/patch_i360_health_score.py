from pathlib import Path

p = Path('instrument_supabase_app.py')
s = p.read_text(encoding='utf-8')
old = '''        c1,c2,c3,c4=st.columns(4)
        c1.metric("Health",f"{score}/100",health_state(score))
        c2.metric("Status",inst.get("operational_status") or "—")
        c3.metric("Open events",len(open_inst_events))
        c4.metric("Latest Availability","—" if latest_availability is None else f"{latest_availability:.1f}%")
        st.caption("Instrument 360 summarizes connected evidence. Health and performance indicators prioritize attention; they do not determine GMP disposition or root cause.")
'''
new = """        _health_label=health_state(score)
        _health_color="#59d98e" if score>=85 else ("#f3c969" if score>=70 else "#ff7b7b")
        _availability_text="—" if latest_availability is None else f"{latest_availability:.1f}%"
        _utilization_text="—" if latest_utilization is None else f"{latest_utilization:.1f}%"
        st.markdown(
            f'''<div style="margin:-.35rem 0 .9rem;padding:.85rem 1rem;border:1px solid {_health_color};border-radius:18px;background:rgba(255,255,255,.025)">
                <div style="font-size:.72rem;letter-spacing:.12em;color:#aebdca;font-weight:800">INSTRUMENT HEALTH SCORE</div>
                <div style="display:flex;align-items:baseline;gap:.55rem;flex-wrap:wrap;margin-top:.15rem">
                    <span style="font-size:2rem;line-height:1;font-weight:900;color:{_health_color}">{score}/100</span>
                    <span style="font-size:.95rem;font-weight:800;color:{_health_color}">{_health_label}</span>
                </div>
            </div>
            <div style="display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:.55rem;margin-bottom:.75rem">
                <div style="padding:.7rem .8rem;border:1px solid #344252;border-radius:14px;background:#111923"><div style="font-size:.72rem;color:#8fa0af">STATUS</div><div style="font-size:1rem;font-weight:800;color:#f6f8fb">{inst.get('operational_status') or '—'}</div></div>
                <div style="padding:.7rem .8rem;border:1px solid #344252;border-radius:14px;background:#111923"><div style="font-size:.72rem;color:#8fa0af">OPEN EVENTS</div><div style="font-size:1rem;font-weight:800;color:#f6f8fb">{len(open_inst_events)}</div></div>
                <div style="padding:.7rem .8rem;border:1px solid #344252;border-radius:14px;background:#111923"><div style="font-size:.72rem;color:#8fa0af">AVAILABILITY</div><div style="font-size:1rem;font-weight:800;color:#f6f8fb">{_availability_text}</div></div>
                <div style="padding:.7rem .8rem;border:1px solid #344252;border-radius:14px;background:#111923"><div style="font-size:.72rem;color:#8fa0af">UTILIZATION</div><div style="font-size:1rem;font-weight:800;color:#f6f8fb">{_utilization_text}</div></div>
            </div>''',
            unsafe_allow_html=True,
        )
        st.caption("Instrument 360 summarizes connected evidence. Health and performance indicators prioritize attention; they do not determine GMP disposition or root cause.")
"""
if old not in s:
    raise SystemExit('Instrument 360 KPI block not found')
s = s.replace(old, new, 1)
p.write_text(s, encoding='utf-8')
print('Instrument 360 health score made mobile-visible')

from pathlib import Path

p = Path('instrument_supabase_app.py')
s = p.read_text(encoding='utf-8')

old = '''        codes=[str(x.get("instrument_code")) for x in instruments]; default_index=codes.index(deep_code) if deep_code in codes else 0
        selected_code=st.selectbox("Open Instrument Passport",codes,index=default_index,key="passport_selected")
        inst=next(x for x in instruments if str(x.get("instrument_code"))==selected_code); inst_id=str(inst.get("id")); score,reasons=health_score_v2(inst,events,components)
        c1,c2,c3=st.columns(3); c1.metric("Health Score",f"{score}/100",health_state(score)); c2.metric("Status",inst.get("operational_status") or "—"); c3.metric("Open events",len([e for e in events if str(e.get("instrument_id"))==inst_id and str(e.get("event_status"))!="Closed"]))
        st.markdown(f"### {selected_code} · {inst.get('instrument_name')}")
        details={"Type":inst.get("instrument_type") or "—","Manufacturer / Model":f"{inst.get('manufacturer') or '—'} / {inst.get('model') or '—'}","Serial number":inst.get("serial_number") or "—","Location":inst.get("location") or "—","Responsible team":inst.get("responsible_team") or "—","Qualification":f"{inst.get('qualification_due') or 'Not set'} · {_due_label(inst.get('qualification_due'))}","PM":f"{inst.get('pm_due') or 'Not set'} · {_due_label(inst.get('pm_due'))}","Calibration":f"{inst.get('calibration_due') or 'Not set'} · {_due_label(inst.get('calibration_due'))}"}
        st.dataframe(pd.DataFrame([details]).T.rename(columns={0:"Value"}),use_container_width=True)
        if reasons:
            with st.expander("Why this Health Score?"):
                for reason in reasons: st.write(f"• {reason}")
        with st.expander("QR Digital Passport"):
            st.write("Scan the QR to reopen this instrument after authentication. RLS still controls access.")
            try: app_url=str(st.context.url)
            except Exception: app_url=""
            if app_url:
                link=app_url.split("?")[0]+f"?instrument={urlparse.quote(selected_code)}"; st.code(link)
                if qrcode:
                    qr=qrcode.make(link); buf=io.BytesIO(); qr.save(buf,format="PNG"); st.image(buf.getvalue(),width=190); st.download_button("Download QR",buf.getvalue(),file_name=f"{selected_code}_passport_qr.png",mime="image/png")
                else: st.caption("QR rendering package is not installed; the deep link above is ready to use.")
            else: st.caption("Open the deployed app URL to generate a QR deep link.")
'''

new = '''        codes=[str(x.get("instrument_code")) for x in instruments]; default_index=codes.index(deep_code) if deep_code in codes else 0
        selected_code=st.selectbox("Open Instrument 360",codes,index=default_index,key="passport_selected")
        inst=next(x for x in instruments if str(x.get("instrument_code"))==selected_code); inst_id=str(inst.get("id")); score,reasons=health_score_v2(inst,events,components)

        # Instrument 360 assembles the connected story without inventing missing evidence.
        inst_events=[e for e in events if str(e.get("instrument_id"))==inst_id]
        open_inst_events=[e for e in inst_events if str(e.get("event_status"))!="Closed"]
        inst_maintenance=[r for r in maintenance if str(r.get("instrument_id"))==inst_id]
        inst_lifecycle=[r for r in lifecycle_records if str(r.get("instrument_id"))==inst_id]
        inst_components=[r for r in components if str(r.get("instrument_id"))==inst_id]

        perf_rows=[]
        perf_ok=False
        try:
            _all_perf, _perf_err, perf_ok = _db_list(
                "instrument_monthly_performance",
                "id,instrument_id,month_start,scheduled_hours,planned_downtime_hours,unplanned_downtime_hours,productive_run_hours,notes,created_at,updated_at",
                "month_start.desc",
            )
            if perf_ok:
                perf_rows=[r for r in _all_perf if str(r.get("instrument_id"))==inst_id]
        except Exception:
            perf_rows=[]
            perf_ok=False

        def _i360_perf_metrics(row):
            if not row:
                return None, None, None, None
            scheduled=float(row.get("scheduled_hours") or 0)
            planned=float(row.get("planned_downtime_hours") or 0)
            unplanned=float(row.get("unplanned_downtime_hours") or 0)
            productive=float(row.get("productive_run_hours") or 0)
            planned_operating=max(0.0,scheduled-planned)
            available=max(0.0,planned_operating-unplanned)
            availability=(available/planned_operating*100.0) if planned_operating>0 else None
            utilization=(productive/available*100.0) if available>0 else None
            return planned_operating,available,availability,utilization

        latest_perf=perf_rows[0] if perf_rows else None
        latest_planned,latest_available,latest_availability,latest_utilization=_i360_perf_metrics(latest_perf)

        st.markdown(
            f'''<div style="border:1px solid rgba(201,165,74,.65);border-radius:22px;padding:1rem 1.05rem;background:linear-gradient(145deg,#071422,#10263a);margin:.65rem 0 1rem;color:#e7eef5">
            <div style="font-size:.76rem;letter-spacing:.12em;color:#d6b85f;font-weight:800">INSTRUMENT 360 · CONNECTED ASSET STORY</div>
            <div style="font-size:1.35rem;font-weight:800;color:#fff;margin:.28rem 0">{selected_code} · {inst.get('instrument_name') or 'Unnamed instrument'}</div>
            <div style="color:#b8c6d3;font-size:.92rem">{inst.get('instrument_type') or 'Type not set'} · {inst.get('manufacturer') or 'Manufacturer not set'} · {inst.get('model') or 'Model not set'}</div>
            <div style="margin-top:.45rem;color:#d6b85f;font-size:.84rem;font-weight:700">IDENTITY → LIFECYCLE → CONTROL → PERFORMANCE → EVENTS → EVIDENCE</div>
            </div>''',
            unsafe_allow_html=True,
        )

        c1,c2,c3,c4=st.columns(4)
        c1.metric("Health",f"{score}/100",health_state(score))
        c2.metric("Status",inst.get("operational_status") or "—")
        c3.metric("Open events",len(open_inst_events))
        c4.metric("Latest Availability","—" if latest_availability is None else f"{latest_availability:.1f}%")
        st.caption("Instrument 360 summarizes connected evidence. Health and performance indicators prioritize attention; they do not determine GMP disposition or root cause.")

        with st.expander("🪪 IDENTITY | الهوية", expanded=True):
            identity_rows=[
                {"Field":"Instrument ID","Value":selected_code},
                {"Field":"Instrument name","Value":inst.get("instrument_name") or "Missing Evidence"},
                {"Field":"Type","Value":inst.get("instrument_type") or "Missing Evidence"},
                {"Field":"Manufacturer","Value":inst.get("manufacturer") or "Missing Evidence"},
                {"Field":"Model","Value":inst.get("model") or "Missing Evidence"},
                {"Field":"Serial number","Value":inst.get("serial_number") or "Missing Evidence"},
                {"Field":"Location","Value":inst.get("location") or "Missing Evidence"},
                {"Field":"Responsible team","Value":inst.get("responsible_team") or "Missing Evidence"},
            ]
            st.dataframe(pd.DataFrame(identity_rows),use_container_width=True,hide_index=True)

        with st.expander("↻ LIFECYCLE | دورة حياة الجهاز", expanded=False):
            l1,l2,l3=st.columns(3)
            l1.metric("Maintenance records",len(inst_maintenance))
            l2.metric("Calibration / Qualification",len(inst_lifecycle))
            l3.metric("Tracked components",len(inst_components))
            if inst_maintenance:
                st.markdown("**Latest maintenance**")
                maint_view=[]
                for r in sorted(inst_maintenance,key=lambda x:str(x.get("maintenance_date") or ""),reverse=True)[:5]:
                    maint_view.append({"Date":r.get("maintenance_date"),"Type":r.get("maintenance_type"),"Result":r.get("result"),"Provider":r.get("provider"),"Next due":r.get("next_due")})
                st.dataframe(pd.DataFrame(maint_view),use_container_width=True,hide_index=True)
            if inst_lifecycle:
                st.markdown("**Latest calibration / qualification evidence**")
                life_view=[]
                for r in sorted(inst_lifecycle,key=lambda x:str(x.get("performed_date") or ""),reverse=True)[:5]:
                    life_view.append({"Date":r.get("performed_date"),"Record":r.get("record_type"),"Result":r.get("result"),"Reference":r.get("reference"),"Next due":r.get("next_due")})
                st.dataframe(pd.DataFrame(life_view),use_container_width=True,hide_index=True)
            if not inst_maintenance and not inst_lifecycle:
                st.info("No maintenance / calibration / qualification history has been recorded for this instrument yet.")

        with st.expander("◎ CONTROL | حالة التحكم الحالية", expanded=False):
            control_rows=[]
            for _label,_field in [("Qualification","qualification_due"),("Preventive Maintenance","pm_due"),("Calibration","calibration_due")]:
                _value=inst.get(_field)
                control_rows.append({"Control":_label,"Due date":_value or "Missing Evidence","Status":_due_label(_value) if _value else "Missing Evidence"})
            st.dataframe(pd.DataFrame(control_rows),use_container_width=True,hide_index=True)
            if reasons:
                st.markdown("**Why the current Health Score needs attention**")
                for reason in reasons:
                    st.write(f"• {reason}")
            if inst_components:
                st.markdown("**Component control**")
                comp_view=[]
                for r in inst_components:
                    comp_view.append({"Component":r.get("component_name"),"Type":r.get("component_type"),"Status":r.get("status"),"Replacement / review due":r.get("replacement_due"),"Due signal":_due_label(r.get("replacement_due"))})
                st.dataframe(pd.DataFrame(comp_view),use_container_width=True,hide_index=True)
            else:
                st.caption("No components are currently tracked for this instrument.")

        with st.expander("📈 PERFORMANCE | Availability & Utilization", expanded=False):
            if not perf_ok:
                st.info("Monthly performance storage is not available in this workspace yet.")
            elif not perf_rows:
                st.info("No monthly Availability / Utilization record has been entered for this instrument yet. Open Performance to record the first month.")
            else:
                p1,p2,p3,p4=st.columns(4)
                p1.metric("Month",str(latest_perf.get("month_start") or "—")[:7])
                p2.metric("Availability","—" if latest_availability is None else f"{latest_availability:.1f}%")
                p3.metric("Utilization","—" if latest_utilization is None else f"{latest_utilization:.1f}%")
                p4.metric("Available time","—" if latest_available is None else f"{latest_available:.1f} h")
                trend=[]
                for r in sorted(perf_rows,key=lambda x:str(x.get("month_start") or ""))[-6:]:
                    _po,_av,_a,_u=_i360_perf_metrics(r)
                    trend.append({"Month":str(r.get("month_start") or "")[:7],"Availability %":None if _a is None else round(_a,1),"Utilization %":None if _u is None else round(_u,1)})
                if trend:
                    trend_df=pd.DataFrame(trend)
                    st.line_chart(trend_df.set_index("Month")[["Availability %","Utilization %"]],use_container_width=True)
                    st.dataframe(trend_df.sort_values("Month",ascending=False),use_container_width=True,hide_index=True)
            if callable(globals().get("_ilm_route_href")):
                st.markdown(f'<a href="{_ilm_route_href("📈 Performance")}#ilm-top" style="display:block;text-align:center;padding:.7rem;border:1px solid #c9a54d;border-radius:14px;text-decoration:none;font-weight:800">Open full Performance Intelligence →</a>',unsafe_allow_html=True)

        with st.expander("⚠ EVENTS | الأعطال والإشارات", expanded=False):
            e1,e2=st.columns(2)
            e1.metric("All events",len(inst_events))
            e2.metric("Open / active",len(open_inst_events))
            if inst_events:
                event_view=[]
                for r in sorted(inst_events,key=lambda x:str(x.get("event_date") or ""),reverse=True)[:8]:
                    event_view.append({"Date":r.get("event_date"),"Event":r.get("event_type"),"Severity":r.get("severity"),"Subsystem":r.get("subsystem"),"Status":r.get("event_status"),"Root cause status":r.get("root_cause_status")})
                st.dataframe(pd.DataFrame(event_view),use_container_width=True,hide_index=True)
            else:
                st.success("No instrument events are currently recorded for this asset.")
            if callable(globals().get("_ilm_route_href")):
                st.markdown(f'<a href="{_ilm_route_href("⚠ Events")}#ilm-top" style="display:block;text-align:center;padding:.7rem;border:1px solid #cbd5e1;border-radius:14px;text-decoration:none;font-weight:700">Open Event / Failure Log →</a>',unsafe_allow_html=True)

        with st.expander("▦ EVIDENCE | Passport & traceability", expanded=False):
            missing=[]
            for _label,_field in [("Manufacturer","manufacturer"),("Model","model"),("Serial number","serial_number"),("Location","location"),("Responsible team","responsible_team"),("Qualification due","qualification_due"),("PM due","pm_due"),("Calibration due","calibration_due")]:
                if not inst.get(_field):
                    missing.append(_label)
            if missing:
                st.warning("Missing Evidence: "+", ".join(missing))
            else:
                st.success("Core identity and due-date evidence is populated for this instrument.")

            refs=[]
            for r in inst_lifecycle:
                if r.get("reference"):
                    refs.append({"Evidence":r.get("record_type") or "Lifecycle record","Date":r.get("performed_date"),"Reference":r.get("reference")})
            for r in inst_maintenance:
                if r.get("work_order"):
                    refs.append({"Evidence":r.get("maintenance_type") or "Maintenance","Date":r.get("maintenance_date"),"Reference":r.get("work_order")})
            for r in inst_events:
                if r.get("investigation_reference"):
                    refs.append({"Evidence":"Event / investigation","Date":r.get("event_date"),"Reference":r.get("investigation_reference")})
            if refs:
                st.markdown("**Connected references**")
                st.dataframe(pd.DataFrame(refs).sort_values("Date",ascending=False),use_container_width=True,hide_index=True)
            else:
                st.caption("No certificate / protocol / work-order / investigation reference is currently connected to this asset.")

            st.markdown("**QR Digital Passport**")
            st.write("Scan the QR to reopen this instrument after authentication. RLS still controls access.")
            try: app_url=str(st.context.url)
            except Exception: app_url=""
            if app_url:
                link=app_url.split("?")[0]+f"?instrument={urlparse.quote(selected_code)}"; st.code(link)
                if qrcode:
                    qr=qrcode.make(link); buf=io.BytesIO(); qr.save(buf,format="PNG"); st.image(buf.getvalue(),width=190); st.download_button("Download QR",buf.getvalue(),file_name=f"{selected_code}_passport_qr.png",mime="image/png",key=f"i360_qr_{inst_id}")
                else: st.caption("QR rendering package is not installed; the deep link above is ready to use.")
            else: st.caption("Open the deployed app URL to generate a QR deep link.")
'''

if old not in s:
    raise SystemExit('Instrument Passport block anchor not found')

s = s.replace(old, new, 1)
p.write_text(s, encoding='utf-8')
print('Instrument 360 applied')

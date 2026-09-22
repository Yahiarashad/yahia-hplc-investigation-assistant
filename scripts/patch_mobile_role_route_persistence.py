from pathlib import Path

p = Path('app.py')
s = p.read_text(encoding='utf-8')

# 1) Restore UX role from the URL before deciding whether onboarding is needed.
anchor = 'ROLE_HELP = {item[0]: item[1] for item in ROLE_OPTIONS}\n\ndef _ilm_complete_role_onboarding():'
replacement = '''ROLE_HELP = {item[0]: item[1] for item in ROLE_OPTIONS}\n\n# Mobile route links can create a fresh Streamlit session. Persist only the UX\n# role in the URL so navigation never re-opens onboarding. This value controls\n# presentation only; database permissions remain workspace/RLS controlled.\ntry:\n    _url_ui_role = str(st.query_params.get("ui_role", "") or "").strip()\nexcept Exception:\n    _url_ui_role = ""\nif _url_ui_role in ROLE_LABELS and not st.session_state.get("ilm_user_role"):\n    st.session_state.ilm_user_role = _url_ui_role\n\ndef _ilm_complete_role_onboarding():'''
if anchor not in s:
    raise SystemExit('ROLE_HELP anchor not found')
s = s.replace(anchor, replacement, 1)

# 2) When onboarding completes, persist UX role into the URL before full rerun.
old = '''def _ilm_complete_role_onboarding():\n    role_label = str(st.session_state.get("ilm_role_onboarding_select") or "QC Analyst")\n    st.session_state.ilm_user_role = role_label\n    st.session_state.ilm_route = "🏠 Dashboard"\n    st.session_state.ilm_route_transition = True\n'''
new = '''def _ilm_complete_role_onboarding():\n    role_label = str(st.session_state.get("ilm_role_onboarding_select") or "QC Analyst")\n    st.session_state.ilm_user_role = role_label\n    st.session_state.ilm_route = "🏠 Dashboard"\n    st.session_state.ilm_route_transition = True\n    try:\n        st.query_params["ui_role"] = role_label\n        st.query_params["route"] = "dashboard"\n    except Exception:\n        pass\n'''
if old not in s:
    raise SystemExit('onboarding function anchor not found')
s = s.replace(old, new, 1)

# 3) Ensure every mobile route link carries the UX role and a top-of-content anchor.
old = '''    params["route"] = _ROUTE_SLUGS.get(route_item, "dashboard")\n    return "?" + urlencode(params, doseq=True)\n'''
new = '''    params["route"] = _ROUTE_SLUGS.get(route_item, "dashboard")\n    if st.session_state.get("ilm_user_role") in ROLE_LABELS:\n        params["ui_role"] = st.session_state.ilm_user_role\n    return "?" + urlencode(params, doseq=True) + "#ilm-top"\n'''
if old not in s:
    raise SystemExit('route href anchor not found')
s = s.replace(old, new, 1)

# 4) Force mobile route navigation at the top browsing context. This makes it a\n# clean navigation instead of preserving the open sidebar overlay state.
s = s.replace('target="_self">{route_item}</a>', 'target="_top">{route_item}</a>', 1)

# 5) Give the browser a deterministic top target before the app content renders.
anchor = 'if _signed_in_shell and st.session_state.get("ilm_user_role"):\n    with st.sidebar:'
replacement = '''if _signed_in_shell and st.session_state.get("ilm_user_role"):\n    st.markdown('<div id="ilm-top" style="height:0;overflow:hidden"></div>', unsafe_allow_html=True)\n    with st.sidebar:'''
if anchor not in s:
    raise SystemExit('signed-in sidebar anchor not found')
s = s.replace(anchor, replacement, 1)

# 6) Changing role must clear the URL-persisted UX role too.
old = '''        if st.button("Change my role", use_container_width=True, key="ilm_change_role"):\n            st.session_state.pop("ilm_user_role", None)\n            st.rerun()\n'''
new = '''        if st.button("Change my role", use_container_width=True, key="ilm_change_role"):\n            st.session_state.pop("ilm_user_role", None)\n            try:\n                if "ui_role" in st.query_params:\n                    del st.query_params["ui_role"]\n            except Exception:\n                pass\n            st.rerun()\n'''
if old not in s:
    raise SystemExit('change role anchor not found')
s = s.replace(old, new, 1)

p.write_text(s, encoding='utf-8')
print('patched mobile UX role persistence and top-level navigation')

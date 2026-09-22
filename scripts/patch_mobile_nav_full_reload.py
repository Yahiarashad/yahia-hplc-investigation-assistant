from pathlib import Path

p = Path('app.py')
s = p.read_text(encoding='utf-8')

# Remove URL ui_role persistence block. Workspace membership is the authority for UX role.
start = s.find('# Mobile route links can create a fresh Streamlit session.')
end = s.find('def _ilm_complete_role_onboarding():', start)
if start >= 0 and end >= 0:
    s = s[:start] + s[end:]

# Load workspace context before onboarding so fresh browser navigations do not reopen onboarding.
anchor = 'ROLE_HELP = {item[0]: item[1] for item in ROLE_OPTIONS}\n\ndef _ilm_complete_role_onboarding():'
early = '''ROLE_HELP = {item[0]: item[1] for item in ROLE_OPTIONS}\n\n# Resolve workspace membership before onboarding. A stored job_role is the\n# persistent UX role; security remains enforced by workspace membership/RLS.\n_ilm_workspaces, _ilm_workspace_id, _ilm_membership = ([], None, None)\nif _signed_in_shell:\n    try:\n        _ilm_workspaces, _ilm_workspace_id, _ilm_membership = _shell_workspace_context()\n    except Exception:\n        pass\nif _ilm_membership and str(_ilm_membership.get("job_role") or "") in ROLE_LABELS:\n    st.session_state.ilm_user_role = str(_ilm_membership.get("job_role"))\n\ndef _ilm_complete_role_onboarding():'''
if anchor not in s:
    raise SystemExit('ROLE_HELP onboarding anchor not found')
s = s.replace(anchor, early, 1)

# Add a small authenticated PATCH helper used to persist the user's personal UX role.
helper_anchor = 'def _shell_workspace_context():\n'
pos = s.find(helper_anchor)
if pos < 0:
    raise SystemExit('workspace context helper not found')
# Insert helper after _shell_workspace_context function, immediately before role-aware comment.
role_comment = '# -----------------------------------------------------------------------------\n# Role-aware onboarding + persistent workspace navigation.'
ri = s.find(role_comment, pos)
if ri < 0:
    raise SystemExit('role comment not found')
patch_helper = '''def _shell_persist_own_job_role(role_label: str):\n    \"\"\"Best-effort persistence for the signed-in member's UX role.\n\n    This is presentation metadata only; it does not grant permissions.\n    \"\"\"\n    token = str((st.session_state.get("_ilm_auth") or {}).get("access_token") or "")\n    user = (st.session_state.get("_ilm_auth") or {}).get("user") or {}\n    uid = str(user.get("id") or "")\n    wid = str(st.session_state.get("ilm_workspace_id") or "")\n    if not token or not uid or not wid or not SUPABASE_URL or not SUPABASE_KEY:\n        return\n    from urllib import parse as _urlparse\n    path = (\n        f"qc_workspace_members?workspace_id=eq.{_urlparse.quote(wid)}"\n        f"&user_id=eq.{_urlparse.quote(uid)}"\n    )\n    req = urlrequest.Request(\n        f"{SUPABASE_URL}/rest/v1/{path}",\n        data=json.dumps({"job_role": role_label}, ensure_ascii=False).encode("utf-8"),\n        headers={\n            "apikey": SUPABASE_KEY,\n            "Authorization": f"Bearer {token}",\n            "Content-Type": "application/json",\n            "Prefer": "return=minimal",\n        },\n        method="PATCH",\n    )\n    try:\n        with urlrequest.urlopen(req, timeout=15):\n            pass\n    except Exception:\n        pass\n\n\n'''
s = s[:ri] + patch_helper + s[ri:]

# Persist onboarding role in workspace membership and keep only route in URL.
old_func = '''def _ilm_complete_role_onboarding():\n    role_label = str(st.session_state.get("ilm_role_onboarding_select") or "QC Analyst")\n    st.session_state.ilm_user_role = role_label\n    st.session_state.ilm_route = "🏠 Dashboard"\n    st.session_state.ilm_route_transition = True\n    try:\n        st.query_params["ui_role"] = role_label\n        st.query_params["route"] = "dashboard"\n    except Exception:\n        pass\n'''
new_func = '''def _ilm_complete_role_onboarding():\n    role_label = str(st.session_state.get("ilm_role_onboarding_select") or "QC Analyst")\n    st.session_state.ilm_user_role = role_label\n    st.session_state.ilm_route = "🏠 Dashboard"\n    st.session_state.ilm_route_transition = True\n    _shell_persist_own_job_role(role_label)\n    try:\n        st.query_params["route"] = "dashboard"\n        if "ui_role" in st.query_params:\n            del st.query_params["ui_role"]\n    except Exception:\n        pass\n'''
if old_func in s:
    s = s.replace(old_func, new_func, 1)
else:
    # Fallback for already-partially-patched source.
    basic = '''def _ilm_complete_role_onboarding():\n    role_label = str(st.session_state.get("ilm_role_onboarding_select") or "QC Analyst")\n    st.session_state.ilm_user_role = role_label\n    st.session_state.ilm_route = "🏠 Dashboard"\n    st.session_state.ilm_route_transition = True\n'''
    if basic not in s:
        raise SystemExit('onboarding function body not found')
    s = s.replace(basic, new_func, 1)

# Remove the later duplicate workspace-context initialization; keep the early authoritative one.
late = '''_ilm_workspaces, _ilm_workspace_id, _ilm_membership = ([], None, None)\nif _signed_in_shell:\n    try:\n        _ilm_workspaces, _ilm_workspace_id, _ilm_membership = _shell_workspace_context()\n    except Exception:\n        pass\nif _ilm_membership and _ilm_membership.get("job_role"):\n    st.session_state.ilm_user_role = str(_ilm_membership.get("job_role"))\n'''
# Remove only the second occurrence if present.
first = s.find(late)
if first >= 0:
    second = s.find(late, first + 1)
    if second >= 0:
        s = s[:second] + s[second + len(late):]
    else:
        # If only one exists here, it is likely the old late block because early version differs.
        s = s.replace(late, '', 1)

# Replace route href with an absolute current-app URL. Full browser navigation is
# intentional on mobile: it closes the sidebar overlay and resets scroll to top.
start = s.find('def _ilm_route_href(route_item: str) -> str:')
end = s.find('\n\nif _signed_in_shell and st.session_state.get("ilm_user_role"):', start)
if start < 0 or end < 0:
    raise SystemExit('route href function bounds not found')
new_href = '''def _ilm_route_href(route_item: str) -> str:\n    from urllib.parse import urlencode\n    try:\n        base = str(st.context.url).split("?", 1)[0].split("#", 1)[0]\n    except Exception:\n        base = ""\n    params = {"route": _ROUTE_SLUGS.get(route_item, "dashboard")}\n    try:\n        instrument = st.query_params.get("instrument")\n        if instrument:\n            params["instrument"] = instrument\n    except Exception:\n        pass\n    query = urlencode(params, doseq=True)\n    return (base + "?" + query) if base else ("?" + query)\n'''
s = s[:start] + new_href + s[end:]

# Replace the mixed anchor/button navigation with one real browser link per route.
loop_start = s.find('        st.markdown(\n            """\n<style>\n.ilm-mobile-nav')
loop_end_marker = '        st.divider()\n        if st.button("Change my role"'
loop_end = s.find(loop_end_marker, loop_start)
if loop_start < 0 or loop_end < 0:
    raise SystemExit('sidebar mixed navigation block not found')
new_nav = '''        st.markdown(\n            """\n<style>\n.ilm-route-link{\n  display:flex!important;align-items:center;justify-content:center;\n  min-height:50px;margin:.34rem 0;padding:.55rem .75rem;\n  border:1px solid rgba(226,232,240,.82);border-radius:17px;\n  color:#f8fafc!important;text-decoration:none!important;font-weight:650;\n  background:rgba(255,255,255,.025);box-sizing:border-box;\n}\n.ilm-route-link.active{background:#ff4b4b!important;border-color:#ff7676!important;color:white!important}\n.ilm-route-link:visited{color:#f8fafc!important}\n.ilm-route-link:hover{border-color:#ffffff!important}\n</style>\n""",\n            unsafe_allow_html=True,\n        )\n        for group_name, group_items in _ROUTE_GROUPS.items():\n            st.caption(group_name)\n            for route_item in group_items:\n                is_active = route_item == current\n                _nav_class = "ilm-route-link active" if is_active else "ilm-route-link"\n                st.markdown(\n                    f'<a class="{_nav_class}" href="{_ilm_route_href(route_item)}">{route_item}</a>',\n                    unsafe_allow_html=True,\n                )\n'''
s = s[:loop_start] + new_nav + s[loop_end:]

# Change-role should deliberately reopen onboarding and clear the persisted role.
old_change = '''        st.divider()\n        if st.button("Change my role", use_container_width=True, key="ilm_change_role"):\n            st.session_state.pop("ilm_user_role", None)\n            try:\n                if "ui_role" in st.query_params:\n                    del st.query_params["ui_role"]\n            except Exception:\n                pass\n            st.rerun()\n'''
new_change = '''        st.divider()\n        if st.button("Change my role", use_container_width=True, key="ilm_change_role"):\n            st.session_state.pop("ilm_user_role", None)\n            # Clear only the personal UX role metadata. Security roles/permissions are untouched.\n            _shell_persist_own_job_role("")\n            try:\n                if "route" in st.query_params:\n                    del st.query_params["route"]\n                if "ui_role" in st.query_params:\n                    del st.query_params["ui_role"]\n            except Exception:\n                pass\n            st.rerun()\n'''
if old_change in s:
    s = s.replace(old_change, new_change, 1)

p.write_text(s, encoding='utf-8')
print('patched app.py with persistent workspace role and full-reload route links')

from pathlib import Path

p = Path('app.py')
s = p.read_text(encoding='utf-8')

# 1) Add a shell-level logout helper before role-aware navigation.
anchor = '\n\n# -----------------------------------------------------------------------------\n# Role-aware onboarding + persistent workspace navigation.\n'
if 'def _shell_logout():' not in s:
    helper = '''\n\ndef _shell_logout():\n    \"\"\"Sign out from Supabase, clear local session state and remove the persistent auth cookie.\"\"\"\n    token = str((st.session_state.get("_ilm_auth") or {}).get("access_token") or "")\n    if token and SUPABASE_URL and SUPABASE_KEY:\n        req = urlrequest.Request(\n            f"{SUPABASE_URL}/auth/v1/logout",\n            data=b"{}",\n            headers={\n                "apikey": SUPABASE_KEY,\n                "Authorization": f"Bearer {token}",\n                "Content-Type": "application/json",\n            },\n            method="POST",\n        )\n        try:\n            with urlrequest.urlopen(req, timeout=15):\n                pass\n        except Exception:\n            # Local sign-out must still complete even if the network call fails.\n            pass\n\n    for key in list(st.session_state.keys()):\n        if key.startswith("_ilm_") or key.startswith("ilm_") or key.startswith("form_"):\n            st.session_state.pop(key, None)\n    try:\n        controller.remove(COOKIE_NAME)\n    except Exception:\n        pass\n    try:\n        st.query_params.clear()\n    except Exception:\n        pass\n\n\ndef _shell_reopen_role_onboarding():\n    \"\"\"Clear only the UX job role so the onboarding role selector opens again.\"\"\"\n    st.session_state.pop("ilm_user_role", None)\n    _shell_persist_own_job_role("")\n    try:\n        if "route" in st.query_params:\n            del st.query_params["route"]\n        if "ui_role" in st.query_params:\n            del st.query_params["ui_role"]\n    except Exception:\n        pass\n\n'''
    if anchor not in s:
        raise SystemExit('role-aware navigation anchor not found')
    s = s.replace(anchor, helper + anchor, 1)

# 2) Reuse the role helper in the desktop sidebar and add Logout there too.
old_desktop = '''        st.divider()\n        if st.button("Change my role", use_container_width=True, key="ilm_change_role"):\n            st.session_state.pop("ilm_user_role", None)\n            # Clear only the personal UX role metadata. Security roles/permissions are untouched.\n            _shell_persist_own_job_role("")\n            try:\n                if "route" in st.query_params:\n                    del st.query_params["route"]\n                if "ui_role" in st.query_params:\n                    del st.query_params["ui_role"]\n            except Exception:\n                pass\n            st.rerun()\n'''
new_desktop = '''        st.divider()\n        st.caption("ACCOUNT")\n        if st.button("👤 Change my role", use_container_width=True, key="ilm_change_role"):\n            _shell_reopen_role_onboarding()\n            st.rerun()\n        if st.button("↪ Log out", use_container_width=True, key="ilm_logout"):\n            _shell_logout()\n            st.rerun()\n'''
if old_desktop in s:
    s = s.replace(old_desktop, new_desktop, 1)

# 3) Add Account controls inside the custom mobile popover menu.
mobile_tail = '''                    st.markdown(\n                        f'<a class="{_cls}" href="{_href}" target="_self">{_route_item}</a>',\n                        unsafe_allow_html=True,\n                    )\n'''
if 'key="ilm_mobile_change_role"' not in s:
    pos = s.find(mobile_tail)
    if pos < 0:
        raise SystemExit('mobile route link tail not found')
    pos = pos + len(mobile_tail)
    account_block = '''            st.divider()\n            st.caption("ACCOUNT")\n            _mobile_user = (st.session_state.get("_ilm_auth") or {}).get("user") or {}\n            _mobile_email = str(_mobile_user.get("email") or "").strip()\n            if _mobile_email:\n                st.caption(_mobile_email)\n            if st.button("👤 Change role", use_container_width=True, key="ilm_mobile_change_role"):\n                _shell_reopen_role_onboarding()\n                st.rerun()\n            if st.button("↪ Log out", use_container_width=True, key="ilm_mobile_logout", type="secondary"):\n                _shell_logout()\n                st.rerun()\n'''
    s = s[:pos] + account_block + s[pos:]

p.write_text(s, encoding='utf-8')
print('mobile account controls added')

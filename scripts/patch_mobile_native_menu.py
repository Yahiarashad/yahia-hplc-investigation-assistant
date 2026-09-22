from pathlib import Path

p = Path('app.py')
s = p.read_text(encoding='utf-8')

# Replace the existing desktop-only sidebar CSS block with a responsive split:
# native Streamlit sidebar on desktop, custom top mobile menu on phones.
old_css = '''    # Desktop: sidebar is the permanent navigation rail. Mobile: Streamlit's
    # responsive sidebar is collapsed; make the menu trigger self-explanatory.
    st.markdown("""
    <style>
    @media (min-width: 769px) {
      section[data-testid="stSidebar"] { min-width: 285px !important; max-width: 285px !important; }
      section[data-testid="stSidebar"] > div { width: 285px !important; }
    }
    </style>
    """, unsafe_allow_html=True)
'''
new_css = '''    # Responsive navigation split.
    # Desktop keeps the persistent native sidebar. On mobile we hide Streamlit's
    # drawer completely and use a top popover menu in the main app instead. This
    # avoids the mobile drawer reopening over the newly selected page.
    st.markdown("""
    <style>
    @media (min-width: 769px) {
      section[data-testid="stSidebar"] { min-width: 285px !important; max-width: 285px !important; }
      section[data-testid="stSidebar"] > div { width: 285px !important; }
      .st-key-ilm_mobile_nav { display:none !important; }
    }
    @media (max-width: 768px) {
      section[data-testid="stSidebar"] { display:none !important; }
      [data-testid="stSidebarCollapsedControl"],
      [data-testid="collapsedControl"],
      button[data-testid="stSidebarCollapseButton"] { display:none !important; }
      .st-key-ilm_mobile_nav { display:block !important; margin:.15rem 0 .65rem !important; }
      .ilm-mobile-route-link {
        display:flex !important; align-items:center; justify-content:center;
        min-height:48px; margin:.34rem 0; padding:.52rem .68rem;
        border:1px solid rgba(226,232,240,.78); border-radius:15px;
        color:#f8fafc !important; text-decoration:none !important; font-weight:700;
        background:rgba(255,255,255,.035); box-sizing:border-box;
      }
      .ilm-mobile-route-link.active {
        background:#ff4b4b !important; border-color:#ff7676 !important; color:white !important;
      }
      .ilm-mobile-route-link:visited { color:#f8fafc !important; }
    }
    </style>
    """, unsafe_allow_html=True)

    # Mobile navigation is deliberately outside st.sidebar. A route click performs
    # a normal same-app browser navigation, so the menu closes with the page load
    # and #ilm-top positions the user at the first line of the selected workspace.
    with st.container(key="ilm_mobile_nav"):
        _mobile_current = st.session_state.get("ilm_route", "🏠 Dashboard")
        _mobile_label = _mobile_current.replace("🏠 ", "").replace("📋 ", "").replace("↻ ", "").replace("◎ ", "").replace("⚠ ", "").replace("🔎 ", "").replace("📈 ", "").replace("🔔 ", "").replace("▦ ", "").replace("🎛 ", "").replace("ⓘ ", "").replace("🛡 ", "")
        with st.popover(f"☰ Menu · {_mobile_label}", use_container_width=True):
            st.caption("QC Intelligence · choose a workspace")
            for _group_name, _group_items in _ROUTE_GROUPS.items():
                st.caption(_group_name)
                for _route_item in _group_items:
                    _is_active = _route_item == _mobile_current
                    _cls = "ilm-mobile-route-link active" if _is_active else "ilm-mobile-route-link"
                    _href = _ilm_route_href(_route_item) + "#ilm-top"
                    st.markdown(
                        f'<a class="{_cls}" href="{_href}" target="_self">{_route_item}</a>',
                        unsafe_allow_html=True,
                    )
'''
if old_css not in s:
    raise SystemExit('responsive sidebar CSS anchor not found')
s = s.replace(old_css, new_css, 1)

p.write_text(s, encoding='utf-8')
print('patched mobile navigation to custom main-area menu')

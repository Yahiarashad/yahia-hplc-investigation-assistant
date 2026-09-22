from pathlib import Path

# -----------------------------------------------------------------------------
# app.py — reliable mobile navigation without parent-iframe JavaScript.
# Mobile uses real same-tab links so a route change performs a clean page load:
# sidebar collapses naturally and the viewport starts at the top. Desktop keeps
# Streamlit buttons for a faster persistent navigation rail.
# -----------------------------------------------------------------------------
app = Path('app.py')
s = app.read_text(encoding='utf-8')

s = s.replace('"MY INSTRUMENTS": ["🪪 Passport", "↻ Lifecycle"],', '"MY INSTRUMENTS": ["📋 Instruments", "↻ Lifecycle"],', 1)
s = s.replace('"🏠 Dashboard", "↻ Lifecycle", "🪪 Passport", "◎ Cal & PM",', '"🏠 Dashboard", "↻ Lifecycle", "📋 Instruments", "◎ Cal & PM",', 1)

route_anchor = '_ROUTE_ITEMS = [item for group in _ROUTE_GROUPS.values() for item in group]\n\n'
route_block = '''_ROUTE_ITEMS = [item for group in _ROUTE_GROUPS.values() for item in group]\n\n# Stable URL slugs make mobile navigation a real same-tab page navigation.\n# This is deliberately used instead of trying to click Streamlit sidebar DOM\n# controls from a sandboxed component iframe, which is not reliable on mobile.\n_ROUTE_SLUGS = {\n    "🏠 Dashboard": "dashboard",\n    "📋 Instruments": "instruments",\n    "↻ Lifecycle": "lifecycle",\n    "◎ Cal & PM": "cal-pm",\n    "⚠ Events": "events",\n    "🔎 Investigate": "investigate",\n    "📈 Performance": "performance",\n    "🔔 Alerts": "alerts",\n    "▦ Reports": "reports",\n    "🎛 Cockpit": "cockpit",\n    "ⓘ Guide": "guide",\n    "🛡 Admin": "admin",\n}\n_ROUTE_BY_SLUG = {slug: route for route, slug in _ROUTE_SLUGS.items()}\ntry:\n    _requested_route_slug = str(st.query_params.get("route", "") or "").strip().lower()\nexcept Exception:\n    _requested_route_slug = ""\n_requested_route = _ROUTE_BY_SLUG.get(_requested_route_slug)\nif _requested_route and _requested_route in _ROUTE_ITEMS:\n    st.session_state.ilm_route = _requested_route\n\ndef _ilm_route_href(route_item: str) -> str:\n    from urllib.parse import urlencode\n    params = {}\n    try:\n        for key in st.query_params:\n            if str(key) == "route":\n                continue\n            value = st.query_params.get(key)\n            if value not in (None, ""):\n                params[str(key)] = value\n    except Exception:\n        pass\n    params["route"] = _ROUTE_SLUGS.get(route_item, "dashboard")\n    return "?" + urlencode(params, doseq=True)\n\n'''
if route_anchor not in s:
    raise SystemExit('route items anchor not found')
s = s.replace(route_anchor, route_block, 1)

old_loop = '''        for group_name, group_items in _ROUTE_GROUPS.items():\n            st.caption(group_name)\n            for route_item in group_items:\n                is_active = route_item == current\n                if st.button(\n                    route_item,\n                    key="ilm_nav_" + route_item,\n                    use_container_width=True,\n                    type="primary" if is_active else "secondary",\n                ):\n                    st.session_state.ilm_route = route_item\n                    st.session_state.ilm_route_transition = True\n                    st.rerun()\n'''
new_loop = '''        st.markdown(\n            """\n<style>\n.ilm-mobile-nav{display:none!important}\n@media(max-width:768px){\n  .ilm-mobile-nav{\n    display:flex!important;align-items:center;justify-content:center;\n    min-height:52px;margin:.36rem 0;padding:.55rem .7rem;\n    border:1px solid rgba(226,232,240,.82);border-radius:18px;\n    color:#f8fafc!important;text-decoration:none!important;font-weight:650;\n    background:rgba(255,255,255,.025);box-sizing:border-box;\n  }\n  .ilm-mobile-nav.active{background:#ff4b4b!important;border-color:#ff7676!important;color:white!important}\n  .ilm-mobile-nav:visited{color:#f8fafc!important}\n  [class*="st-key-ilm_desktop_nav_"]{display:none!important}\n}\n</style>\n""",\n            unsafe_allow_html=True,\n        )\n        for group_name, group_items in _ROUTE_GROUPS.items():\n            st.caption(group_name)\n            for route_item in group_items:\n                is_active = route_item == current\n                _nav_class = "ilm-mobile-nav active" if is_active else "ilm-mobile-nav"\n                st.markdown(\n                    f'<a class="{_nav_class}" href="{_ilm_route_href(route_item)}" target="_self">{route_item}</a>',\n                    unsafe_allow_html=True,\n                )\n                _desktop_key = "ilm_desktop_nav_" + _ROUTE_SLUGS.get(route_item, "dashboard").replace("-", "_")\n                with st.container(key=_desktop_key):\n                    if st.button(\n                        route_item,\n                        key="ilm_nav_" + route_item,\n                        use_container_width=True,\n                        type="primary" if is_active else "secondary",\n                    ):\n                        st.session_state.ilm_route = route_item\n                        st.session_state.ilm_route_transition = True\n                        st.rerun()\n'''
if old_loop not in s:
    raise SystemExit('sidebar navigation loop anchor not found')
s = s.replace(old_loop, new_loop, 1)
app.write_text(s, encoding='utf-8')

# -----------------------------------------------------------------------------
# instrument_v03_user_guide.py — clean RTL interface and remove import widgets.
# The import engine remains available as a function and is rendered from the
# Instruments / Passport workspace instead.
# -----------------------------------------------------------------------------
guide = Path('instrument_v03_user_guide.py')
g = guide.read_text(encoding='utf-8')

css_anchor = '.v03-guide-tip b{color:inherit}\n\n/* Excel-vs-app expander added later by the camera module. */'
css_insert = '''.v03-guide-tip b{color:inherit}\n.v03-guide-banner-brand{direction:ltr;text-align:left;color:#0f2742;font-weight:900;font-size:1rem;unicode-bidi:isolate}\n.v03-guide-banner-title{direction:rtl;text-align:right;color:#0f2742;font-weight:900;font-size:1.06rem;margin-top:.35rem}\n\n/* The practical guide is Arabic-first. Keep widgets/data tables native, but\n   force narrative markdown and tab labels to read naturally right-to-left. */\ndiv[data-testid="stExpander"]:has(.v03-guide-shell-marker) summary,\ndiv[data-testid="stExpander"]:has(.v03-guide-shell-marker) summary *{\n  direction:rtl!important;text-align:right!important;unicode-bidi:plaintext!important\n}\ndiv[data-testid="stExpander"]:has(.v03-guide-shell-marker) div[data-testid="stMarkdownContainer"]{\n  direction:rtl!important;text-align:right!important;unicode-bidi:plaintext!important;line-height:1.9\n}\ndiv[data-testid="stExpander"]:has(.v03-guide-shell-marker) div[data-baseweb="tab-list"]{\n  direction:rtl!important;justify-content:flex-start!important\n}\ndiv[data-testid="stExpander"]:has(.v03-guide-shell-marker) button[data-baseweb="tab"],\ndiv[data-testid="stExpander"]:has(.v03-guide-shell-marker) button[data-baseweb="tab"] *{\n  direction:rtl!important;text-align:right!important;unicode-bidi:plaintext!important\n}\ndiv[data-testid="stExpander"]:has(.v03-guide-shell-marker) ul,\ndiv[data-testid="stExpander"]:has(.v03-guide-shell-marker) ol{\n  direction:rtl!important;text-align:right!important;padding-right:1.45rem!important;padding-left:0!important\n}\n\n/* Excel-vs-app expander added later by the camera module. */'''
if css_anchor not in g:
    raise SystemExit('guide css anchor not found')
g = g.replace(css_anchor, css_insert, 1)

old_banner = '<div class="v03-guide-banner"><b>🚀 Yahia QC Instrument Intelligence™ | <span dir="ltr" style="display:inline;color:inherit;font-size:inherit">Start here</span></b><span>افهم ما يحتويه التطبيق، دورة العمل الصحيحة، وكيف تسجل البيانات يدويًا أو من Excel قبل أن تبدأ.</span></div>'
new_banner = '''<div class="v03-guide-banner">\n  <div class="v03-guide-banner-brand">🚀 Yahia QC Instrument Intelligence™</div>\n  <div class="v03-guide-banner-title">دليل الاستخدام العملي</div>\n  <span>افهم المنصة، دورة العمل الصحيحة، وكيف تستخدمها يوميًا قبل أن تبدأ.</span>\n</div>'''
if old_banner not in g:
    raise SystemExit('guide banner anchor not found')
g = g.replace(old_banner, new_banner, 1)

g = g.replace('st.caption("الدليل الرسمي الموحد للمنتج — نسخة Product + User + Management قابلة للمشاركة، بدون أي بيانات خاصة بالـWorkspace.")', 'st.caption("الدليل الرسمي الموحد للمنتج — نسخة قابلة للمشاركة بدون أي بيانات خاصة بمساحة العمل.")', 1)

old_expander = '''    with st.expander("📘 دليل الاستخدام التفصيلي | \\u2066Practical User Guide\\u2069", expanded=True):\n        guide_tabs = st.tabs([\n            "🎯 ابدأ من هنا",\n            "↻ دورة الحياة",\n            "🧾 الاستخدام اليومي",\n            "📥 استيراد Excel",\n            "🔎 التحقيق",\n            "🔐 GMP & Privacy",\n        ])\n'''
new_expander = '''    with st.expander("📘 دليل الاستخدام العملي", expanded=True):\n        st.markdown('<div class="v03-guide-shell-marker"></div>', unsafe_allow_html=True)\n        guide_tabs = st.tabs([\n            "🎯 ابدأ من هنا",\n            "↻ دورة الحياة",\n            "🧾 الاستخدام اليومي",\n            "🔎 التحقيق",\n            "🔐 الحوكمة والخصوصية",\n        ])\n'''
if old_expander not in g:
    raise SystemExit('guide tabs anchor not found')
g = g.replace(old_expander, new_expander, 1)

# Remove the old Excel-import tab UI entirely.
excel_start = g.find('        with guide_tabs[3]:\n            _render_excel_import()')
invest_start = g.find('        with guide_tabs[4]:', excel_start)
if excel_start < 0 or invest_start < 0:
    raise SystemExit('guide Excel tab block not found')
g = g[:excel_start] + g[invest_start:]
g = g.replace('        with guide_tabs[4]:', '        with guide_tabs[3]:', 1)
g = g.replace('        with guide_tabs[5]:', '        with guide_tabs[4]:', 1)

# Add a concise pointer to the correct operational location; no template/uploader
# controls remain inside Guide.
start_marker = '<h3 style="margin-top:1.1rem">أفضل طريقة تبدأ بها</h3>'
start_note = '''<div class="v03-guide-rule"><b>لإضافة عدة أجهزة دفعة واحدة:</b> استخدم <span dir="ltr">MY INSTRUMENTS → Instruments → Import Instrument List</span>. القالب والرفع والمراجعة موجودة هناك، وليس داخل الدليل.</div>\n\n<h3 style="margin-top:1.1rem">أفضل طريقة تبدأ بها</h3>'''
if start_marker not in g:
    raise SystemExit('guide start marker not found')
g = g.replace(start_marker, start_note, 1)

guide.write_text(g, encoding='utf-8')

# -----------------------------------------------------------------------------
# instrument_supabase_app.py — make Passport the operational Instruments hub.
# Add one instrument, import a list, review the registry, then open a Passport.
# -----------------------------------------------------------------------------
core = Path('instrument_supabase_app.py')
c = core.read_text(encoding='utf-8')
c = c.replace('    st.header("Digital Instrument Passport")\n    st.caption("One instrument identity. One lifecycle view. One history you can actually use.")\n    with st.expander("➕ Add new instrument", expanded=(len(instruments)==0)):',
'''    st.header("Instrument Registry & Passport")\n    st.caption("Add one instrument, import an instrument list, then open any asset's Digital Passport.")\n    with st.expander("➕ Add one instrument | إضافة جهاز", expanded=(len(instruments)==0)):''', 1)

insert_anchor = '''                if ok: st.success(f"{clean} created."); st.rerun()\n                else: st.error(err or "Could not create instrument.")\n    if instruments:\n'''
insert_block = '''                if ok: st.success(f"{clean} created."); st.rerun()\n                else: st.error(err or "Could not create instrument.")\n\n    with st.expander("📥 إضافة / استيراد قائمة أجهزة | Import Instrument List", expanded=False):\n        if callable(globals().get("_render_excel_import")):\n            _render_excel_import()\n        else:\n            st.error("Instrument list import is temporarily unavailable.")\n\n    if instruments:\n        with st.expander("📋 سجل الأجهزة الحالي | Current Instrument Registry", expanded=False):\n            registry_rows = [{\n                "Instrument ID": x.get("instrument_code") or "",\n                "Instrument name": x.get("instrument_name") or "",\n                "Type": x.get("instrument_type") or "",\n                "Manufacturer": x.get("manufacturer") or "",\n                "Model": x.get("model") or "",\n                "Location": x.get("location") or "",\n                "Status": x.get("operational_status") or "",\n            } for x in instruments]\n            st.dataframe(pd.DataFrame(registry_rows), use_container_width=True, hide_index=True)\n\n'''
if insert_anchor not in c:
    raise SystemExit('passport import insertion anchor not found')
c = c.replace(insert_anchor, insert_block, 1)
core.write_text(c, encoding='utf-8')

# -----------------------------------------------------------------------------
# camera module — keep Excel-vs-app explanation, but point operational action
# to the Instruments workspace instead of implying Guide hosts the uploader.
# -----------------------------------------------------------------------------
cam = Path('instrument_camera_capture.py')
cc = cam.read_text(encoding='utf-8')
cc = cc.replace('الأفضل تنزيل Template التطبيق أو توحيد أسماء الأعمدة معه.', 'الأفضل فتح **MY INSTRUMENTS → Instruments → Import Instrument List** ثم تنزيل Template التطبيق من هناك أو توحيد أسماء الأعمدة معه.', 1)
cam.write_text(cc, encoding='utf-8')

print('patched app.py, guide, core registry and camera guide note')

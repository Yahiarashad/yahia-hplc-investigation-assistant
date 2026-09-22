from pathlib import Path

# Patch app.py ---------------------------------------------------------------
app = Path('app.py')
s = app.read_text(encoding='utf-8')

old_helper = '''def _ilm_mobile_route_transition():
    try:
        import streamlit.components.v1 as components
        components.html(
            """<script>
            try {
              const w = window.parent;
              w.scrollTo({top: 0, behavior: 'instant'});
              const sidebar = w.document.querySelector('section[data-testid="stSidebar"]');
              const collapse = sidebar && sidebar.querySelector('button[data-testid="stSidebarCollapseButton"], button[aria-label*="Close sidebar"], button[aria-label*="Collapse sidebar"]');
              if (collapse && w.innerWidth <= 768) { collapse.click(); }
            } catch (e) {}
            </script>""",
            height=0,
            width=0,
        )
    except Exception:
        pass
'''

new_helper = '''def _ilm_mobile_route_transition():
    """Finish a route change after the selected workspace has rendered.

    On mobile this closes Streamlit's overlay sidebar. On every device it moves
    the viewport to the first visible line of the active keyed workspace.
    """
    try:
        import streamlit.components.v1 as components
        components.html(
            """<script>
            (() => {
              try {
                const w = window.parent;
                const d = w.document;

                const activeWorkspace = () => {
                  const nodes = Array.from(d.querySelectorAll('[class*="st-key-ilm_workspace_"]'));
                  return nodes.find((el) => {
                    const cs = w.getComputedStyle(el);
                    const r = el.getBoundingClientRect();
                    return cs.display !== 'none' && cs.visibility !== 'hidden' && r.height > 0;
                  }) || null;
                };

                const scrollToSelected = () => {
                  const active = activeWorkspace();
                  if (active) {
                    active.scrollIntoView({behavior: 'instant', block: 'start', inline: 'nearest'});
                  } else {
                    const main = d.querySelector('[data-testid="stMain"]') || d.querySelector('section.main');
                    if (main && typeof main.scrollTo === 'function') {
                      main.scrollTo({top: 0, behavior: 'instant'});
                    }
                    try { w.scrollTo({top: 0, behavior: 'instant'}); } catch (_) { w.scrollTo(0, 0); }
                  }
                };

                const closeMobileSidebar = () => {
                  if (w.innerWidth > 768) return;
                  const sidebar = d.querySelector('section[data-testid="stSidebar"]');
                  if (!sidebar) return;
                  const r = sidebar.getBoundingClientRect();
                  const cs = w.getComputedStyle(sidebar);
                  const isOpen = cs.visibility !== 'hidden' && cs.display !== 'none' && r.width > 40 && r.right > 24 && r.left < w.innerWidth;
                  if (!isOpen) return;
                  const closeButton = sidebar.querySelector(
                    'button[data-testid="stSidebarCollapseButton"], button[aria-label*="Close sidebar"], button[aria-label*="Collapse sidebar"]'
                  ) || d.querySelector('button[data-testid="stSidebarCollapseButton"]');
                  if (closeButton) closeButton.click();
                };

                const finish = () => {
                  scrollToSelected();
                  closeMobileSidebar();
                };

                [0, 120, 320, 650, 1100].forEach((delay) => w.setTimeout(finish, delay));
              } catch (e) {}
            })();
            </script>""",
            height=0,
            width=0,
        )
    except Exception:
        pass
'''

if old_helper not in s:
    raise SystemExit('mobile helper anchor not found')
s = s.replace(old_helper, new_helper, 1)

early = '''if _signed_in_shell and st.session_state.get("ilm_user_role"):
    if st.session_state.pop("ilm_route_transition", False):
        _ilm_mobile_route_transition()
    with st.sidebar:
'''
replacement = '''if _signed_in_shell and st.session_state.get("ilm_user_role"):
    with st.sidebar:
'''
if early not in s:
    raise SystemExit('early transition anchor not found')
s = s.replace(early, replacement, 1)

onboarding_old = '''def _ilm_complete_role_onboarding():
    role_label = str(st.session_state.get("ilm_role_onboarding_select") or "QC Analyst")
    st.session_state.ilm_user_role = role_label
    st.session_state.ilm_route = "🏠 Dashboard"
'''
onboarding_new = '''def _ilm_complete_role_onboarding():
    role_label = str(st.session_state.get("ilm_role_onboarding_select") or "QC Analyst")
    st.session_state.ilm_user_role = role_label
    st.session_state.ilm_route = "🏠 Dashboard"
    st.session_state.ilm_route_transition = True
'''
if onboarding_old not in s:
    raise SystemExit('onboarding anchor not found')
s = s.replace(onboarding_old, onboarding_new, 1)

# Insert after the LAST final CSS block.
tail_anchor = '''</style>
""",
    unsafe_allow_html=True,
)
'''
tail_insert = '''</style>
""",
    unsafe_allow_html=True,
)

# Run route transition only after the active keyed workspace has been emitted.
if st.session_state.pop("ilm_route_transition", False):
    _ilm_mobile_route_transition()
'''
idx = s.rfind(tail_anchor)
if idx < 0:
    raise SystemExit('final style anchor not found')
s = s[:idx] + s[idx:].replace(tail_anchor, tail_insert, 1)
app.write_text(s, encoding='utf-8')

# Patch official 19-page guide -----------------------------------------------
pdf = Path('instrument_product_guide_pdf.py')
p = pdf.read_text(encoding='utf-8')
admin_old = """    story.append(Paragraph('Organization Admins can add or invite users, assign job roles, control account status and configure module-level privileges such as View, Add, Edit, Delete and Approve.',styles['body']))
    story.append(RTLBlock('الفكرة الأساسية هي الفصل بين Job Role الذي يرتب تجربة المستخدم وبين Access Privileges التي يجب أن تحكم ما يستطيع المستخدم فعله فعليًا. تغييرات الوصول يجب أن تكون قابلة للتتبع.'))
    story.append(_table([['ACTION','EXAMPLE'],['View','See instrument or report data'],['Add','Create a new record'],['Edit','Modify an existing record'],['Delete / Archive','Remove or retire according to governance'],['Approve','Perform a controlled approval action when implemented']],[48*mm,116*mm])); story.append(PageBreak())
"""
admin_new = """    story.append(Paragraph('Organization Admins can add or invite users, assign job roles, control account status and configure module-level privileges such as View, Add, Edit, Delete and Approve.',styles['body']))
    story.append(RTLBlock('الفكرة الأساسية هي الفصل بين Job Role الذي يرتب تجربة المستخدم وبين Access Privileges التي يجب أن تحكم ما يستطيع المستخدم فعله فعليًا. تغييرات الوصول يجب أن تكون قابلة للتتبع.'))
    story.append(Paragraph('Secure invitation is enforced server-side: the signed-in caller is validated, workspace-admin authority is checked, and service-role capability remains on the server. Access changes require an accountable reason and are written to the access audit trail.',styles['small']))
    story.append(RTLBlock('الأمان ليس مجرد زر مخفي في الواجهة: دعوة المستخدم والتحقق من صلاحية مدير الـWorkspace تتم على الخادم، وتغييرات الوصول يجب أن تترك أثرًا واضحًا في Audit Trail.',size=9.2,leading=14,space_after=5))
    story.append(_table([['ACTION','EXAMPLE'],['View','See instrument or report data'],['Add','Create a new record'],['Edit','Modify an existing record'],['Delete / Archive','Remove or retire according to governance'],['Approve','Perform a controlled approval action when implemented']],[48*mm,116*mm])); story.append(PageBreak())
"""
if admin_old not in p:
    raise SystemExit('official guide admin anchor not found')
p = p.replace(admin_old, admin_new, 1)
pdf.write_text(p, encoding='utf-8')

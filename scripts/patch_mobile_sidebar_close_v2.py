from pathlib import Path

p = Path('app.py')
s = p.read_text(encoding='utf-8')

start = s.index('def _ilm_mobile_route_transition():')
end = s.index('\n\ndef _shell_rest_list', start)
new_helper = r'''def _ilm_mobile_route_transition():
    """Close the mobile sidebar and focus the active route after rerender."""
    try:
        import streamlit.components.v1 as components
        components.html(
            """<script>
            (() => {
              const w = window.parent;
              const d = w.document;

              function activeWorkspace() {
                const nodes = Array.from(d.querySelectorAll('[class*="st-key-ilm_workspace_"]'));
                return nodes.find((el) => {
                  try {
                    const cs = w.getComputedStyle(el);
                    const r = el.getBoundingClientRect();
                    return cs.display !== 'none' && cs.visibility !== 'hidden' && r.height > 0;
                  } catch (_) { return false; }
                }) || null;
              }

              function scrollMainTop() {
                const active = activeWorkspace();
                const main = d.querySelector('[data-testid="stMain"]') || d.querySelector('section.main') || d.querySelector('main');
                try {
                  if (main && typeof main.scrollTo === 'function') main.scrollTo({top: 0, left: 0, behavior: 'instant'});
                } catch (_) {}
                try { d.documentElement.scrollTop = 0; d.body.scrollTop = 0; } catch (_) {}
                try { w.scrollTo({top: 0, left: 0, behavior: 'instant'}); } catch (_) { try { w.scrollTo(0,0); } catch(__){} }
                if (active) {
                  try { active.scrollIntoView({behavior: 'instant', block: 'start', inline: 'nearest'}); } catch (_) {}
                }
              }

              function candidateButtons(sidebar) {
                const exact = [
                  d.querySelector('button[data-testid="stSidebarCollapseButton"]'),
                  d.querySelector('[data-testid="stSidebarCollapseButton"] button'),
                  d.querySelector('button[aria-label="Close sidebar"]'),
                  d.querySelector('button[aria-label*="Close sidebar"]'),
                  d.querySelector('button[title*="Close sidebar"]')
                ].filter(Boolean);
                const local = sidebar ? Array.from(sidebar.querySelectorAll('button')) : [];
                return [...new Set([...exact, ...local])];
              }

              function closeSidebar() {
                if (w.innerWidth > 768) return true;
                const sidebar = d.querySelector('section[data-testid="stSidebar"]');
                if (!sidebar) return true;
                const sr = sidebar.getBoundingClientRect();
                const cs = w.getComputedStyle(sidebar);
                const open = cs.display !== 'none' && cs.visibility !== 'hidden' && sr.width > 80 && sr.right > 0 && sr.left < w.innerWidth;
                if (!open) return true;

                const buttons = candidateButtons(sidebar);
                let target = buttons.find((b) => {
                  const label = ((b.getAttribute('aria-label') || '') + ' ' + (b.getAttribute('title') || '') + ' ' + (b.getAttribute('data-testid') || '')).toLowerCase();
                  return label.includes('sidebar') && (label.includes('close') || label.includes('collapse'));
                });

                if (!target) {
                  target = buttons.find((b) => {
                    const r = b.getBoundingClientRect();
                    return r.top >= 45 && r.top <= 190 && r.right >= sr.right - 110 && r.left <= sr.right;
                  });
                }

                if (target) {
                  try { target.click(); return true; } catch (_) {}
                }

                try {
                  d.dispatchEvent(new KeyboardEvent('keydown', {key:'Escape', code:'Escape', keyCode:27, which:27, bubbles:true}));
                } catch (_) {}
                return false;
              }

              function finish() {
                closeSidebar();
                w.setTimeout(scrollMainTop, 70);
              }

              [0, 100, 250, 500, 900, 1400, 2200].forEach((delay) => w.setTimeout(finish, delay));
            })();
            </script>""",
            height=0,
            width=0,
        )
    except Exception:
        pass
'''
s = s[:start] + new_helper + s[end:]

old_nav = '''                if st.button(\n                    route_item,\n                    key="ilm_nav_" + route_item,\n                    use_container_width=True,\n                    type="primary" if is_active else "secondary",\n                ):\n                    if not is_active:\n                        st.session_state.ilm_route = route_item\n                        st.session_state.ilm_route_transition = True\n                        st.rerun()\n'''
new_nav = '''                if st.button(\n                    route_item,\n                    key="ilm_nav_" + route_item,\n                    use_container_width=True,\n                    type="primary" if is_active else "secondary",\n                ):\n                    st.session_state.ilm_route = route_item\n                    st.session_state.ilm_route_transition = True\n                    st.rerun()\n'''
if old_nav not in s:
    raise SystemExit('sidebar nav anchor not found')
s = s.replace(old_nav, new_nav, 1)

p.write_text(s, encoding='utf-8')
print('patched app.py')

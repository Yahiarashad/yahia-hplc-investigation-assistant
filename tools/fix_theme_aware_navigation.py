from pathlib import Path

p = Path('app.py')
s = p.read_text(encoding='utf-8')

old_sidebar = '''.ilm-route-link{
  display:flex!important;align-items:center;justify-content:center;
  min-height:50px;margin:.34rem 0;padding:.55rem .75rem;
  border:1px solid rgba(226,232,240,.82);border-radius:17px;
  color:#f8fafc!important;text-decoration:none!important;font-weight:650;
  background:rgba(255,255,255,.025);box-sizing:border-box;
}
.ilm-route-link.active{background:#ff4b4b!important;border-color:#ff7676!important;color:white!important}
.ilm-route-link:visited{color:#f8fafc!important}
.ilm-route-link:hover{border-color:#ffffff!important}
'''
new_sidebar = '''.ilm-route-link{
  display:flex!important;align-items:center;justify-content:center;
  min-height:50px;margin:.34rem 0;padding:.55rem .75rem;
  border:1px solid rgba(128,128,128,.38);border-radius:17px;
  color:var(--text-color)!important;text-decoration:none!important;font-weight:650;
  background:var(--secondary-background-color)!important;box-sizing:border-box;
}
.ilm-route-link.active{background:#ff4b4b!important;border-color:#ff7676!important;color:white!important}
.ilm-route-link:visited{color:var(--text-color)!important}
.ilm-route-link.active:visited{color:white!important}
.ilm-route-link:hover{border-color:var(--primary-color)!important;color:var(--text-color)!important}
.ilm-route-link.active:hover{color:white!important}
'''
if old_sidebar not in s:
    raise SystemExit('desktop/sidebar navigation CSS anchor not found')
s = s.replace(old_sidebar, new_sidebar, 1)

old_mobile = '''      .ilm-mobile-route-link {
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
'''
new_mobile = '''      .ilm-mobile-route-link {
        display:flex !important; align-items:center; justify-content:center;
        min-height:48px; margin:.34rem 0; padding:.52rem .68rem;
        border:1px solid rgba(128,128,128,.38); border-radius:15px;
        color:var(--text-color) !important; text-decoration:none !important; font-weight:700;
        background:var(--secondary-background-color) !important; box-sizing:border-box;
      }
      .ilm-mobile-route-link.active {
        background:#ff4b4b !important; border-color:#ff7676 !important; color:white !important;
      }
      .ilm-mobile-route-link:visited { color:var(--text-color) !important; }
      .ilm-mobile-route-link.active:visited { color:white !important; }
      .ilm-mobile-route-link:hover { border-color:var(--primary-color) !important; color:var(--text-color) !important; }
      .ilm-mobile-route-link.active:hover { color:white !important; }
'''
if old_mobile not in s:
    raise SystemExit('mobile navigation CSS anchor not found')
s = s.replace(old_mobile, new_mobile, 1)

p.write_text(s, encoding='utf-8')
print('Theme-aware navigation colors applied')

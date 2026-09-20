# Three-level instrument email notification center
# User -> Manager -> Director escalation model.
# Email delivery is handled by the Supabase Edge Function instrument-email-notifications.

from __future__ import annotations

from html import escape
from urllib import parse as urlparse

import pandas as pd
import streamlit as st


NOTIFICATION_FUNCTION = "instrument-email-notifications"


def _notif_user():
    try:
        return _auth_user() or {}
    except Exception:
        return {}


def _notif_defaults():
    user = _notif_user()
    return {
        "enabled": True,
        "user_level_enabled": True,
        "manager_level_enabled": True,
        "director_level_enabled": True,
        "user_email": str(user.get("email") or ""),
        "manager_email": "",
        "director_email": "",
        "user_due_days": 30,
        "manager_overdue_days": 1,
        "director_overdue_days": 14,
        "director_critical_event_days": 3,
        "timezone": "UTC",
        "digest_hour": 7,
    }


def _notif_preferences():
    rows, err, ok = _db_list(
        "instrument_notification_preferences",
        "user_id,enabled,user_level_enabled,manager_level_enabled,director_level_enabled,user_email,manager_email,director_email,user_due_days,manager_overdue_days,director_overdue_days,director_critical_event_days,timezone,digest_hour,updated_at",
        "updated_at.desc",
    )
    if ok and rows:
        merged = _notif_defaults()
        merged.update(rows[0])
        return merged, "", True
    return _notif_defaults(), err, ok


def _notif_save(payload):
    user = _notif_user()
    uid = str(user.get("id") or "")
    if not uid:
        return False, "Signed-in user ID is unavailable."
    existing, _, ok = _db_list("instrument_notification_preferences", "user_id")
    if not ok:
        return False, "Could not read notification preferences."
    payload = dict(payload)
    payload["user_id"] = uid
    if existing:
        path = f"instrument_notification_preferences?user_id=eq.{urlparse.quote(uid)}"
        success, _, _, err = _db_request(path, method="PATCH", payload={k: v for k, v in payload.items() if k != "user_id"}, prefer="return=representation")
    else:
        success, _, _, err = _db_insert("instrument_notification_preferences", payload)
    return success, err or ""


def _notif_call(*, dry_run=True, force=False):
    if not SUPABASE_URL or not SUPABASE_KEY:
        return False, None, "Supabase is not configured."
    ok, data, status, err = _http_json(
        f"{SUPABASE_URL}/functions/v1/{NOTIFICATION_FUNCTION}",
        method="POST",
        payload={"dry_run": bool(dry_run), "force": bool(force)},
        headers={
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {_auth_token()}",
            "Content-Type": "application/json",
        },
        timeout=45,
    )
    if status == 401 and _auth_refresh():
        ok, data, status, err = _http_json(
            f"{SUPABASE_URL}/functions/v1/{NOTIFICATION_FUNCTION}",
            method="POST",
            payload={"dry_run": bool(dry_run), "force": bool(force)},
            headers={
                "apikey": SUPABASE_KEY,
                "Authorization": f"Bearer {_auth_token()}",
                "Content-Type": "application/json",
            },
            timeout=45,
        )
    return ok, data, err or (f"HTTP {status}" if not ok else "")


def _level_card(title, subtitle, items, tone):
    rows = "".join(f"<li>{escape(str(x))}</li>" for x in items)
    return (
        f'<div class="notif-card {tone}"><div class="notif-eyebrow">{escape(title)}</div>'
        f'<div class="notif-sub">{escape(subtitle)}</div><ul>{rows}</ul></div>'
    )


def _render_preview(preview):
    if not preview:
        st.info("No notification preview is available yet.")
        return
    cols = st.columns(3)
    labels = {"user": "👤 User", "manager": "🧑‍💼 Manager", "director": "🏢 Director"}
    for idx, level in enumerate(["user", "manager", "director"]):
        row = next((x for x in preview if str(x.get("level")) == level), {})
        with cols[idx]:
            st.metric(labels[level], int(row.get("count") or 0))
            recipient = str(row.get("recipient") or "Not configured")
            st.caption(recipient)
            if not bool(row.get("enabled", True)):
                st.caption("Level disabled")
    st.markdown("#### Evidence-based preview")
    for level in ["user", "manager", "director"]:
        row = next((x for x in preview if str(x.get("level")) == level), {})
        alerts = row.get("alerts") or []
        if not alerts:
            continue
        with st.expander(f"{labels[level]} · {len(alerts)} signal(s)", expanded=False):
            for alert in alerts[:30]:
                sev = str(alert.get("severity") or "info").upper()
                code = str(alert.get("code") or "Instrument")
                title = str(alert.get("title") or "Signal")
                detail = str(alert.get("detail") or "")
                st.markdown(f"**{code} · {title}**  \n`{sev}` · {detail}")
            if len(alerts) > 30:
                st.caption(f"+ {len(alerts)-30} more signal(s)")


def render_instrument_notification_center():
    st.markdown(
        """
<style>
.notif-hero{border:1px solid rgba(214,184,95,.45);border-radius:24px;padding:1.15rem 1.2rem;margin:.35rem 0 1rem;background:linear-gradient(145deg,#061322,#0a2032);color:#fff;box-shadow:0 12px 32px rgba(2,12,27,.12)}
.notif-hero .k{font-size:.72rem;letter-spacing:.12em;color:#e1c56d;font-weight:900}.notif-hero h2{color:#fff!important;margin:.22rem 0 .35rem!important}.notif-hero p{color:#c8d8e5;margin:.2rem 0}.notif-hero .line{color:#71d6e7;font-weight:800}
.notif-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:.65rem;margin:.7rem 0 1rem}.notif-card{border:1px solid #e3e8ef;border-radius:17px;padding:.85rem;background:#fff;box-shadow:0 5px 16px rgba(15,23,42,.04)}.notif-card.user{border-top:4px solid #2f83aa}.notif-card.manager{border-top:4px solid #d2a62a}.notif-card.director{border-top:4px solid #c84646}.notif-eyebrow{font-weight:900;color:#102a43}.notif-sub{font-size:.78rem;color:#718096;margin:.15rem 0 .45rem}.notif-card ul{padding-left:1.1rem;margin:.2rem 0;color:#506579;font-size:.82rem}.notif-card li{margin:.28rem 0}
.notif-flow{display:flex;align-items:center;gap:.38rem;flex-wrap:wrap;margin:.55rem 0 1rem}.notif-pill{border:1px solid #dce4ec;border-radius:999px;padding:.35rem .55rem;background:#fff;font-size:.74rem;font-weight:800;color:#234}.notif-arrow{color:#9aa9b7}
@media(max-width:760px){.notif-grid{grid-template-columns:1fr}.notif-hero{padding:1rem}.notif-card{padding:.8rem}.notif-flow{gap:.28rem}}
</style>
<div class="notif-hero">
  <div class="k">QC INSTRUMENT INTELLIGENCE · ESCALATION ENGINE</div>
  <h2>🔔 Email Notification Control Center</h2>
  <p>Right signal → right person → right escalation level.</p>
  <p class="line">Reduce missed controls without creating notification noise.</p>
</div>
""",
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="notif-flow"><span class="notif-pill">USER · act on routine work</span><span class="notif-arrow">→</span><span class="notif-pill">MANAGER · review risk</span><span class="notif-arrow">→</span><span class="notif-pill">DIRECTOR · see escalated business risk</span></div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="notif-grid">' +
        _level_card("LEVEL 1 · USER", "Operational reminder", [
            "Calibration / PM / Qualification due soon",
            "Open instrument events",
            "Next incomplete lifecycle milestone",
        ], "user") +
        _level_card("LEVEL 2 · MANAGER", "Risk review", [
            "Overdue controlled activities",
            "High / Critical open events",
            "Open calibration OOC",
            "Availability below instrument target",
        ], "manager") +
        _level_card("LEVEL 3 · DIRECTOR", "Escalated business visibility", [
            "Persistent overdue controls",
            "Critical events open beyond escalation window",
            "Open calibration OOC",
            "Capacity risk: low availability + high utilization",
        ], "director") +
        '</div>',
        unsafe_allow_html=True,
    )

    prefs, pref_err, pref_ok = _notif_preferences()
    if not pref_ok and pref_err:
        st.warning("Notification settings could not be loaded completely.")
        st.caption(pref_err)

    st.markdown("### ⚙ Notification policy")
    st.caption("These settings define who receives each level. They do not change Supabase RLS or application permissions.")
    with st.form("ilm_notification_preferences_form"):
        enabled = st.toggle("Enable email notification system", value=bool(prefs.get("enabled", True)))
        c1, c2, c3 = st.columns(3)
        with c1:
            user_level = st.toggle("👤 User level", value=bool(prefs.get("user_level_enabled", True)))
            user_email = st.text_input("User email", value=str(prefs.get("user_email") or _notif_user().get("email") or ""))
            user_due_days = st.number_input("Warn before due date (days)", min_value=1, max_value=90, value=int(prefs.get("user_due_days") or 30), step=1)
        with c2:
            manager_level = st.toggle("🧑‍💼 Manager level", value=bool(prefs.get("manager_level_enabled", True)))
            manager_email = st.text_input("Manager email", value=str(prefs.get("manager_email") or ""))
            manager_overdue_days = st.number_input("Escalate overdue after (days)", min_value=0, max_value=90, value=int(prefs.get("manager_overdue_days") or 1), step=1)
        with c3:
            director_level = st.toggle("🏢 Director level", value=bool(prefs.get("director_level_enabled", True)))
            director_email = st.text_input("Director email", value=str(prefs.get("director_email") or ""))
            director_overdue_days = st.number_input("Director overdue escalation (days)", min_value=1, max_value=180, value=int(prefs.get("director_overdue_days") or 14), step=1)
            director_event_days = st.number_input("Critical event escalation (days open)", min_value=0, max_value=60, value=int(prefs.get("director_critical_event_days") or 3), step=1)

        t1, t2 = st.columns(2)
        with t1:
            timezone = st.selectbox(
                "Timezone",
                ["UTC", "Africa/Cairo", "Asia/Riyadh", "Asia/Dubai", "Europe/London"],
                index=["UTC", "Africa/Cairo", "Asia/Riyadh", "Asia/Dubai", "Europe/London"].index(str(prefs.get("timezone") or "UTC")) if str(prefs.get("timezone") or "UTC") in ["UTC", "Africa/Cairo", "Asia/Riyadh", "Asia/Dubai", "Europe/London"] else 0,
            )
        with t2:
            digest_hour = st.number_input("Preferred digest hour (0–23)", min_value=0, max_value=23, value=int(prefs.get("digest_hour") or 7), step=1)

        saved = st.form_submit_button("💾 Save notification policy", use_container_width=True)
        if saved:
            payload = {
                "enabled": enabled,
                "user_level_enabled": user_level,
                "manager_level_enabled": manager_level,
                "director_level_enabled": director_level,
                "user_email": user_email.strip(),
                "manager_email": manager_email.strip(),
                "director_email": director_email.strip(),
                "user_due_days": int(user_due_days),
                "manager_overdue_days": int(manager_overdue_days),
                "director_overdue_days": int(director_overdue_days),
                "director_critical_event_days": int(director_event_days),
                "timezone": timezone,
                "digest_hour": int(digest_hour),
            }
            ok, err = _notif_save(payload)
            if ok:
                st.success("Notification policy saved.")
            else:
                st.error("Could not save notification policy.")
                if err:
                    st.caption(err)

    st.markdown("### 🧠 What would be emailed right now?")
    p1, p2 = st.columns(2)
    with p1:
        preview_clicked = st.button("🔎 Build notification preview", use_container_width=True, key="notif_preview_btn")
    with p2:
        send_clicked = st.button("✉ Send digest now", use_container_width=True, key="notif_send_btn")

    if preview_clicked:
        with st.spinner("Evaluating lifecycle, events, calibration and performance signals…"):
            ok, data, err = _notif_call(dry_run=True)
        if ok and isinstance(data, dict):
            st.session_state["ilm_notification_preview"] = data.get("preview") or []
            st.success("Preview generated from live evidence.")
        else:
            st.error("Could not generate notification preview.")
            if err:
                st.caption(err)

    if send_clicked:
        with st.spinner("Building and sending the three-level digest…"):
            ok, data, err = _notif_call(dry_run=False)
        if ok and isinstance(data, dict):
            results = data.get("sent") or []
            if not results:
                st.info("No enabled level had both a recipient and an actionable signal to send.")
            else:
                successes = sum(1 for r in results if r.get("success"))
                skipped = sum(1 for r in results if r.get("skipped"))
                st.success(f"Email run completed · {successes} sent · {skipped} skipped.")
                for r in results:
                    level = str(r.get("level") or "").upper()
                    recipient = str(r.get("recipient") or "")
                    if r.get("success"):
                        st.caption(f"✅ {level} → {recipient}")
                    elif r.get("skipped"):
                        st.caption(f"↷ {level} → {recipient} · already sent today")
                    else:
                        st.caption(f"⚠ {level} → {recipient} · {r.get('error') or 'send failed'}")
            st.session_state["ilm_notification_preview"] = data.get("preview") or []
        else:
            st.error("Email delivery is not active yet.")
            if isinstance(data, dict) and data.get("error"):
                st.caption(str(data.get("error")))
            elif err:
                st.caption(err)
            st.info("The notification engine is installed. To send real email, configure RESEND_API_KEY in Supabase Edge Function secrets and optionally NOTIFICATION_FROM_EMAIL / NOTIFICATION_APP_URL.")

    _render_preview(st.session_state.get("ilm_notification_preview") or [])

    st.markdown("### 🧾 Notification history")
    logs, log_err, log_ok = _db_list(
        "instrument_notification_log",
        "created_at,notification_level,recipient_email,notification_type,severity,subject,status,sent_at,error_message",
        "created_at.desc",
    )
    if log_ok and logs:
        frame = pd.DataFrame(logs[:50])
        st.dataframe(frame, use_container_width=True, hide_index=True)
    elif log_ok:
        st.caption("No notification emails have been logged yet.")
    else:
        st.caption(log_err or "Notification history is unavailable.")

    with st.expander("📌 Automation status & design boundary", expanded=False):
        st.markdown(
            """
**What is already live**
- Three escalation levels with separate recipients and thresholds.
- Live evidence evaluation from lifecycle dates, events, calibration OOC and monthly performance.
- Email-ready Supabase Edge Function with daily deduplication and send history.
- RLS-protected notification settings and history for each account.

**What still requires one external mail credential**
- Real email delivery requires a transactional email API key (`RESEND_API_KEY`).
- Automatic scheduled delivery requires a secure scheduler/service invocation. Until that is configured, **Send digest now** runs the same engine manually.

**GMP boundary**
Email is an attention mechanism, not the official record and not proof of root cause or disposition. The controlled record stays in approved systems/SOP-controlled records.
"""
        )

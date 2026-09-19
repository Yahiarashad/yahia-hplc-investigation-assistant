import csv
import json
import os
import sqlite3
from datetime import datetime, timezone
from io import StringIO
from pathlib import Path
from urllib import request

import streamlit as st

DB_PATH = Path("/tmp/yahia_beta_feedback.db")


def _now_iso():
    return datetime.now(timezone.utc).isoformat()


def _secret(name, default=None):
    try:
        value = st.secrets.get(name)
        return value if value not in (None, "") else default
    except Exception:
        return os.environ.get(name, default)


def init_feedback_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS beta_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                source TEXT NOT NULL,
                event TEXT NOT NULL,
                language TEXT,
                metadata_json TEXT,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS beta_feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                source TEXT NOT NULL,
                language TEXT,
                rating INTEGER,
                outcome TEXT,
                accuracy TEXT,
                most_useful TEXT,
                improvement TEXT,
                desired_feature TEXT,
                name TEXT,
                contact TEXT,
                consent_research INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.commit()


def external_storage_configured():
    return bool(_secret("BETA_FEEDBACK_WEBHOOK"))


def _post_webhook(payload):
    webhook = _secret("BETA_FEEDBACK_WEBHOOK")
    if not webhook:
        return False

    outbound = dict(payload)
    token = _secret("BETA_FEEDBACK_WEBHOOK_TOKEN", "")
    if token:
        outbound["token"] = str(token)

    try:
        body = json.dumps(outbound, ensure_ascii=False).encode("utf-8")
        req = request.Request(
            webhook,
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with request.urlopen(req, timeout=8) as resp:
            status_ok = 200 <= int(resp.status) < 300
            if not status_ok:
                return False
            raw = resp.read().decode("utf-8", errors="replace").strip()
            if not raw:
                return True
            try:
                parsed = json.loads(raw)
                if isinstance(parsed, dict) and "ok" in parsed:
                    return parsed.get("ok") is True
            except Exception:
                pass
            return True
    except Exception:
        return False


def test_external_storage():
    if not external_storage_configured():
        return False
    return _post_webhook(
        {
            "type": "event",
            "session_id": "dashboard-storage-test",
            "source": "beta_dashboard",
            "event": "storage_test",
            "language": "en",
            "metadata": {"purpose": "connection_test"},
            "created_at": _now_iso(),
        }
    )


def record_event(session_id, source, event, language="", metadata=None):
    init_feedback_db()
    metadata = metadata or {}
    created_at = _now_iso()
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            INSERT INTO beta_events(session_id, source, event, language, metadata_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                str(session_id),
                str(source),
                str(event),
                str(language or ""),
                json.dumps(metadata, ensure_ascii=False),
                created_at,
            ),
        )
        conn.commit()
    _post_webhook(
        {
            "type": "event",
            "session_id": str(session_id),
            "source": str(source),
            "event": str(event),
            "language": str(language or ""),
            "metadata": metadata,
            "created_at": created_at,
        }
    )


def save_feedback(
    session_id,
    source,
    language,
    rating,
    outcome,
    accuracy,
    most_useful,
    improvement,
    desired_feature,
    name,
    contact,
    consent_research,
):
    init_feedback_db()
    created_at = _now_iso()
    row = {
        "type": "feedback",
        "session_id": str(session_id),
        "source": str(source),
        "language": str(language or ""),
        "rating": int(rating) if rating else None,
        "outcome": str(outcome or ""),
        "accuracy": str(accuracy or ""),
        "most_useful": str(most_useful or "").strip(),
        "improvement": str(improvement or "").strip(),
        "desired_feature": str(desired_feature or ""),
        "name": str(name or "").strip(),
        "contact": str(contact or "").strip(),
        "consent_research": bool(consent_research),
        "created_at": created_at,
    }
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            INSERT INTO beta_feedback(
                session_id, source, language, rating, outcome, accuracy,
                most_useful, improvement, desired_feature, name, contact,
                consent_research, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                row["session_id"],
                row["source"],
                row["language"],
                row["rating"],
                row["outcome"],
                row["accuracy"],
                row["most_useful"],
                row["improvement"],
                row["desired_feature"],
                row["name"],
                row["contact"],
                1 if row["consent_research"] else 0,
                row["created_at"],
            ),
        )
        conn.commit()
    _post_webhook(row)
    record_event(session_id, source, "feedback_submitted", language)


def _labels(language, source):
    is_ar = language == "ar"
    if is_ar:
        return {
            "title": "ساعدني أبني النسخة القادمة — دقيقة واحدة فقط",
            "intro": "ملاحظتك هنا أهم من المجاملة. نريد أن نعرف ما الذي نجح فعلًا وما الذي يحتاج تطويرًا.",
            "rating": "تقييم التجربة",
            "outcome": "هل ساعدتك التجربة؟",
            "outcome_options": ["ساعدتني جدًا", "ساعدتني جزئيًا", "لم تساعدني بعد"],
            "accuracy": "هل النتيجة/التحليل عبّر عنك أو عن الحالة بدقة؟",
            "accuracy_options": ["نعم", "إلى حد ما", "لا"],
            "most": "أكثر شيء كان مفيدًا لك",
            "improve": "لو هنطوّر حاجة واحدة فورًا، تكون إيه؟",
            "feature": "أي ميزة ستكون الأكثر قيمة لك مستقبلًا؟",
            "features": [
                "تحقيقات HPLC خطوة بخطوة",
                "تقييم واتخاذ القرار",
                "تقرير Investigation جاهز للمراجعة",
                "تدريب Cases واقعية",
                "Team Dashboard للمشرفين",
                "تكامل مع SOP / Method",
            ],
            "name": "الاسم — اختياري",
            "contact": "LinkedIn أو Email — اختياري",
            "consent": "أوافق على استخدام ملاحظاتي بصورة مجهولة لتحسين النسخة التأسيسية.",
            "privacy": "لا نطلب منك كتابة أي بيانات سرية تخص الشركة أو المنتج أو الطريقة التحليلية هنا.",
            "submit": "إرسال الملاحظة",
            "thanks": "وصلت ملاحظتك 🙌 شكرًا لأنك جزء من النسخة التأسيسية.",
        }
    return {
        "title": "Help shape the next version — about 60 seconds",
        "intro": "Useful feedback matters more than praise. Tell us what worked and what should improve.",
        "rating": "Overall experience",
        "outcome": "Did the experience help you?",
        "outcome_options": ["A lot", "Partly", "Not yet"],
        "accuracy": "Did the result/analysis accurately reflect your thinking or case?",
        "accuracy_options": ["Yes", "Partly", "No"],
        "most": "What was most useful?",
        "improve": "If we improve one thing next, what should it be?",
        "feature": "Which future feature would be most valuable to you?",
        "features": [
            "Step-by-step HPLC investigations",
            "Decision calibration assessment",
            "Review-ready investigation report",
            "Real-world case training",
            "Team dashboard for supervisors",
            "SOP / method integration",
        ],
        "name": "Name — optional",
        "contact": "LinkedIn or email — optional",
        "consent": "I agree that my anonymized feedback may be used to improve the founding beta.",
        "privacy": "Do not enter confidential company, product, method, or patient information here.",
        "submit": "Send feedback",
        "thanks": "Feedback received 🙌 Thank you for helping shape the founding beta.",
    }


def render_feedback_form(source, session_id, language="en", compact=False):
    labels = _labels(language, source)
    is_ar = language == "ar"
    key_prefix = f"beta_fb_{source}_{session_id}"

    if st.session_state.get(f"{key_prefix}_done"):
        st.success(labels["thanks"])
        return

    expander_label = labels["title"]
    container = st.expander(expander_label, expanded=not compact)
    with container:
        if is_ar:
            st.markdown(
                "<div style='direction:rtl;text-align:right;unicode-bidi:plaintext;'>"
                f"<b>{labels['intro']}</b><br><span style='color:#6b7280'>{labels['privacy']}</span>"
                "</div>",
                unsafe_allow_html=True,
            )
        else:
            st.markdown(f"**{labels['intro']}**")
            st.caption(labels["privacy"])

        with st.form(f"{key_prefix}_form", clear_on_submit=False):
            rating = st.slider(labels["rating"], 1, 5, 4)
            outcome = st.radio(labels["outcome"], labels["outcome_options"], horizontal=True)
            accuracy = st.radio(labels["accuracy"], labels["accuracy_options"], horizontal=True)
            most_useful = st.text_area(labels["most"], height=80)
            improvement = st.text_area(labels["improve"], height=80)
            desired_feature = st.selectbox(labels["feature"], labels["features"])
            c1, c2 = st.columns(2)
            with c1:
                name = st.text_input(labels["name"])
            with c2:
                contact = st.text_input(labels["contact"])
            consent = st.checkbox(labels["consent"], value=True)
            submitted = st.form_submit_button(labels["submit"], use_container_width=True, type="primary")

        if submitted:
            save_feedback(
                session_id=session_id,
                source=source,
                language=language,
                rating=rating,
                outcome=outcome,
                accuracy=accuracy,
                most_useful=most_useful,
                improvement=improvement,
                desired_feature=desired_feature,
                name=name,
                contact=contact,
                consent_research=consent,
            )
            st.session_state[f"{key_prefix}_done"] = True
            st.success(labels["thanks"])


def dashboard_snapshot():
    init_feedback_db()
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        events = [dict(r) for r in conn.execute("SELECT * FROM beta_events ORDER BY id DESC").fetchall()]
        feedback = [dict(r) for r in conn.execute("SELECT * FROM beta_feedback ORDER BY id DESC").fetchall()]
    return events, feedback


def rows_to_csv(rows):
    if not rows:
        return ""
    out = StringIO()
    writer = csv.DictWriter(out, fieldnames=list(rows[0].keys()))
    writer.writeheader()
    writer.writerows(rows)
    return out.getvalue()

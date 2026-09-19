# Standalone Streamlit entrypoint for the Instrument Lifecycle application.
# This branch is intentionally isolated from the main HPLC / Decision Gap app.
# v0.1.2 adds optional durable Google Sheets storage through an Apps Script
# webhook, while keeping local SQLite as a short-lived fallback/cache.

from __future__ import annotations

import io
import json
import sqlite3
from pathlib import Path
from urllib import error as urlerror
from urllib import request as urlrequest

import pandas as pd
import streamlit as st

DB_PATH = Path("/tmp/yahia_qc_instrument_lifecycle.sqlite3")


def _secret(name: str) -> str:
    try:
        return str(st.secrets.get(name, "") or "").strip()
    except Exception:
        return ""


REMOTE_URL = _secret("INSTRUMENT_LIFECYCLE_WEBHOOK")
REMOTE_TOKEN = _secret("INSTRUMENT_LIFECYCLE_TOKEN")


def _remote_configured() -> bool:
    return bool(REMOTE_URL and REMOTE_TOKEN)


def _remote_request(payload: dict, timeout: int = 12):
    if not _remote_configured():
        return None
    body = dict(payload)
    body["token"] = REMOTE_TOKEN
    req = urlrequest.Request(
        REMOTE_URL,
        data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlrequest.urlopen(req, timeout=timeout) as response:
            raw = response.read().decode("utf-8")
        parsed = json.loads(raw)
        return parsed if isinstance(parsed, dict) else None
    except (urlerror.URLError, TimeoutError, ValueError, json.JSONDecodeError):
        return None


def _init_store() -> None:
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS app_state (
                state_key TEXT PRIMARY KEY,
                state_value TEXT NOT NULL
            )
            """
        )
        conn.commit()


def _get_value(key: str) -> str | None:
    with sqlite3.connect(DB_PATH) as conn:
        row = conn.execute(
            "SELECT state_value FROM app_state WHERE state_key = ?",
            (key,),
        ).fetchone()
    return row[0] if row else None


def _set_value(key: str, value: str) -> None:
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            INSERT INTO app_state (state_key, state_value)
            VALUES (?, ?)
            ON CONFLICT(state_key) DO UPDATE SET state_value = excluded.state_value
            """,
            (key, value),
        )
        conn.commit()


def _load_df(key: str):
    raw = _get_value(key)
    if not raw:
        return None
    try:
        return pd.read_csv(io.StringIO(raw), dtype=str).fillna("")
    except Exception:
        return None


def _save_local_state() -> None:
    instruments = st.session_state.get("ilm_instruments")
    events = st.session_state.get("ilm_events")

    if isinstance(instruments, pd.DataFrame):
        _set_value("instruments_csv", instruments.to_csv(index=False))
    if isinstance(events, pd.DataFrame):
        _set_value("events_csv", events.to_csv(index=False))

    brief = st.session_state.get("ilm_last_brief")
    if isinstance(brief, str):
        _set_value("last_brief", brief)

    result = st.session_state.get("ilm_last_result")
    if isinstance(result, dict):
        _set_value("last_result_json", json.dumps(result, ensure_ascii=False))


def _save_remote_state() -> bool:
    if not _remote_configured():
        return False
    instruments = st.session_state.get("ilm_instruments")
    events = st.session_state.get("ilm_events")
    result = st.session_state.get("ilm_last_result")
    payload = {
        "action": "save",
        "instruments": instruments.fillna("").astype(str).to_dict(orient="records") if isinstance(instruments, pd.DataFrame) else [],
        "events": events.fillna("").astype(str).to_dict(orient="records") if isinstance(events, pd.DataFrame) else [],
        "last_brief": st.session_state.get("ilm_last_brief", "") if isinstance(st.session_state.get("ilm_last_brief", ""), str) else "",
        "last_result": result if isinstance(result, dict) else {},
    }
    response = _remote_request(payload)
    ok = bool(response and response.get("ok"))
    st.session_state["_ilm_remote_last_save_ok"] = ok
    return ok


def _save_state() -> None:
    _save_local_state()
    _save_remote_state()


def _restore_local_state() -> None:
    if "ilm_instruments" not in st.session_state:
        instruments = _load_df("instruments_csv")
        if instruments is not None:
            st.session_state.ilm_instruments = instruments

    if "ilm_events" not in st.session_state:
        events = _load_df("events_csv")
        if events is not None:
            st.session_state.ilm_events = events

    if "ilm_last_brief" not in st.session_state:
        brief = _get_value("last_brief")
        if brief:
            st.session_state.ilm_last_brief = brief

    if "ilm_last_result" not in st.session_state:
        raw = _get_value("last_result_json")
        if raw:
            try:
                parsed = json.loads(raw)
                if isinstance(parsed, dict):
                    st.session_state.ilm_last_result = parsed
            except Exception:
                pass


def _restore_remote_state() -> bool:
    if not _remote_configured() or st.session_state.get("_ilm_remote_loaded"):
        return False
    response = _remote_request({"action": "load"})
    st.session_state["_ilm_remote_loaded"] = True
    if not response or not response.get("ok"):
        st.session_state["_ilm_remote_load_ok"] = False
        return False

    instruments = response.get("instruments")
    events = response.get("events")
    if isinstance(instruments, list):
        st.session_state.ilm_instruments = pd.DataFrame(instruments).fillna("")
    if isinstance(events, list):
        st.session_state.ilm_events = pd.DataFrame(events).fillna("")

    brief = response.get("last_brief")
    if isinstance(brief, str) and brief:
        st.session_state.ilm_last_brief = brief
    result = response.get("last_result")
    if isinstance(result, dict) and result:
        st.session_state.ilm_last_result = result

    st.session_state["_ilm_remote_load_ok"] = True
    _save_local_state()
    return True


_init_store()
_restore_local_state()
_restore_remote_state()

# The lifecycle app calls st.rerun() immediately after writes. Persist first so
# those changes survive browser refreshes and, when configured, server restarts.
_original_rerun = st.rerun


def _persistent_rerun(*args, **kwargs):
    _save_state()
    return _original_rerun(*args, **kwargs)


st.rerun = _persistent_rerun

try:
    from instrument_lifecycle_app import *  # noqa: F401,F403
finally:
    _save_state()

# Mobile-first spacing fix: Streamlit's fixed app toolbar can cover the top of
# the hero card on small screens. This late CSS override applies globally to the
# already-rendered page and keeps the tab strip horizontally scrollable.
st.markdown(
    """
    <style>
      .block-container {
        padding-top: 4.8rem !important;
      }
      div[data-baseweb="tab-list"] {
        overflow-x: auto !important;
        flex-wrap: nowrap !important;
        scrollbar-width: none;
      }
      div[data-baseweb="tab-list"]::-webkit-scrollbar { display: none; }
      button[data-baseweb="tab"] { white-space: nowrap !important; flex: 0 0 auto !important; }
      @media (max-width: 700px) {
        .block-container {
          padding-top: 6.2rem !important;
          padding-left: 1rem !important;
          padding-right: 1rem !important;
        }
      }
    </style>
    """,
    unsafe_allow_html=True,
)

if _remote_configured():
    if st.session_state.get("_ilm_remote_load_ok") is False or st.session_state.get("_ilm_remote_last_save_ok") is False:
        st.caption("⚠️ Durable storage is configured but the last Google Sheets sync did not complete. Local fallback is active.")
    else:
        st.caption("☁️ Durable storage: Google Sheets sync enabled")
else:
    st.caption("💾 Storage mode: local prototype cache. Configure durable storage before relying on data across reboot/redeploy.")

# Standalone Streamlit entrypoint for the Instrument Lifecycle application.
# This branch is intentionally isolated from the main HPLC / Decision Gap app.
# v0.1.1 adds lightweight local SQLite persistence so browser refreshes do not
# erase prototype data during the lifetime of the current Streamlit instance.

from __future__ import annotations

import io
import json
import sqlite3
from pathlib import Path

import pandas as pd
import streamlit as st

DB_PATH = Path("/tmp/yahia_qc_instrument_lifecycle.sqlite3")


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


def _save_state() -> None:
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


def _restore_state() -> None:
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


_init_store()
_restore_state()

# The lifecycle app calls st.rerun() immediately after writes. Persist first so
# those changes survive the rerun and a browser refresh.
_original_rerun = st.rerun


def _persistent_rerun(*args, **kwargs):
    _save_state()
    return _original_rerun(*args, **kwargs)


st.rerun = _persistent_rerun

try:
    from instrument_lifecycle_app import *  # noqa: F401,F403
finally:
    _save_state()

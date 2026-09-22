from pathlib import Path

path = Path("instrument_supabase_app.py")
text = path.read_text(encoding="utf-8")
marker = "_ILM_APP_SHELL_BOOTSTRAPPED"
if marker in text:
    print("Shell bootstrap already present.")
    raise SystemExit(0)

anchor = "from __future__ import annotations\n"
if anchor not in text:
    raise SystemExit("Could not find future-import anchor; refusing blind edit.")

bootstrap = '''from __future__ import annotations\n\n# _ILM_APP_SHELL_BOOTSTRAPPED\n# Compatibility bootstrap: if Streamlit Cloud still points directly to this\n# legacy core file, hand execution to app.py so the current application shell,\n# workspace navigation, admin controls and premium Product/User Guide are used.\nif __name__ == "__main__" and not globals().get("_ILM_APP_SHELL_BOOTSTRAPPED"):\n    globals()["_ILM_APP_SHELL_BOOTSTRAPPED"] = True\n    from pathlib import Path as _ILMBootstrapPath\n    import streamlit as _ilm_bootstrap_st\n    _ilm_shell = _ILMBootstrapPath(__file__).resolve().with_name("app.py")\n    exec(compile(_ilm_shell.read_text(encoding="utf-8"), str(_ilm_shell), "exec"), globals(), globals())\n    _ilm_bootstrap_st.stop()\n'''

path.write_text(text.replace(anchor, bootstrap, 1), encoding="utf-8")
print("Legacy entrypoint now delegates to app.py when run directly.")

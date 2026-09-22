"""Compatibility redirect for Streamlit deployments still configured to the legacy core file.

Python imports usercustomize during interpreter startup. Streamlit parses the target
script path afterwards, so replacing only the legacy instrument entrypoint here lets
existing deployments start the guarded application shell without changing the
Streamlit Cloud setting.
"""

from __future__ import annotations

import sys
from pathlib import Path


def _redirect_legacy_streamlit_entrypoint() -> None:
    for idx, raw in enumerate(list(sys.argv)):
        try:
            arg = str(raw or "")
            if not arg.endswith("instrument_supabase_app.py"):
                continue
            current = Path(arg)
            candidate = current.with_name("safe_app.py")
            if not candidate.exists():
                candidate = Path.cwd() / "safe_app.py"
            if candidate.exists():
                sys.argv[idx] = str(candidate)
            return
        except Exception:
            return


_redirect_legacy_streamlit_entrypoint()

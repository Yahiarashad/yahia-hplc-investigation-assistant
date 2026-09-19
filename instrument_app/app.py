from pathlib import Path

# This standalone entrypoint intentionally lives in its own directory so Streamlit
# does not auto-discover the root-level pages/ directory used by the original app.
# Keep the source implementation in sync with ../instrument_lifecycle_app.py.

source = Path(__file__).resolve().parent.parent / "instrument_lifecycle_app.py"
exec(compile(source.read_text(encoding="utf-8"), str(source), "exec"), globals(), globals())

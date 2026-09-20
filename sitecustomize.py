"""Application-wide startup customizations for Yahia QC Instrument Lifecycle.

1) Keep Streamlit expanders collapsed until the user opens them.
2) Pre-register a premium Arabic PDF typography stack using system-installed
   Noto fonts. No font files are bundled with or exposed by the application.
"""

from pathlib import Path


# ---------------------------------------------------------------------------
# Streamlit interaction default: all expanders start collapsed.
# ---------------------------------------------------------------------------
try:
    import streamlit as st

    _ilm_native_expander_default = st.expander

    def _ilm_collapsed_expander(label, *args, **kwargs):
        # Product decision: every accordion/expander starts closed.
        # Explicit expanded=True in older modules is intentionally overridden.
        kwargs["expanded"] = False
        return _ilm_native_expander_default(label, *args, **kwargs)

    st.expander = _ilm_collapsed_expander
except Exception:
    # Never block application startup if Streamlit is unavailable during
    # interpreter bootstrap.
    pass


# ---------------------------------------------------------------------------
# Arabic PDF typography.
#
# Streamlit Cloud installs fonts-noto-core from packages.txt. We intentionally
# use two complementary Arabic faces:
#   • Noto Naskh Arabic Regular for readable body text and long evidence notes.
#   • Noto Kufi Arabic Bold for headings, table labels and management metrics.
#
# The PDF modules historically register their own aliases (ILM/ILMB and
# EXECV2REG/EXECV2BOLD). We pre-register those aliases here and protect only
# those names from being overwritten later by a DejaVu fallback.
# ---------------------------------------------------------------------------
try:
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont

    def _find_font(filename: str):
        roots = [
            Path("/usr/share/fonts/truetype/noto"),
            Path("/usr/share/fonts/opentype/noto"),
            Path("/usr/share/fonts"),
        ]
        for root in roots:
            try:
                direct = root / filename
                if direct.exists():
                    return direct
                if root.exists():
                    for match in root.rglob(filename):
                        if match.exists():
                            return match
            except Exception:
                continue
        return None

    # Preferred premium stack.
    _naskh_regular = _find_font("NotoNaskhArabic-Regular.ttf")
    _kufi_bold = _find_font("NotoKufiArabic-Bold.ttf")

    # Graceful fallbacks if a distro ships a slightly different Noto subset.
    if _naskh_regular is None:
        _naskh_regular = _find_font("NotoSansArabic-Regular.ttf")
    if _kufi_bold is None:
        _kufi_bold = _find_font("NotoSansArabic-Bold.ttf")

    _protected_aliases = {"ILM", "ILMB", "EXECV2REG", "EXECV2BOLD"}

    if _naskh_regular is not None and _kufi_bold is not None:
        _native_register_font = pdfmetrics.registerFont

        # Lifecycle Evidence PDF aliases.
        if "ILM" not in pdfmetrics.getRegisteredFontNames():
            _native_register_font(TTFont("ILM", str(_naskh_regular)))
        if "ILMB" not in pdfmetrics.getRegisteredFontNames():
            _native_register_font(TTFont("ILMB", str(_kufi_bold)))

        # Executive Performance PDF aliases.
        if "EXECV2REG" not in pdfmetrics.getRegisteredFontNames():
            _native_register_font(TTFont("EXECV2REG", str(_naskh_regular)))
        if "EXECV2BOLD" not in pdfmetrics.getRegisteredFontNames():
            _native_register_font(TTFont("EXECV2BOLD", str(_kufi_bold)))

        def _ilm_register_font_once(font):
            """Protect our Arabic aliases; preserve normal ReportLab behavior."""
            try:
                name = str(getattr(font, "fontName", "") or "")
                if name in _protected_aliases and name in pdfmetrics.getRegisteredFontNames():
                    return None
            except Exception:
                pass
            return _native_register_font(font)

        pdfmetrics.registerFont = _ilm_register_font_once
except Exception:
    # PDF generation must still work with the existing fallback fonts if the
    # Noto package is temporarily unavailable during a deployment.
    pass

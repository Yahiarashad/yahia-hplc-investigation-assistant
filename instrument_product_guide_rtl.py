"""RTL-safe adapter for the premium product guide PDF.

ReportLab in the deployed stack does not provide native bidi layout. The base
product guide previously reshaped + bidi-reversed an entire Arabic paragraph
before ReportLab wrapped it. That makes wrapped Arabic lines appear reversed.

This adapter keeps Arabic in logical word order for line layout, shapes each
word independently, and draws each line from right to left. It patches only the
premium product guide PDF and does not affect technical tables or other reports.
"""

from __future__ import annotations

import instrument_product_guide as _pg

try:
    from reportlab.pdfbase import pdfmetrics
    from reportlab.platypus import Flowable
except Exception:
    pdfmetrics = None
    Flowable = object


class _RTLArabicFlowable(Flowable):
    """Small ReportLab flowable that wraps logical Arabic words RTL correctly."""

    def __init__(self, text, style):
        super().__init__()
        self.text = str(text or "")
        self.style = style
        self._lines = []
        self._avail_width = 0
        self._space_width = 0

    def getSpaceBefore(self):
        return float(getattr(self.style, "spaceBefore", 0) or 0)

    def getSpaceAfter(self):
        return float(getattr(self.style, "spaceAfter", 0) or 0)

    def _display_word(self, word: str) -> str:
        # Apply shaping/bidi to one token only. Word order is handled by the
        # layout engine below, so paragraph wrapping can never reverse lines.
        if _pg._contains_arabic(word):
            return _pg._shape_arabic(word)
        return word

    def wrap(self, availWidth, availHeight):
        if pdfmetrics is None:
            return availWidth, 0

        font_name = self.style.fontName
        font_size = float(self.style.fontSize)
        leading = float(self.style.leading or (font_size * 1.5))
        self._avail_width = float(availWidth)
        self._space_width = pdfmetrics.stringWidth(" ", font_name, font_size)
        lines = []

        logical_paragraphs = self.text.splitlines() or [""]
        for p_index, paragraph in enumerate(logical_paragraphs):
            words = paragraph.split()
            if not words:
                lines.append([])
                continue

            current = []
            current_width = 0.0
            for logical_word in words:
                visual_word = self._display_word(logical_word)
                word_width = pdfmetrics.stringWidth(visual_word, font_name, font_size)
                extra = word_width if not current else self._space_width + word_width
                if current and current_width + extra > self._avail_width:
                    lines.append(current)
                    current = [(visual_word, word_width)]
                    current_width = word_width
                else:
                    current.append((visual_word, word_width))
                    current_width += extra
            if current:
                lines.append(current)
            if p_index < len(logical_paragraphs) - 1:
                lines.append([])

        self._lines = lines or [[]]
        self.width = self._avail_width
        self.height = max(leading, len(self._lines) * leading)
        return self.width, self.height

    def draw(self):
        if pdfmetrics is None:
            return

        canvas = self.canv
        font_name = self.style.fontName
        font_size = float(self.style.fontSize)
        leading = float(self.style.leading or (font_size * 1.5))
        canvas.saveState()
        canvas.setFont(font_name, font_size)
        if getattr(self.style, "textColor", None) is not None:
            canvas.setFillColor(self.style.textColor)

        # Baseline correction keeps the visual rhythm close to Paragraph.
        y = self.height - leading + max(0.0, (leading - font_size) * 0.35)
        for line in self._lines:
            x = self._avail_width
            for visual_word, word_width in line:
                x -= word_width
                canvas.drawString(x, y, visual_word)
                x -= self._space_width
            y -= leading
        canvas.restoreState()


def _rtl_ar(text: str, style):
    if pdfmetrics is None:
        return _pg._ar(text, style)
    return _RTLArabicFlowable(text, style)


# Patch the base module so every Arabic paragraph in the brochure uses the
# corrected RTL layout while all existing English/product content stays intact.
_pg._ar = _rtl_ar

# A fresh deployment starts with an empty cache. Clear defensively in case this
# module is hot-reloaded inside an existing Streamlit process.
try:
    _pg.build_product_user_guide_pdf.clear()
except Exception:
    pass


build_product_user_guide_pdf = _pg.build_product_user_guide_pdf
render_product_guide_hub = _pg.render_product_guide_hub

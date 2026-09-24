from __future__ import annotations

import base64

_GUIDE_VISUALS = {
    "instrument_360_overview": "__OVERVIEW__",
    "instrument_360_attention": "__ATTENTION__",
}

def guide_visual_bytes(name: str) -> bytes:
    value = _GUIDE_VISUALS.get(name, "")
    return base64.b64decode(value) if value else b""

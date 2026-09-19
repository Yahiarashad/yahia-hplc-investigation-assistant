# Camera-assisted instrument nameplate capture for Yahia QC Instrument Lifecycle.
# Loaded by app.py before the core Instrument Passport is rendered.

from __future__ import annotations

import base64
import json
import re

import streamlit as st

try:
    from openai import OpenAI
except Exception:
    OpenAI = None


_CAMERA_FIELDS = {
    "manufacturer": "Manufacturer",
    "model": "Model",
    "serial_number": "Serial number",
    "instrument_name": "Instrument name *",
    "instrument_code": "Instrument ID *",
}

_CAMERA_TYPE_OPTIONS = [
    "HPLC", "UHPLC", "GC", "LC-MS", "LC-MS/MS", "UV-Vis", "Dissolution",
    "Balance", "pH Meter", "Viscometer", "Other",
]


def _camera_secret(name: str) -> str:
    try:
        return str(st.secrets.get(name, "") or "").strip()
    except Exception:
        return ""


def _clean_json_text(text: str) -> str:
    raw = str(text or "").strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json)?\s*", "", raw, flags=re.I)
        raw = re.sub(r"\s*```$", "", raw)
    start = raw.find("{")
    end = raw.rfind("}")
    return raw[start:end + 1] if start >= 0 and end > start else raw


def _extract_nameplate(image_bytes: bytes, mime_type: str = "image/jpeg"):
    api_key = _camera_secret("OPENAI_API_KEY")
    if not api_key:
        return None, "OPENAI_API_KEY is not configured in this Streamlit app."
    if OpenAI is None:
        return None, "OpenAI client library is not available."

    model = _camera_secret("INSTRUMENT_LABEL_MODEL") or "gpt-5.6-terra"
    data_url = f"data:{mime_type or 'image/jpeg'};base64,{base64.b64encode(image_bytes).decode('ascii')}"
    prompt = """
You are reading a pharmaceutical laboratory instrument nameplate / identification label.
Extract ONLY values that are clearly visible in the image. Never infer, expand, correct, or guess missing characters.
Return one JSON object with exactly these keys:
{
  "manufacturer": null,
  "model": null,
  "serial_number": null,
  "instrument_name": null,
  "instrument_type": null,
  "instrument_code": null,
  "confidence_note": ""
}
Rules:
- manufacturer: brand/manufacturer printed on the label.
- model: exact model designation as printed.
- serial_number: exact S/N, Serial No., Serial Number or equivalent. Preserve letters, dashes, slashes and leading zeroes.
- instrument_name: concise equipment/product name only if printed or unambiguous from the label itself.
- instrument_type: only one of HPLC, UHPLC, GC, LC-MS, LC-MS/MS, UV-Vis, Dissolution, Balance, pH Meter, Viscometer, Other, or null.
- instrument_code: only if an internal Asset ID / Equipment ID / Instrument ID is clearly printed. Do not use the serial number as instrument_code.
- If any character is unclear, return null for that field rather than guessing.
- confidence_note: one short sentence listing any field that should be manually checked.
Return JSON only.
""".strip()
    try:
        client = OpenAI(api_key=api_key)
        response = client.responses.create(
            model=model,
            input=[{
                "role": "user",
                "content": [
                    {"type": "input_text", "text": prompt},
                    {"type": "input_image", "image_url": data_url},
                ],
            }],
        )
        text = getattr(response, "output_text", "") or ""
        data = json.loads(_clean_json_text(text))
        if not isinstance(data, dict):
            return None, "The label reader did not return structured data."
        cleaned = {}
        for key in ("manufacturer", "model", "serial_number", "instrument_name", "instrument_type", "instrument_code", "confidence_note"):
            value = data.get(key)
            cleaned[key] = str(value).strip() if value not in (None, "", "null") else None
        if cleaned.get("instrument_type") not in _CAMERA_TYPE_OPTIONS:
            cleaned["instrument_type"] = None
        return cleaned, ""
    except Exception as exc:
        code = getattr(exc, "code", None) or exc.__class__.__name__
        return None, f"Label extraction could not complete ({code})."


def _render_camera_scanner():
    st.markdown("#### 📷 Scan instrument nameplate — optional")
    st.caption(
        "Use the camera to reduce transcription mistakes in Manufacturer, Model and Serial number. "
        "Nothing is saved automatically — always review the extracted values before creating the Passport."
    )
    source = st.radio(
        "Label image source",
        ["📷 Camera", "🖼️ Upload photo"],
        horizontal=True,
        key="ilm_label_source",
    )
    if source.startswith("📷"):
        image = st.camera_input(
            "Take a clear photo of the instrument nameplate / S/N label",
            key="ilm_instrument_nameplate_camera",
            help="Fill the frame with the label. Avoid glare and keep S/N and Model sharply focused.",
        )
    else:
        image = st.file_uploader(
            "Upload a clear nameplate photo",
            type=["jpg", "jpeg", "png", "webp"],
            key="ilm_instrument_nameplate_upload",
        )

    if not image:
        st.info("Tip: photograph the manufacturer's identification plate, not the front panel display.")
        return

    st.image(image, caption="Nameplate image — verify it is readable before extraction", use_container_width=True)
    consent = st.checkbox(
        "Analyze this image to extract the printed label data. The photo is used for extraction and is not saved in the instrument database.",
        key="ilm_label_ai_consent",
    )
    if st.button(
        "✨ Extract Manufacturer · Model · S/N",
        use_container_width=True,
        disabled=not consent,
        key="ilm_extract_nameplate",
    ):
        with st.spinner("Reading the printed nameplate without guessing…"):
            result, err = _extract_nameplate(image.getvalue(), getattr(image, "type", "image/jpeg"))
        if err:
            st.error(err)
            return
        st.session_state.ilm_camera_prefill = result or {}
        st.success("Label read. The suggested values are prefilled below — review them before saving.")

    result = st.session_state.get("ilm_camera_prefill") or {}
    if result:
        preview = {
            "Manufacturer": result.get("manufacturer") or "—",
            "Model": result.get("model") or "—",
            "Serial number": result.get("serial_number") or "—",
            "Instrument name": result.get("instrument_name") or "—",
            "Instrument type": result.get("instrument_type") or "—",
            "Instrument ID": result.get("instrument_code") or "—",
        }
        st.dataframe([preview], use_container_width=True, hide_index=True)
        if result.get("confidence_note"):
            st.warning("Manual check: " + result["confidence_note"])
        if st.button("Clear scanned suggestions", use_container_width=True, key="ilm_clear_camera_prefill"):
            st.session_state.pop("ilm_camera_prefill", None)
            st.rerun()


# Monkeypatch only the existing Add Instrument form. This keeps the core app
# stable while placing the scanner exactly inside the Add new instrument expander.
_real_form = st.form
_real_text_input = st.text_input
_real_selectbox = st.selectbox
_CAMERA_FORM_ACTIVE = False


class _CameraFormProxy:
    def __init__(self, inner):
        self.inner = inner

    def __enter__(self):
        global _CAMERA_FORM_ACTIVE
        _CAMERA_FORM_ACTIVE = True
        return self.inner.__enter__()

    def __exit__(self, exc_type, exc, tb):
        global _CAMERA_FORM_ACTIVE
        try:
            return self.inner.__exit__(exc_type, exc, tb)
        finally:
            _CAMERA_FORM_ACTIVE = False


def _camera_form(form_key, *args, **kwargs):
    if str(form_key) == "add_instrument":
        _render_camera_scanner()
        return _CameraFormProxy(_real_form(form_key, *args, **kwargs))
    return _real_form(form_key, *args, **kwargs)


def _camera_text_input(label, *args, **kwargs):
    if _CAMERA_FORM_ACTIVE:
        prefill = st.session_state.get("ilm_camera_prefill") or {}
        label_text = str(label)
        lookup = {
            "Manufacturer": "manufacturer",
            "Model": "model",
            "Serial number": "serial_number",
            "Instrument name *": "instrument_name",
            "Instrument ID *": "instrument_code",
        }
        field = lookup.get(label_text)
        suggested = prefill.get(field) if field else None
        if suggested and "value" not in kwargs:
            kwargs["value"] = str(suggested)
    return _real_text_input(label, *args, **kwargs)


def _camera_selectbox(label, options, *args, **kwargs):
    option_list = list(options)
    if _CAMERA_FORM_ACTIVE and str(label) == "Type":
        # Keep Viscometer available in the Passport even though the legacy core
        # list predates this instrument type.
        if "Viscometer" not in option_list:
            if "Other" in option_list:
                option_list.insert(option_list.index("Other"), "Viscometer")
            else:
                option_list.append("Viscometer")
        prefill = st.session_state.get("ilm_camera_prefill") or {}
        suggested = prefill.get("instrument_type")
        if suggested in option_list and "index" not in kwargs:
            kwargs["index"] = option_list.index(suggested)
        return _real_selectbox(label, option_list, *args, **kwargs)
    return _real_selectbox(label, options, *args, **kwargs)


st.form = _camera_form
st.text_input = _camera_text_input
st.selectbox = _camera_selectbox

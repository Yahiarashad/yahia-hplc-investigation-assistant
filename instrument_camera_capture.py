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
        for key in (
            "manufacturer", "model", "serial_number", "instrument_name",
            "instrument_type", "instrument_code", "confidence_note",
        ):
            value = data.get(key)
            cleaned[key] = str(value).strip() if value not in (None, "", "null") else None
        if cleaned.get("instrument_type") not in _CAMERA_TYPE_OPTIONS:
            cleaned["instrument_type"] = None
        return cleaned, ""
    except Exception as exc:
        code = getattr(exc, "code", None) or exc.__class__.__name__
        return None, f"Label extraction could not complete ({code})."


# IMPORTANT: Streamlit reruns the script without recreating the imported `st`
# module. The previous implementation captured an already-patched st.form on the
# next rerun, causing the camera wrapper to wrap itself again. That rendered the
# same radio/camera widgets twice and raised StreamlitDuplicateElementKey.
# Store the native Streamlit callables once on the module itself, then always
# wrap those originals. This makes the patch idempotent across refresh/reboot.
if not hasattr(st, "_ilm_native_form"):
    st._ilm_native_form = st.form
if not hasattr(st, "_ilm_native_text_input"):
    st._ilm_native_text_input = st.text_input
if not hasattr(st, "_ilm_native_selectbox"):
    st._ilm_native_selectbox = st.selectbox

_real_form = st._ilm_native_form
_real_text_input = st._ilm_native_text_input
_real_selectbox = st._ilm_native_selectbox
_CAMERA_FORM_ACTIVE = False
_CAMERA_SCANNER_RENDERED = False


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
    global _CAMERA_SCANNER_RENDERED
    if str(form_key) == "add_instrument":
        # One scanner per script run. If the core ever references the Add form
        # more than once, do not duplicate keyed camera widgets.
        if not _CAMERA_SCANNER_RENDERED:
            _render_camera_scanner()
            _CAMERA_SCANNER_RENDERED = True
        return _CameraFormProxy(_real_form(form_key, *args, **kwargs))
    return _real_form(form_key, *args, **kwargs)


def _camera_text_input(label, *args, **kwargs):
    if _CAMERA_FORM_ACTIVE:
        prefill = st.session_state.get("ilm_camera_prefill") or {}
        lookup = {
            "Manufacturer": "manufacturer",
            "Model": "model",
            "Serial number": "serial_number",
            "Instrument name *": "instrument_name",
            "Instrument ID *": "instrument_code",
        }
        field = lookup.get(str(label))
        suggested = prefill.get(field) if field else None
        if suggested and "value" not in kwargs:
            kwargs["value"] = str(suggested)
    return _real_text_input(label, *args, **kwargs)


def _camera_selectbox(label, options, *args, **kwargs):
    option_list = list(options)
    if _CAMERA_FORM_ACTIVE and str(label) == "Type":
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


# Re-assign on every script run, but always delegate to the saved native methods.
st.form = _camera_form
st.text_input = _camera_text_input
st.selectbox = _camera_selectbox


# Extend the practical guide with the Excel-vs-app value proposition and a
# dedicated founding-user feedback step. The base guide itself is defined in
# instrument_v03_user_guide.py immediately before this module is executed.
_existing_user_guide = globals().get("render_v03_user_guide")
if callable(_existing_user_guide):
    def render_v03_user_guide():
        _existing_user_guide()
        with st.expander("⭐ عندي Excel Tracker بالفعل — لماذا أستخدم التطبيق؟", expanded=False):
            st.markdown(
                """
### Excel يحفظ البيانات. التطبيق يحوّل تاريخ الجهاز إلى قرار.

لو عندك Excel Tracker جيد، **لا تبدأ من الصفر ولا تتخلص منه**. استخدمه كمدخل للتطبيق، ثم دع التطبيق يضيف طبقة المتابعة والقرار.

- **Next Action وليس مجرد Row** — Current Stage، Missing Evidence، Next Controlled Milestone وما يحتاج متابعة الآن.
- **Lifecycle واحدة مترابطة** — Need → URS → Quotation → PR → PO → Receiving → Installation → IQ/OQ/PQ → Release → First Run → Routine Control → Performance Review → Retirement.
- **Priority Attention Queue** — يجمع Calibration/PM overdue، OOC، Open Events، Receiving delays والمراحل الناقصة حسب الأولوية.
- **Instrument Memory** — الصيانة والمعايرة والمكونات والأعطال والتحقيقات مرتبطة بنفس الجهاز وتاريخه.
- **Investigation Intelligence** — يفصل Observed / Inferred / Unknown ويقترح Next Evidence Action بدل trial-and-error.
- **Camera-assisted entry** — يقلل أخطاء نقل Manufacturer / Model / S/N مع مراجعة المستخدم قبل الحفظ.
- **Multi-user isolation** — كل حساب يرى بياناته فقط عبر Supabase Row Level Security.

#### أفضل Workflow
**Existing Excel Tracker → Import → Lifecycle Intelligence → Priorities / Decisions → Investigation Memory / Reports**

يمكن رفع Excel، لكن التطبيق يتعرف **فقط على الأعمدة التي تحمل نفس اسم الحقل داخل التطبيق**. أي اسم مختلف لا يتم تخمينه أو ربطه تلقائيًا. الأفضل فتح **MY INSTRUMENTS → Instruments → Import Instrument List** ثم تنزيل Template التطبيق من هناك أو توحيد أسماء الأعمدة معه.

> **Excel tracks instruments. Yahia QC Instrument Lifecycle helps you decide what needs attention next — and why.**
"""
            )
            st.info(
                "لأعلى استفادة: لا تستخدم التطبيق فقط وقت المشكلة. حافظ على Passport وLifecycle وCalibration/PM وComponents وEvents محدثة؛ جودة القرار تعتمد على جودة التاريخ المسجل."
            )

        try:
            from instrument_feedback import render_instrument_feedback
            render_instrument_feedback(compact=True)
        except Exception as exc:
            st.caption(f"Feedback module is temporarily unavailable ({type(exc).__name__}).")

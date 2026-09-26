from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app.py"
PROMPT = ROOT / "core_prompt.txt"
REQ = ROOT / "requirements.txt"


def replace_once(text, old, new, label):
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected exactly 1 match, found {count}")
    return text.replace(old, new, 1)


def regex_replace_once(text, pattern, replacement, label, flags=0):
    new_text, count = re.subn(pattern, replacement, text, count=1, flags=flags)
    if count != 1:
        raise RuntimeError(f"{label}: expected exactly 1 regex match, found {count}")
    return new_text


app = APP.read_text(encoding="utf-8")

app = replace_once(
    app,
    "from evidence_engine import format_evidence_context, retrieve_evidence\nfrom portrait_asset import PORTRAIT_B64",
    "from evidence_engine import format_evidence_context, retrieve_evidence\nfrom investigation_report import build_investigation_pdf\nfrom portrait_asset import PORTRAIT_B64",
    "investigation_report import",
)
app = replace_once(app, 'APP_VERSION = "v1.1"', 'APP_VERSION = "v1.2"', "app version")

app = regex_replace_once(
    app,
    r"def _conclusion_detected\(messages\):\n.*?\n(?=def _last_assistant_answer)",
    '''def _conclusion_detected(messages):
    return _investigation_status(messages) in ("PROBABLE", "CONFIRMED")


''',
    "conclusion detector",
    flags=re.S,
)

helper_block = '''def _evidence_stage_from_answer(answer):
    match = re.search(
        r"EVIDENCE_STAGE\\s*:\\s*(OBSERVED|HYPOTHESIS|LOCALIZED|IMMEDIATE_CAUSE_CONFIRMED|ROOT_CAUSE_PROBABLE|ROOT_CAUSE_CONFIRMED)",
        answer or "",
        re.I,
    )
    return match.group(1).upper() if match else "OBSERVED"


def _evidence_stage(messages):
    return _evidence_stage_from_answer(_last_assistant_answer(messages))


def _response_sections(answer):
    raw = answer or ""
    what_match = re.search(r"(?im)^\\s*WHAT_NEXT\\s*:\\s*(.*)$", raw)
    turn_match = re.search(r"(?im)^\\s*YOUR_TURN\\s*:\\s*(.*)$", raw)
    what_next = what_match.group(1).strip() if what_match else ""
    your_turn = turn_match.group(1).strip() if turn_match else ""

    clean = re.sub(
        r"(?im)^\\s*(?:INVESTIGATION_STATUS|EVIDENCE_STAGE)\\s*:\\s*[^\\n]+\\s*$",
        "",
        raw,
    )
    clean = re.sub(r"(?im)^\\s*(?:WHAT_NEXT|YOUR_TURN)\\s*:\\s*[^\\n]*\\s*$", "", clean)
    clean = re.sub(r"(?im)^\\s*EXPLANATION\\s*:\\s*$", "", clean)
    explanation = re.sub(r"\\n{3,}", "\\n\\n", clean).strip()
    return {
        "what_next": what_next,
        "your_turn": your_turn,
        "explanation": explanation,
    }


def _is_none_value(value):
    return (value or "").strip().casefold() in {"", "none", "n/a", "not applicable", "لا يوجد", "لا شيء"}


def _render_assistant_turn(answer, is_ar):
    sections = _response_sections(answer)
    stage = _evidence_stage_from_answer(answer)
    what_next = sections["what_next"]
    explanation = sections["explanation"]

    stage_label = stage.replace("_", " ")
    st.caption(("مرحلة الدليل: " if is_ar else "Evidence stage: ") + stage_label)

    if not _is_none_value(what_next):
        st.markdown("### 🎯 المطلوب التالي" if is_ar else "### 🎯 What next?")
        st.markdown(what_next)
    elif stage in {"ROOT_CAUSE_PROBABLE", "ROOT_CAUSE_CONFIRMED"}:
        st.markdown("### ✅ الخلاصة الحالية" if is_ar else "### ✅ Current conclusion")

    if explanation:
        expander_label = (
            "لماذا هذه الخطوة؟ · الأدلة والتفسير"
            if is_ar
            else "Why this step? · Evidence & explanation"
        )
        with st.expander(expander_label, expanded=False):
            st.markdown(explanation)


def _turn_prompt(messages, is_ar):
    status = _investigation_status(messages)
    sections = _response_sections(_last_assistant_answer(messages))
    requested = sections["your_turn"]

    if is_ar:
        if status == "AWAITING_TEST":
            title = "دورك الآن — نفّذ الفحص المطلوب"
            fallback = "نفّذ الفحص المحدد أعلاه واكتب النتيجة كما لاحظتها، من غير افتراض للسبب."
        elif status == "AWAITING_USER":
            title = "دورك الآن — جاوب على السؤال أعلاه"
            fallback = "اكتب المعلومة المطلوبة أعلاه حتى نحدد الخطوة التالية."
        else:
            title = "دورك الآن — كمّل التحقيق"
            fallback = "اكتب المعلومة أو النتيجة المطلوبة أعلاه لمواصلة التحقيق."
    else:
        if status == "AWAITING_TEST":
            title = "Your turn — run the requested check"
            fallback = "Perform the check above and report exactly what you observed, without assuming the cause."
        elif status == "AWAITING_USER":
            title = "Your turn — answer the question above"
            fallback = "Provide the requested information so the investigation can choose the next step."
        else:
            title = "Your turn — continue the investigation"
            fallback = "Provide the requested information or result above to continue the investigation."

    return title, (fallback if _is_none_value(requested) else requested)


'''
app = replace_once(
    app,
    '''def _display_answer(answer):
    return re.sub(
        r"\\n?INVESTIGATION_STATUS\\s*:\\s*(?:INVESTIGATING|AWAITING_USER|AWAITING_TEST|PROBABLE|CONFIRMED)\\s*$",
        "",
        answer or "",
        flags=re.I,
    ).strip()
''',
    helper_block + '''def _display_answer(answer):
    return _response_sections(answer)["explanation"]
''',
    "response parser helpers",
)

old_history = '''else:
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(_display_answer(message["content"]))
    continue_class = "continue-card continue-card-ar" if is_ar else "continue-card"
    st.markdown(
        f'<div class="{continue_class}"><strong>{T["your_turn"]}</strong>{T["your_turn_copy"]}</div>',
        unsafe_allow_html=True,
    )
    privacy_notice = (
        "⚠️ لا تضع أي معلومات حساسة أو سرية تخص الشركة، المنتج، المريض، الطريقة التحليلية أو أي بيانات غير مصرح بمشاركتها. "
        "يتم حفظ ما ترسله في هذه المرحلة لأغراض مراجعة وتحسين النسخة التجريبية."
        if is_ar else
        "⚠️ Do not enter sensitive or confidential company, product, patient, analytical-method, or unauthorized information. "
        "What you submit at this stage is stored for founding-beta review and improvement."
    )
    st.warning(privacy_notice)
'''
new_history = '''else:
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            if message["role"] == "assistant":
                _render_assistant_turn(message["content"], is_ar)
            else:
                st.markdown(message["content"])
    continue_class = "continue-card continue-card-ar" if is_ar else "continue-card"
    turn_title, turn_copy = _turn_prompt(st.session_state.messages, is_ar)
    st.markdown(
        f'<div class="{continue_class}"><strong>{turn_title}</strong>{turn_copy}</div>',
        unsafe_allow_html=True,
    )
    st.caption(
        "🔒 لا تضع معلومات سرية أو بيانات غير مصرح بمشاركتها." if is_ar
        else "🔒 Do not enter confidential or unauthorized information."
    )
'''
app = replace_once(app, old_history, new_history, "compact conversation history")

old_state_contract = '''        + "STATE CONTRACT: End every reply with exactly one machine-readable line: INVESTIGATION_STATUS: INVESTIGATING, AWAITING_USER, AWAITING_TEST, PROBABLE, or CONFIRMED. Use AWAITING_USER when one answer is needed; AWAITING_TEST when one test/check result is needed; PROBABLE only when a probable root cause is supported and no further investigation step is requested; CONFIRMED only after discriminating evidence confirms the root cause and no further investigation step is requested. Never use PROBABLE or CONFIRMED in a reply that asks the user for another investigative action. Do not explain this status line.\\n\\n"
'''
new_state_contract = '''        + "UI RESPONSE CONTRACT: Every reply must contain these literal keys, each on its own line: WHAT_NEXT: <one concise action or NONE>; YOUR_TURN: <one precise thing the user should report/do next or NONE>; EXPLANATION: followed by the full evidence-based explanation. Keep WHAT_NEXT and YOUR_TURN short and mobile-first. Put reasoning summary, what we know, unknowns, hypotheses, interpretation branches, cautions, and supporting evidence under EXPLANATION so the UI can keep them collapsed by default. Use the user's language for the values, but keep the literal keys in English exactly as written.\\n"
        + "STATE CONTRACT: End every reply with exactly two machine-readable lines. First: EVIDENCE_STAGE: OBSERVED, HYPOTHESIS, LOCALIZED, IMMEDIATE_CAUSE_CONFIRMED, ROOT_CAUSE_PROBABLE, or ROOT_CAUSE_CONFIRMED. Second: INVESTIGATION_STATUS: INVESTIGATING, AWAITING_USER, AWAITING_TEST, PROBABLE, or CONFIRMED. EVIDENCE_STAGE describes scientific confidence; INVESTIGATION_STATUS describes conversation/action state. AWAITING_USER means one answer is needed. AWAITING_TEST means one test/check result is needed. PROBABLE is allowed only for a probable underlying root cause with no further investigative action requested. CONFIRMED is allowed only for an underlying root cause confirmed by targeted evidence with reasonable competing explanations materially weakened/excluded. Never call fault localization or an immediate failure mode ROOT_CAUSE_CONFIRMED. Never use PROBABLE or CONFIRMED in a reply that requests another investigative action. Do not explain either machine line.\\n\\n"
'''
app = replace_once(app, old_state_contract, new_state_contract, "v1.2 response/state contract")

app = replace_once(
    app,
    '''                if first_user_message:
                    st.rerun()
''',
    '''                # Rebuild the page after every completed assistant turn so the
                # current WHAT NEXT / YOUR TURN state appears immediately.
                st.rerun()
''',
    "rerun after every assistant turn",
)

pdf_anchor = '''    assistant_turns = _assistant_turn_count(st.session_state.messages)

    if _conclusion_detected(st.session_state.messages):
'''
pdf_block = '''    assistant_turns = _assistant_turn_count(st.session_state.messages)

    # Documentation-ready PDF snapshot. The integrity fingerprint changes if the
    # recorded case content changes, while formal GMP approval remains in the QMS.
    try:
        pdf_bytes, report_id, report_status = build_investigation_pdf(
            case_id=CASE_ID,
            app_version=APP_VERSION,
            category=_case_category(st.session_state.messages, area),
            messages=st.session_state.messages,
            status=_investigation_status(st.session_state.messages),
            evidence_stage=_evidence_stage(st.session_state.messages),
        )
        report_label = (
            f"📄 تنزيل تقرير التحقيق ({report_status})"
            if is_ar else
            f"📄 Download Investigation Report ({report_status})"
        )
        st.download_button(
            report_label,
            data=pdf_bytes,
            file_name=f"Yahia_QC_HPLC_Investigation_{CASE_ID}.pdf",
            mime="application/pdf",
            use_container_width=True,
            key=f"download_report_{CASE_ID}",
        )
        st.caption(("رقم التقرير: " if is_ar else "Report ID: ") + report_id)
    except Exception as exc:
        st.caption(
            ("تعذر تجهيز تقرير PDF حاليًا: " if is_ar else "PDF report is temporarily unavailable: ")
            + str(exc)
        )

    if _conclusion_detected(st.session_state.messages):
'''
app = replace_once(app, pdf_anchor, pdf_block, "PDF report UI")

APP.write_text(app, encoding="utf-8")

prompt = PROMPT.read_text(encoding="utf-8")
old_labels = '''ALLOWED CONCLUSION LABELS
- ROOT CAUSE CONFIRMED
- ROOT CAUSE PROBABLE — MORE CONFIRMATION NEEDED
- ROOT CAUSE NOT YET IDENTIFIED

CONFIRMATION STANDARD
A root cause is CONFIRMED only when a targeted intervention/test changes the relevant symptom in the predicted direction and reasonable competing hypotheses have been excluded or made materially less plausible.
'''
new_labels = '''EVIDENCE CONFIDENCE LADDER — V1.2
Use the highest stage that is directly supported by case-specific evidence:
1. OBSERVED — explicit user-reported/observed evidence only.
2. HYPOTHESIS — plausible explanation, not yet localized or demonstrated.
3. LOCALIZED — a discriminating test isolates the fault/restriction/location.
4. IMMEDIATE_CAUSE_CONFIRMED — the direct failure mode is demonstrated, but the underlying mechanism may remain unknown.
5. ROOT_CAUSE_PROBABLE — the underlying mechanism is materially supported but still needs confirmation.
6. ROOT_CAUSE_CONFIRMED — the underlying mechanism is confirmed by targeted evidence and reasonable competing explanations are excluded or materially weakened.

VISIBLE CONCLUSION LANGUAGE
- IMMEDIATE CAUSE CONFIRMED
- UNDERLYING ROOT CAUSE NOT YET CONFIRMED
- ROOT CAUSE PROBABLE — MORE CONFIRMATION NEEDED
- ROOT CAUSE CONFIRMED
- ROOT CAUSE NOT YET IDENTIFIED

CONFIRMATION STANDARD
Do not confuse WHERE the failure is with WHY it happened. Fault localization or a demonstrated restriction can confirm an immediate cause without confirming the underlying root cause. A ROOT CAUSE is CONFIRMED only when targeted evidence supports the underlying mechanism and reasonable competing explanations have been excluded or made materially less plausible.

COLUMN-ISOLATION EXAMPLE
If removing only the analytical column and replacing it with a union causes pressure to fall sharply, the restriction may be LOCALIZED to the analytical column and the immediate cause may be a column restriction. That evidence alone does NOT establish why the column became restricted. Particulate loading, precipitation, inlet-frit blockage, bed damage, or another internal mechanism remain hypotheses until separately supported.
'''
prompt = replace_once(prompt, old_labels, new_labels, "core prompt evidence ladder")

response_contract = '''

V1.2 UI RESPONSE CONTRACT — NON-NEGOTIABLE
The application renders each turn in a compact mobile-first decision view. Every reply must therefore contain:
WHAT_NEXT: <exactly one concise next action, or NONE if truly terminal>
YOUR_TURN: <exactly one concise thing the user should answer/report/do next, or NONE if truly terminal>
EXPLANATION:
<the full evidence-based explanation, including what is known, unknown, hypothesis direction, why the next step is discriminating, interpretation branches, and high-value cautions>
EVIDENCE_STAGE: <OBSERVED | HYPOTHESIS | LOCALIZED | IMMEDIATE_CAUSE_CONFIRMED | ROOT_CAUSE_PROBABLE | ROOT_CAUSE_CONFIRMED>
INVESTIGATION_STATUS: <INVESTIGATING | AWAITING_USER | AWAITING_TEST | PROBABLE | CONFIRMED>

Rules:
- Keep WHAT_NEXT and YOUR_TURN short enough to read immediately on a mobile screen.
- Use the user's language for the values, but keep the five literal machine keys above exactly in English.
- Put explanation/detail under EXPLANATION; the UI keeps it collapsed by default.
- If the user needs to answer one clarification, use AWAITING_USER.
- If the user needs to run/check something and return with a result, use AWAITING_TEST.
- Do not use PROBABLE or CONFIRMED while asking for more investigative evidence.
- EVIDENCE_STAGE is scientific confidence. INVESTIGATION_STATUS is interaction state. Never substitute one for the other.
'''
if "V1.2 UI RESPONSE CONTRACT — NON-NEGOTIABLE" not in prompt:
    prompt = prompt.rstrip() + response_contract + "\n"
PROMPT.write_text(prompt, encoding="utf-8")

req = REQ.read_text(encoding="utf-8")
for package in ["reportlab>=4.2.0", "arabic-reshaper>=3.0.0", "python-bidi>=0.6.0"]:
    if package.split(">=")[0].lower() not in req.lower():
        req = req.rstrip() + "\n" + package + "\n"
REQ.write_text(req, encoding="utf-8")

print("v1.2 patch applied successfully")

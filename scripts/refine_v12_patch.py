from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app.py"


def replace_once(text, old, new, label):
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected 1 match, found {count}")
    return text.replace(old, new, 1)


app = APP.read_text(encoding="utf-8")

app = replace_once(
    app,
    "import os\nimport re\nimport base64",
    "import os\nimport re\nimport html as html_lib\nimport base64",
    "safe html import",
)

app = replace_once(
    app,
    '''    continue_class = "continue-card continue-card-ar" if is_ar else "continue-card"
    turn_title, turn_copy = _turn_prompt(st.session_state.messages, is_ar)
    st.markdown(
        f'<div class="{continue_class}"><strong>{turn_title}</strong>{turn_copy}</div>',
        unsafe_allow_html=True,
    )
''',
    '''    continue_class = "continue-card continue-card-ar" if is_ar else "continue-card"
    turn_title, turn_copy = _turn_prompt(st.session_state.messages, is_ar)
    safe_turn_title = html_lib.escape(turn_title)
    safe_turn_copy = html_lib.escape(turn_copy)
    st.markdown(
        f'<div class="{continue_class}"><strong>{safe_turn_title}</strong>{safe_turn_copy}</div>',
        unsafe_allow_html=True,
    )
''',
    "escape turn card",
)

app = replace_once(
    app,
    '''                visible_answer = _display_answer(answer)
                placeholder = st.empty()
                rendered = ""
                chunks = re.findall(r"\\S+\\s*", visible_answer)
                for i, chunk in enumerate(chunks):
                    rendered += chunk
                    placeholder.markdown(rendered + ("▌" if i < len(chunks) - 1 else ""))
                    time.sleep(0.018)
                placeholder.markdown(visible_answer)
''',
    '''                visible_answer = _display_answer(answer)
                # The main screen is intentionally decision-first. Do not stream the
                # long explanation into the primary view; it will live in the collapsed
                # evidence/explanation panel after the immediate rerun below.
                compact_sections = _response_sections(answer)
                if not _is_none_value(compact_sections["what_next"]):
                    st.markdown("### 🎯 المطلوب التالي" if response_language == "ar" else "### 🎯 What next?")
                    st.markdown(compact_sections["what_next"])
                else:
                    st.success("تم تحديث حالة التحقيق." if response_language == "ar" else "Investigation state updated.")
''',
    "compact live render",
)

APP.write_text(app, encoding="utf-8")
print("v1.2 compact render refinements applied")

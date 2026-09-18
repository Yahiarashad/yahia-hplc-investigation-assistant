import os
from pathlib import Path

import streamlit as st
from openai import OpenAI


APP_TITLE = "Yahia HPLC Investigation Assistant"
TAGLINE = "DON'T GUESS. FOLLOW THE EVIDENCE."
MODEL = "gpt-5.6-terra"

st.set_page_config(
    page_title=APP_TITLE,
    page_icon="🧪",
    layout="centered",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
      .block-container {max-width: 820px; padding-top: 1.4rem; padding-bottom: 4rem;}
      h1 {font-size: 2rem !important; line-height: 1.15 !important;}
      .tagline {font-weight: 800; letter-spacing: .04em; margin-top: -.4rem; margin-bottom: 1.2rem;}
      .small-note {font-size: .88rem; opacity: .78;}
      @media (max-width: 640px) {
        .block-container {padding-left: 1rem; padding-right: 1rem; padding-top: 1rem;}
        h1 {font-size: 1.65rem !important;}
      }
    </style>
    """,
    unsafe_allow_html=True,
)


def load_core_prompt() -> str:
    return Path(__file__).with_name("core_prompt.txt").read_text(encoding="utf-8")


def get_api_key():
    try:
        key = st.secrets.get("OPENAI_API_KEY")
        if key:
            return key
    except Exception:
        pass
    return os.environ.get("OPENAI_API_KEY")


CORE_PROMPT = load_core_prompt()
API_KEY = get_api_key()

st.title("🧪 Yahia HPLC Investigation Assistant")
st.markdown(f'<div class="tagline">{TAGLINE}</div>', unsafe_allow_html=True)
st.caption("Evidence-based HPLC troubleshooting & analytical decision support for Pharmaceutical QC")

with st.sidebar:
    st.header("Investigation Setup")
    area = st.selectbox(
        "Closest investigation area",
        [
            "Auto-detect",
            "Pressure",
            "Retention Time",
            "Peak Shape",
            "Baseline",
            "Carryover / Ghost Peaks",
        ],
    )
    st.markdown("---")
    st.markdown("**v0.1 scope**")
    st.markdown("Pressure · RT · Peak Shape · Baseline · Carryover/Ghost Peaks")
    st.info(
        "Decision-support only. Formal GMP investigations must follow approved SOPs, QA requirements, and applicable regulations."
    )
    if st.button("Start new investigation", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

if not API_KEY:
    st.error(
        "The app is not connected to the OpenAI API yet. Add OPENAI_API_KEY in Streamlit Secrets, then reboot the app."
    )
    st.stop()

client = OpenAI(api_key=API_KEY)

if "messages" not in st.session_state:
    st.session_state.messages = []

if not st.session_state.messages:
    st.markdown(
        """
### Start with the observation — not your diagnosis.

**Example case**  
> Pressure was normally 180 bar. Today it increased to 310 bar after about 25 injections. Same method, column, flow, and mobile phase.

The assistant should **not** immediately blame the column. It should identify the missing evidence and choose the next test that best separates the hypotheses.
        """
    )

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

user_input = st.chat_input("Describe the HPLC observation, or answer the last diagnostic question...")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    instructions = (
        CORE_PROMPT
        + f"\n\nCURRENT UI INVESTIGATION AREA: {area}\n"
        + "Treat this selected area only as a hint. If the evidence points to another area, say so."
    )

    api_history = [
        {"role": m["role"], "content": m["content"]}
        for m in st.session_state.messages
    ]

    with st.chat_message("assistant"):
        with st.spinner("Following the evidence..."):
            try:
                response = client.responses.create(
                    model=MODEL,
                    instructions=instructions,
                    input=api_history,
                )
                answer = response.output_text.strip()
                if not answer:
                    answer = "No text response was returned. Please try again."
            except Exception:
                answer = (
                    "I couldn't complete the API request. Please verify the API key, project billing/credits, and model access, then try again."
                )
            st.markdown(answer)

    st.session_state.messages.append({"role": "assistant", "content": answer})

st.markdown("---")
st.markdown(
    '<div class="small-note">v0.1 · Yahia HPLC Investigation Assistant · Pharmaceutical QC decision support</div>',
    unsafe_allow_html=True,
)

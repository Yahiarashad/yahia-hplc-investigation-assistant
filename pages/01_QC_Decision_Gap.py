from pathlib import Path
import hashlib
import random
import runpy
import secrets
import re

import streamlit as st
import streamlit.components.v1 as components

# Thin wrapper around the assessment core.
# It adds mobile-friendly scroll behavior and an anti-cue presentation layer
# without changing the scoring or bilingual analytical logic in qc_gap_core.py.

CORE_PATH = Path(__file__).resolve().parents[1] / "qc_gap_core.py"

# -----------------------------------------------------------------------------
# Attempt seed: keeps answer order stable during one attempt, but changes on a
# new attempt. Language switching does not reshuffle answered questions.
# -----------------------------------------------------------------------------
_current_active = bool(st.session_state.get("gap_started") or st.session_state.get("gap_done"))
_previous_active = bool(st.session_state.get("_qc_gap_prev_active", False))
if "_qc_gap_attempt_seed" not in st.session_state:
    st.session_state["_qc_gap_attempt_seed"] = secrets.randbits(48)
elif not _current_active and _previous_active:
    st.session_state["_qc_gap_attempt_seed"] = secrets.randbits(48)
st.session_state["_qc_gap_prev_active"] = _current_active

# -----------------------------------------------------------------------------
# Mobile UX layer.
# 1) Visually separates each answer into a card.
# 2) Scrolls to the TRUE beginning of the next/previous stage with a safe top
#    offset so the question stem is not hidden under Streamlit's mobile header.
# -----------------------------------------------------------------------------
_pending_target = st.session_state.pop("_qc_gap_scroll_target", None)
_target_js = repr(_pending_target) if _pending_target else "null"

components.html(
    f"""
    <script>
    (function() {{
      const doc = window.parent.document;
      const win = window.parent;
      const pendingTarget = {_target_js};
      let styleAttempts = 0;

      function decorateQuestionRadios() {{
        const radios = Array.from(doc.querySelectorAll('[data-testid="stRadio"]'));
        if (radios.length < 2) {{
          styleAttempts += 1;
          if (styleAttempts < 30) setTimeout(decorateQuestionRadios, 120);
          return;
        }}

        // Radio 0 is the language selector. All following radio widgets are
        // assessment questions and should read as visually separate cards.
        radios.slice(1).forEach((widget) => {{
          widget.style.marginBottom = '1.55rem';

          const group = widget.querySelector('[role="radiogroup"]');
          if (!group) return;
          group.style.display = 'flex';
          group.style.flexDirection = 'column';
          group.style.gap = '10px';
          group.style.width = '100%';

          const labels = Array.from(group.querySelectorAll('label'));
          labels.forEach((label) => {{
            label.style.display = 'flex';
            label.style.width = '100%';
            label.style.boxSizing = 'border-box';
            label.style.alignItems = 'flex-start';
            label.style.padding = '13px 14px';
            label.style.margin = '0';
            label.style.border = '1px solid rgba(49, 51, 63, 0.18)';
            label.style.borderRadius = '14px';
            label.style.background = 'rgba(248, 250, 252, 0.96)';
            label.style.lineHeight = '1.65';
          }});
        }});
      }}

      function scrollWithOffset(el, offsetPx) {{
        if (!el) return false;
        const currentY = win.pageYOffset || doc.documentElement.scrollTop || 0;
        const y = el.getBoundingClientRect().top + currentY - offsetPx;
        win.scrollTo({{top: Math.max(0, y), behavior: 'smooth'}});

        // Streamlit/mobile text can reflow after the first paint. Correct the
        // position once more after layout settles so the stem stays visible.
        setTimeout(() => {{
          const nowY = win.pageYOffset || doc.documentElement.scrollTop || 0;
          const corrected = el.getBoundingClientRect().top + nowY - offsetPx;
          win.scrollTo({{top: Math.max(0, corrected), behavior: 'auto'}});
        }}, 520);
        return true;
      }}

      function findFirstAssessmentQuestion() {{
        const radios = Array.from(doc.querySelectorAll('[data-testid="stRadio"]'));
        if (radios.length <= 1) return null;
        return radios[1];
      }}

      function findResultHeading() {{
        const headings = Array.from(doc.querySelectorAll('h1,h2,h3'));
        return headings.find((el) => {{
          const t = (el.innerText || '').trim();
          return t.startsWith('Your result') || t.startsWith('نتيجتك');
        }}) || null;
      }}

      function performPendingScroll() {{
        if (!pendingTarget) return;
        let attempts = 0;
        function attempt() {{
          let done = false;
          if (pendingTarget === 'question') {{
            // 118 px leaves the complete question stem visible below the
            // mobile toolbar instead of landing in the middle of the stem.
            done = scrollWithOffset(findFirstAssessmentQuestion(), 118);
          }} else if (pendingTarget === 'result') {{
            done = scrollWithOffset(findResultHeading(), 110);
          }} else if (pendingTarget === 'top') {{
            win.scrollTo({{top: 0, behavior: 'smooth'}});
            done = true;
          }}

          attempts += 1;
          if (!done && attempts < 30) setTimeout(attempt, 120);
        }}
        setTimeout(attempt, 180);
      }}

      decorateQuestionRadios();
      performPendingScroll();

      // Keep the card treatment after Streamlit rerenders widgets locally.
      const observer = new MutationObserver(() => decorateQuestionRadios());
      observer.observe(doc.body, {{childList: true, subtree: true}});
      setTimeout(() => observer.disconnect(), 5000);
    }})();
    </script>
    """,
    height=0,
    width=0,
)

# -----------------------------------------------------------------------------
# Anti-cue presentation layer
# Goal: remove the "longest answer = correct answer" signal while preserving
# the underlying original option index and therefore the exact score/analysis.
# -----------------------------------------------------------------------------
_AR_SUFFIXES = [
    "ثم أقارن النتيجة بالبيانات التاريخية قبل الانتقال إلى تغيير إضافي.",
    "وأتعامل مع هذه الخطوة كدليل أولي يحتاج تفسيرًا مع بقية الملاحظات.",
    "مع توثيق ما تضيفه النتيجة لمسار التحقيق قبل اتخاذ قرار نهائي.",
    "وأراجع هل النتيجة تفسر الملاحظة الحالية أم تترك بدائل معقولة مفتوحة.",
]

_EN_SUFFIXES = [
    "Then compare the outcome with historical data before making another change.",
    "Treat this step as preliminary evidence that still needs interpretation with the other observations.",
    "Document what the result adds to the investigation before making a final decision.",
    "Then check whether the result explains the observation or leaves reasonable alternatives open.",
]


def _is_arabic(text):
    return bool(re.search(r"[\u0600-\u06FF]", text or ""))


def _word_count(text):
    return len(re.findall(r"\S+", text or ""))


def _balanced_labels(labels, question_key):
    """Pad shorter choices with neutral analytical clauses.

    The action itself is never changed, and scoring still uses the original
    option index. Only the displayed wording is balanced to reduce test-taking
    cues based on length or reasoning density.
    """
    if not labels:
        return labels

    counts = [_word_count(x) for x in labels]
    target = max(counts)
    # Avoid turning already-balanced questions into unnecessarily long cards.
    if max(counts) - min(counts) <= 3:
        return labels

    output = []
    for option_index, text in enumerate(labels):
        updated = text.strip()
        suffixes = _AR_SUFFIXES if _is_arabic(updated) else _EN_SUFFIXES
        # Deterministic suffix order for this question/option.
        digest = hashlib.blake2b(
            f"{question_key}:{option_index}:padding".encode("utf-8"),
            digest_size=8,
        ).digest()
        rng = random.Random(int.from_bytes(digest, "big"))
        local_suffixes = suffixes[:]
        rng.shuffle(local_suffixes)

        suffix_pos = 0
        while _word_count(updated) < max(target - 2, 1) and suffix_pos < len(local_suffixes):
            updated = f"{updated} {local_suffixes[suffix_pos]}"
            suffix_pos += 1
        output.append(updated)
    return output


_original_radio = st.radio


def _anti_cue_radio(label, options, *args, **kwargs):
    key = kwargs.get("key")
    if not (isinstance(key, str) and key.startswith("q_")):
        return _original_radio(label, options, *args, **kwargs)

    original_options = list(options)
    original_format = kwargs.get("format_func", str)
    original_labels = [str(original_format(value)) for value in original_options]
    display_labels = _balanced_labels(original_labels, key)
    display_map = {value: display_labels[i] for i, value in enumerate(original_options)}

    # Stable random order for the current attempt and question.
    seed_material = f"{st.session_state['_qc_gap_attempt_seed']}:{key}"
    digest = hashlib.blake2b(seed_material.encode("utf-8"), digest_size=8).digest()
    rng = random.Random(int.from_bytes(digest, "big"))
    shuffled_options = original_options[:]
    rng.shuffle(shuffled_options)

    # Core passes index as the position of the stored original option. Convert
    # it to the corresponding position in the shuffled display order.
    old_index = kwargs.get("index", 0)
    if old_index is None:
        new_index = None
    elif isinstance(old_index, int) and 0 <= old_index < len(original_options):
        selected_value = original_options[old_index]
        new_index = shuffled_options.index(selected_value)
    else:
        new_index = old_index

    kwargs["index"] = new_index
    kwargs["format_func"] = lambda value: display_map[value]
    return _original_radio(label, shuffled_options, *args, **kwargs)


_original_rerun = st.rerun


def _rerun_with_scroll(*args, **kwargs):
    if st.session_state.get("gap_done"):
        st.session_state["_qc_gap_scroll_target"] = "result"
    elif st.session_state.get("gap_started"):
        st.session_state["_qc_gap_scroll_target"] = "question"
    else:
        st.session_state["_qc_gap_scroll_target"] = "top"
    return _original_rerun(*args, **kwargs)


st.radio = _anti_cue_radio
st.rerun = _rerun_with_scroll
try:
    runpy.run_path(str(CORE_PATH), run_name="__main__")
finally:
    st.radio = _original_radio
    st.rerun = _original_rerun

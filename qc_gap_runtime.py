from collections import Counter
from pathlib import Path
import hashlib
import random
import re
import runpy
import secrets
import time

import streamlit as st
import streamlit.components.v1 as components

CORE_PATH = Path(__file__).resolve().parent / "qc_gap_core.py"

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
    if not labels:
        return labels
    counts = [_word_count(x) for x in labels]
    target = max(counts)
    if max(counts) - min(counts) <= 3:
        return labels

    output = []
    for option_index, text in enumerate(labels):
        updated = text.strip()
        suffixes = _AR_SUFFIXES if _is_arabic(updated) else _EN_SUFFIXES
        digest = hashlib.blake2b(
            f"{question_key}:{option_index}:padding".encode("utf-8"), digest_size=8
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


def _longest_same_position_streak(position_map):
    longest = 0
    current = 0
    previous = None
    for question_id in sorted(position_map):
        value = position_map[question_id]
        if value == previous:
            current += 1
        else:
            current = 1
            previous = value
        longest = max(longest, current)
    return longest


def _assessment_confidence():
    position_map = dict(st.session_state.get("_qc_gap_display_positions", {}))
    positions = [position_map[q] for q in sorted(position_map)]
    n = len(positions)
    started_at = st.session_state.get("_qc_gap_started_at")
    elapsed = (time.time() - float(started_at)) if started_at else None

    if n == 0:
        return {
            "level": "moderate",
            "dominant": 0.0,
            "streak": 0,
            "elapsed": elapsed,
            "signals": ["tracking_incomplete"],
        }

    counts = Counter(positions)
    dominant = max(counts.values()) / n
    streak = _longest_same_position_streak(position_map)
    low_signals = []
    moderate_signals = []

    if n >= 20 and dominant >= 0.80:
        low_signals.append("dominant_position")
    elif n >= 20 and dominant >= 0.60:
        moderate_signals.append("dominant_position")

    if streak >= 12:
        low_signals.append("long_streak")
    elif streak >= 8:
        moderate_signals.append("long_streak")

    if elapsed is not None and n >= 25:
        if elapsed < 120:
            low_signals.append("very_fast")
        elif elapsed < 180:
            moderate_signals.append("fast")

    if n < 30:
        moderate_signals.append("tracking_incomplete")

    if low_signals or len(set(moderate_signals)) >= 2:
        level = "low"
        signals = low_signals + moderate_signals
    elif moderate_signals:
        level = "moderate"
        signals = moderate_signals
    else:
        level = "high"
        signals = []

    return {
        "level": level,
        "dominant": dominant,
        "streak": streak,
        "elapsed": elapsed,
        "signals": list(dict.fromkeys(signals)),
    }


def _confidence_card_html(snapshot, lang):
    level = snapshot["level"]
    palette = {
        "high": ("#2E7D32", "مرتفعة", "High"),
        "moderate": ("#9A7412", "متوسطة", "Moderate"),
        "low": ("#B23A3A", "منخفضة", "Low"),
    }
    color, ar_level, en_level = palette[level]

    if lang == "ar":
        title = "موثوقية النتيجة"
        level_text = ar_level
        if level == "high":
            body = "نمط الإجابات ووقت الإكمال لا يظهران إشارات واضحة على نقر آلي أو نمط متكرر؛ لذلك يمكن تفسير الدرجة والفجوات المهنية بدرجة ثقة جيدة."
        elif level == "moderate":
            body = "الدرجة الحسابية صحيحة، لكن ظهرت إشارة سلوكية تستدعي بعض الحذر عند تفسير الفجوات أو المستوى المهني."
        else:
            body = "الدرجة الحسابية صحيحة، لكن نمط المحاولة يقلل ثقتنا في التفسير المهني للنتيجة. لا ننصح باعتبار الفجوات أو المستوى المهني تقييمًا دقيقًا قبل إعادة الاختبار بقراءة كل سيناريو واختيار أفضل قرار."
        signal_labels = {
            "dominant_position": f"تم اختيار نفس موضع الإجابة في نحو {round(snapshot['dominant'] * 100)}% من الأسئلة",
            "long_streak": f"ظهرت سلسلة متتالية من {snapshot['streak']} إجابة في نفس الموضع",
            "very_fast": "تم إنهاء الاختبار بسرعة شديدة بالنسبة إلى 30 سؤالًا تحليليًا",
            "fast": "وقت الإكمال أسرع من المتوقع لاختبار تحليلي بهذا الطول",
            "tracking_incomplete": "بيانات سلوك المحاولة غير مكتملة",
        }
        direction, align = "rtl", "right"
    else:
        title = "Assessment Confidence"
        level_text = en_level
        if level == "high":
            body = "The response pattern and completion time show no clear signs of mechanical clicking or repetitive selection, so the score and professional gaps can be interpreted with good confidence."
        elif level == "moderate":
            body = "The numerical score is valid, but one behavioral signal suggests caution when interpreting the professional gaps or level."
        else:
            body = "The numerical score is valid, but the attempt pattern reduces confidence in the professional interpretation. Retake the assessment carefully before treating the gaps or Professional Level as reliable."
        signal_labels = {
            "dominant_position": f"The same displayed answer position was selected in about {round(snapshot['dominant'] * 100)}% of questions",
            "long_streak": f"A run of {snapshot['streak']} consecutive answers used the same displayed position",
            "very_fast": "The assessment was completed unusually quickly for 30 analytical questions",
            "fast": "Completion time was faster than expected for an assessment of this depth",
            "tracking_incomplete": "Attempt-behavior data is incomplete",
        }
        direction, align = "ltr", "left"

    signals = [signal_labels[x] for x in snapshot["signals"] if x in signal_labels]
    signals_html = (
        ("<p class='mini'><b>الإشارات:</b> " if lang == "ar" else "<p class='mini'><b>Signals:</b> ")
        + " · ".join(signals)
        + "</p>"
        if signals
        else ""
    )

    return f"""
    <div class='section-card' style='border:1px solid {color}55; direction:{direction}; text-align:{align};'>
      <div class='result-label' style='color:{color};'>{title}</div>
      <h3 style='margin-top:.35rem;'>{level_text}</h3>
      <p>{body}</p>
      {signals_html}
    </div>
    """


def _inject_mobile_js(pending_target):
    target_js = repr(pending_target) if pending_target else "null"
    components.html(
        f"""
        <script>
        (function() {{
          const doc = window.parent.document;
          const win = window.parent;
          const pendingTarget = {target_js};
          let styleAttempts = 0;

          function assessmentRadios() {{
            return Array.from(doc.querySelectorAll('[data-testid="stRadio"]')).filter((widget) => {{
              const text = (widget.innerText || '').trim();
              return /^\d+\./.test(text);
            }});
          }}

          function findQuestion(number) {{
            const prefix = String(number) + '.';
            return assessmentRadios().find((widget) => (widget.innerText || '').trim().startsWith(prefix)) || null;
          }}

          function decorateQuestionRadios() {{
            const radios = assessmentRadios();
            if (radios.length < 1) {{
              styleAttempts += 1;
              if (styleAttempts < 35) setTimeout(decorateQuestionRadios, 120);
              return;
            }}
            radios.forEach((widget) => {{
              widget.style.marginBottom = '1.55rem';
              const group = widget.querySelector('[role="radiogroup"]');
              if (!group) return;
              group.style.display = 'flex';
              group.style.flexDirection = 'column';
              group.style.gap = '10px';
              group.style.width = '100%';
              Array.from(group.querySelectorAll('label')).forEach((label) => {{
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

          function findScrollableAncestor(el) {{
            let node = el ? el.parentElement : null;
            while (node && node !== doc.body && node !== doc.documentElement) {{
              const style = win.getComputedStyle(node);
              if ((style.overflowY === 'auto' || style.overflowY === 'scroll') && node.scrollHeight > node.clientHeight + 2) return node;
              node = node.parentElement;
            }}
            const candidates = [
              doc.querySelector('[data-testid="stMain"]'),
              doc.querySelector('section.main'),
              doc.querySelector('[data-testid="stAppViewContainer"]')
            ].filter(Boolean);
            for (const candidate of candidates) {{
              if (candidate.scrollHeight > candidate.clientHeight + 2) return candidate;
            }}
            return doc.scrollingElement || doc.documentElement;
          }}

          function scrollElementToTop(el, offsetPx) {{
            if (!el || !el.isConnected) return false;
            const scroller = findScrollableAncestor(el);
            const elRect = el.getBoundingClientRect();
            if (scroller === doc.scrollingElement || scroller === doc.documentElement || scroller === doc.body) {{
              const current = win.scrollY || doc.documentElement.scrollTop || 0;
              win.scrollTo({{top: Math.max(0, current + elRect.top - offsetPx), behavior:'auto'}});
            }} else {{
              const scRect = scroller.getBoundingClientRect();
              const target = scroller.scrollTop + (elRect.top - scRect.top) - offsetPx;
              scroller.scrollTo({{top: Math.max(0, target), behavior:'auto'}});
            }}
            return true;
          }}

          function findResultHeading() {{
            return Array.from(doc.querySelectorAll('h1,h2,h3')).find((el) => {{
              const t = (el.innerText || '').trim();
              return t.startsWith('Your result') || t.startsWith('نتيجتك');
            }}) || null;
          }}

          function scrollExactQuestion(questionNumber) {{
            let attempts = 0;
            function attempt() {{
              const el = findQuestion(questionNumber);
              if (el) {{
                scrollElementToTop(el, 104);
                [250, 650, 1100].forEach((delay) => setTimeout(() => {{
                  const fresh = findQuestion(questionNumber);
                  if (fresh) scrollElementToTop(fresh, 104);
                }}, delay));
                return;
              }}
              attempts += 1;
              if (attempts < 55) setTimeout(attempt, 120);
            }}
            setTimeout(attempt, 120);
          }}

          function performPendingScroll() {{
            if (!pendingTarget) return;
            if (pendingTarget.startsWith('q:')) {{
              const n = parseInt(pendingTarget.split(':')[1], 10);
              if (!Number.isNaN(n)) scrollExactQuestion(n);
            }} else if (pendingTarget === 'result') {{
              let attempts = 0;
              function resultAttempt() {{
                const heading = findResultHeading();
                if (heading) {{ scrollElementToTop(heading, 96); return; }}
                attempts += 1;
                if (attempts < 50) setTimeout(resultAttempt, 120);
              }}
              setTimeout(resultAttempt, 140);
            }} else if (pendingTarget === 'top') {{
              const root = doc.querySelector('[data-testid="stAppViewContainer"]') || doc.body;
              const scroller = findScrollableAncestor(root);
              if (scroller && scroller.scrollTo) scroller.scrollTo({{top:0, behavior:'auto'}});
              else win.scrollTo({{top:0, behavior:'auto'}});
            }}
          }}

          decorateQuestionRadios();
          performPendingScroll();
          const observer = new MutationObserver(() => decorateQuestionRadios());
          observer.observe(doc.body, {{childList:true, subtree:true}});
          setTimeout(() => observer.disconnect(), 5500);
        }})();
        </script>
        """,
        height=0,
        width=0,
    )


def run_assessment_page():
    current_active = bool(st.session_state.get("gap_started") or st.session_state.get("gap_done"))
    previous_active = bool(st.session_state.get("_qc_gap_prev_active", False))

    if "_qc_gap_attempt_seed" not in st.session_state:
        st.session_state["_qc_gap_attempt_seed"] = secrets.randbits(48)

    if current_active and "_qc_gap_started_at" not in st.session_state:
        st.session_state["_qc_gap_started_at"] = time.time()
        st.session_state["_qc_gap_display_positions"] = {}
    elif not current_active and previous_active:
        st.session_state["_qc_gap_attempt_seed"] = secrets.randbits(48)
        st.session_state.pop("_qc_gap_started_at", None)
        st.session_state.pop("_qc_gap_display_positions", None)

    st.session_state["_qc_gap_prev_active"] = current_active

    pending_target = st.session_state.pop("_qc_gap_scroll_target", None)
    _inject_mobile_js(pending_target)

    original_radio = st.radio
    original_markdown = st.markdown
    original_rerun = st.rerun

    def anti_cue_radio(label, options, *args, **kwargs):
        key = kwargs.get("key")
        if not (isinstance(key, str) and key.startswith("q_")):
            return original_radio(label, options, *args, **kwargs)

        original_options = list(options)
        original_format = kwargs.get("format_func", str)
        original_labels = [str(original_format(value)) for value in original_options]
        display_labels = _balanced_labels(original_labels, key)
        display_map = {value: display_labels[i] for i, value in enumerate(original_options)}

        seed_material = f"{st.session_state['_qc_gap_attempt_seed']}:{key}"
        digest = hashlib.blake2b(seed_material.encode("utf-8"), digest_size=8).digest()
        rng = random.Random(int.from_bytes(digest, "big"))
        shuffled_options = original_options[:]
        rng.shuffle(shuffled_options)

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
        selected = original_radio(label, shuffled_options, *args, **kwargs)

        if selected is not None:
            try:
                question_id = int(key.split("_", 1)[1])
                displayed_position = shuffled_options.index(selected)
                positions = st.session_state.setdefault("_qc_gap_display_positions", {})
                positions[question_id] = displayed_position
            except (ValueError, TypeError):
                pass
        return selected

    confidence_snapshot = _assessment_confidence() if st.session_state.get("gap_done") else None
    confidence_injected = {"done": False}

    def markdown_with_confidence(body, *args, **kwargs):
        result = original_markdown(body, *args, **kwargs)
        if (
            confidence_snapshot
            and not confidence_injected["done"]
            and isinstance(body, str)
            and "section-card" in body
            and "result-label" in body
            and "/100" in body
        ):
            lang = "ar" if st.session_state.get("gap_lang", "العربية") == "العربية" else "en"
            original_markdown(_confidence_card_html(confidence_snapshot, lang), unsafe_allow_html=True)
            confidence_injected["done"] = True
        return result

    def rerun_with_scroll(*args, **kwargs):
        if st.session_state.get("gap_done"):
            st.session_state["_qc_gap_scroll_target"] = "result"
        elif st.session_state.get("gap_started"):
            step = int(st.session_state.get("gap_step", 0) or 0)
            target_question = step * 5 + 1
            st.session_state["_qc_gap_scroll_target"] = f"q:{target_question}"
        else:
            st.session_state["_qc_gap_scroll_target"] = "top"
        return original_rerun(*args, **kwargs)

    st.radio = anti_cue_radio
    st.markdown = markdown_with_confidence
    st.rerun = rerun_with_scroll
    try:
        runpy.run_path(str(CORE_PATH), run_name="__main__")
    finally:
        st.radio = original_radio
        st.markdown = original_markdown
        st.rerun = original_rerun

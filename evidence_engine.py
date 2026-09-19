import json
import re
from pathlib import Path

KB_PATH = Path(__file__).with_name("verified_evidence.json")


def _load_cards():
    return json.loads(KB_PATH.read_text(encoding="utf-8"))


def _normalize(text: str) -> str:
    text = (text or "").lower()
    text = re.sub(r"[^\w\u0600-\u06FF%/+-]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _track_hplc_beta_usage(query: str, area: str):
    """Track anonymous usage signals only. Never stores the HPLC case text."""
    try:
        import streamlit as st
        from beta_feedback import record_event

        case_id = st.query_params.get("case")
        if isinstance(case_id, list):
            case_id = case_id[0] if case_id else None
        if not case_id:
            return

        language = "ar" if re.search(r"[\u0600-\u06FF]", query or "") else "en"
        started_key = f"_beta_hplc_started_{case_id}"
        count_key = f"_beta_hplc_message_count_{case_id}"

        if not st.session_state.get(started_key):
            record_event(
                case_id,
                "hplc_assistant",
                "investigation_started",
                language,
                metadata={"area": area or "Auto-detect"},
            )
            st.session_state[started_key] = True

        count = int(st.session_state.get(count_key, 0)) + 1
        st.session_state[count_key] = count
        record_event(
            case_id,
            "hplc_assistant",
            "investigation_message",
            language,
            metadata={"area": area or "Auto-detect", "message_number": count},
        )
    except Exception:
        # Analytics must never interrupt an HPLC investigation.
        return


def retrieve_evidence(query: str, area: str = "Auto-detect", limit: int = 4):
    """Return a small set of relevant curated evidence cards without external API calls."""
    _track_hplc_beta_usage(query, area)

    cards = _load_cards()
    haystack = _normalize(query)
    scored = []

    regulatory_terms = {
        "oos", "oot", "gmp", "sop", "qa", "investigation", "retest", "retesting",
        "تحقيق", "توثيق", "إعادة الاختبار", "خارج المواصفة",
    }
    needs_regulatory = any(term in haystack for term in regulatory_terms)

    for card in cards:
        score = 0
        areas = card.get("areas", [])
        if area and area != "Auto-detect" and area in areas:
            score += 6

        for keyword in card.get("keywords", []):
            kw = _normalize(keyword)
            if kw and kw in haystack:
                score += 3 if " " in kw else 2

        if needs_regulatory and "GMP Investigation" in areas:
            score += 5

        # Broad chromatographic cards can still support sparse auto-detect cases.
        if area == "Auto-detect" and score == 0:
            if any(token in haystack for token in ("hplc", "peak", "rt", "pressure", "chromat", "قمة", "ضغط", "احتجاز")):
                if len(areas) >= 3:
                    score = 1

        if score > 0:
            scored.append((score, card))

    scored.sort(key=lambda item: (-item[0], item[1]["id"]))
    selected = [card for _, card in scored[:limit]]

    # Keep a regulatory guardrail available when the case explicitly invokes GMP/OOS/OOT.
    if needs_regulatory and not any(card["id"] == "FDA-OOS-12" for card in selected):
        fda = next((card for card in cards if card["id"] == "FDA-OOS-12"), None)
        if fda:
            selected = ([fda] + selected)[:limit]

    return selected


def format_evidence_context(cards) -> str:
    if not cards:
        return (
            "VERIFIED EVIDENCE CONTEXT: No curated evidence card was strongly matched. "
            "Do not invent citations or claim source support. Continue using evidence-first diagnostic logic."
        )

    lines = [
        "VERIFIED EVIDENCE CONTEXT",
        "Use these cards only as supporting evidence, not as a substitute for case-specific proof.",
        "If you cite a source, cite only the source IDs supplied below and preserve the exact URL.",
        "Do not fabricate quotations, limits, acceptance criteria, or regulatory requirements.",
        "Do not force a citation into every reply; cite when it materially supports a diagnostic or GMP point.",
        "",
    ]

    for card in cards:
        lines.extend(
            [
                f"[{card['id']}] {card['authority']} — {card['title']}",
                f"Evidence summary: {card['evidence']}",
                f"Guardrail: {card['guardrail']}",
                f"Source URL: {card['url']}",
                "",
            ]
        )

    return "\n".join(lines).strip()

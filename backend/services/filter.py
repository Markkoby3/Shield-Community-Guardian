from typing import Literal
from backend.models import Report

# ── Keyword config — extend here without touching logic ───────────────────────

SIGNAL_KEYWORDS: frozenset[str] = frozenset({
    "phishing", "scam", "breach", "theft", "alert", "outage"
})

NOISE_KEYWORDS: frozenset[str] = frozenset({
    "wifi sucks", "internet slow", "hate my isp"
})

# Maps a frozenset of trigger words → (category, severity)
CATEGORY_MAP: list[tuple[frozenset[str], str, Literal["high", "medium", "low"]]] = [
    (frozenset({"phishing", "breach"}), "cyber_threat",    "high"),
    (frozenset({"scam"}),               "scam_alert",      "medium"),
    (frozenset({"theft"}),              "local_crime",     "medium"),
    (frozenset({"outage"}),             "infrastructure",  "medium"),
]


# ── Logic ─────────────────────────────────────────────────────────────────────

def filter_reports(reports: list[Report]) -> list[Report]:
    """Keep only reports that contain a signal keyword. Signal beats noise."""
    result = []
    for r in reports:
        text = r.text.lower()
        if any(s in text for s in SIGNAL_KEYWORDS):
            result.append(r)
    return result


def classify_alert(text: str) -> tuple[str, Literal["high", "medium", "low"]]:
    """Return (category, severity) for the given alert text."""
    lowered = text.lower()
    for triggers, category, severity in CATEGORY_MAP:
        if any(t in lowered for t in triggers):
            return category, severity
    return "general", "low"

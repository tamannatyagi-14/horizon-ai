"""AI-Slop detector: rule-based humanization score (no API call, zero cost).

Score starts at 100 and loses points for clichéd AI phrases, tell-tale
sentence patterns and em-dash overuse. Everything it flags is returned, so
the UI can show exactly why the score dropped.
"""
import re

PHRASE_PENALTY = 7
PATTERN_PENALTY = 8
DASH_PENALTY = 4
DASH_PENALTY_CAP = 16
DASHES_ALLOWED_PER_100_WORDS = 1

# Stems: a short suffix is allowed, so "unlock" also catches "unlocking",
# and "leverag" catches "leverage / leveraging / leveraged".
SLOP_PHRASES = [
    "game-changer", "game changer", "game-changing", "delve", "unlock", "unleash",
    "supercharg", "revolutioni", "transformative", "cutting-edge", "seamless",
    "leverag", "harness the power", "elevat", "paradigm shift", "synergy",
    "robust", "tapestry", "testament to", "navigate the complexities",
    "ever-evolving", "fast-paced world", "rapidly evolving", "in today's world",
    "at the end of the day", "take it to the next level", "deep dive",
    "let that sink in", "buckle up", "here's the thing",
    "i'm excited to share", "i am excited to share", "humbled",
    "completely rewired", "treasure trove", "unparalleled", "groundbreaking",
    "ruthlessly efficient", "thrilled", "excited to announce", "proud to announce",
    "in the realm of", "digital landscape", "ever-changing", "it's worth noting",
    "it's important to note", "plays a crucial role", "pivotal", "moreover",
    "furthermore", "in conclusion", "stay tuned", "agonizing", "the best part?",
    "here's why", "the kicker", "spoiler", "sound familiar", "ever wondered",
    "imagine this", "picture this", "no more", "mind-blowing", "next-level",
]

PATTERNS = [
    (r"\bnot just\b[^.?!]{0,50}\bbut\b[^.?!]{0,40}", "not just … but …"),
    (r"\b(?:isn't|is not|wasn't|was not|it's not|it is not|not about)\b[^.?!]{0,45}[;,—]\s*(?:it's|it is|it was|it’s)\b[^.?!]{0,30}",
     "it isn't X — it's Y"),
    (r"\bmore than just\b[^.?!]{0,30}", "more than just …"),
    (r"\bin a world where\b[^.?!]{0,30}", "in a world where …"),
    (r"\bdiv(?:e|es|ed|ing)\s+(?:deep\s+)?into\b", "dive into"),
]

_PHRASE_RES = [(p, re.compile(r"(?<!\w)" + re.escape(p) + r"\w{0,4}(?!\w)", re.I)) for p in SLOP_PHRASES]
_PATTERN_RES = [(re.compile(rx, re.I), name) for rx, name in PATTERNS]


def analyze_slop(text: str) -> dict:
    text = (text or "").replace("’", "'")
    words = max(len(text.split()), 1)
    flagged, penalty = [], 0

    for _, rx in _PHRASE_RES:
        m = rx.search(text)
        if m:
            flagged.append(m.group(0).lower())  # show the real text, not the stem
            penalty += PHRASE_PENALTY

    for rx, name in _PATTERN_RES:
        m = rx.search(text)
        if m:
            flagged.append(m.group(0).strip()[:45] or name)
            penalty += PATTERN_PENALTY

    dashes = text.count("—")
    allowed = max(1, round(words / 100 * DASHES_ALLOWED_PER_100_WORDS))
    if dashes > allowed:
        penalty += min((dashes - allowed) * DASH_PENALTY, DASH_PENALTY_CAP)
        flagged.append(f"{dashes} em dashes (—)")

    score = max(0, min(100, 100 - penalty))
    label = "Human" if score >= 75 else "Mixed" if score >= 50 else "Robotic"
    return {"human_score": score, "flagged": flagged, "label": label}


def _post_text(out: dict) -> str:
    tweets = out.get("tweets") or []
    return "\n\n".join(tweets) if tweets else out.get("content", "")


def slop_node(state) -> dict:
    """Scores the FINAL posts (what the user will publish), per platform.

    The overall score is the worst platform, so one robotic post is not hidden
    by two clean ones. Falls back to the draft if there are no posts yet.
    """
    outs = state.get("platform_outputs") or {}
    texts = {k: _post_text(v) for k, v in outs.items() if _post_text(v)}
    if not texts:
        return {"slop": analyze_slop(state.get("draft", ""))}
    per = {k: analyze_slop(t) for k, t in texts.items()}
    worst = min(per.values(), key=lambda r: r["human_score"])
    flagged = []
    for k, r in per.items():
        flagged += [f"{f} ({k})" for f in r["flagged"]]
    return {"slop": {"human_score": worst["human_score"], "flagged": flagged,
                     "label": worst["label"],
                     "by_platform": {k: r["human_score"] for k, r in per.items()}}}
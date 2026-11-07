"""Engagement predictor: Gemini scores hook / CTA / emotion, Python computes virality."""
import json
import re

from prompts.engagement_prompt import ENGAGEMENT_PROMPT
from utils.gemini_client import call_gemini

# Weights are ours, not the model's, so the final number is explainable.
W_HOOK, W_CTA, W_EMOTION = 0.40, 0.25, 0.35


def _to_dict(result) -> dict:
    if isinstance(result, dict):
        return result
    text = re.sub(r"^```(?:json)?|```$", "", str(result).strip(), flags=re.M).strip()
    try:
        return json.loads(text)
    except (ValueError, TypeError):
        return {}


def _score(v) -> int:
    try:
        return max(0, min(100, int(round(float(v)))))
    except (TypeError, ValueError):
        return 0


def _label(value, tiers):
    for floor, name in tiers:
        if value >= floor:
            return name
    return tiers[-1][1]


def engagement_node(state) -> dict:
    prompt = ENGAGEMENT_PROMPT.replace("{draft}", state.get("draft", ""))
    data = _to_dict(call_gemini(prompt))

    hook = _score(data.get("hook_score"))
    cta = _score(data.get("cta_score"))
    emotion = _score(data.get("emotion_score"))
    virality = round(W_HOOK * hook + W_CTA * cta + W_EMOTION * emotion)

    return {
        "engagement": {
            "virality": virality,
            "hook": {"score": hook, "label": _label(hook, [(70, "Strong"), (40, "Medium"), (0, "Weak")])},
            "cta": {"score": cta, "label": _label(cta, [(60, "Present"), (30, "Weak"), (0, "Missing")])},
            "emotion": {"score": emotion, "label": _label(emotion, [(70, "High"), (40, "Medium"), (0, "Low")])},
            "tip": str(data.get("tip", "")).strip()[:160],
        }
    }
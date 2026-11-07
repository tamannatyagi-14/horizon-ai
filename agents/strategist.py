"""Strategist agent: learns style rules from the user's rated past posts.

Cold start: stays asleep until MIN_RATED posts have a rating. After that it
shows the best and worst rated posts to Gemini, gets 3 concrete style rules,
and appends them to the research notes so the Writer follows them
(prompt conditioning, loosely inspired by learning from human feedback).
Rules are cached per set of ratings, so most runs cost no extra API call.
"""
import json
import re

from prompts.strategist_prompt import STRATEGIST_PROMPT
from utils import cache, history_db
from utils.gemini_client import call_gemini

MIN_RATED = 10
TOP_N, LOW_N = 5, 3
SNIPPET_CHARS = 450


def status() -> dict:
    n = history_db.rated_count()
    return {"rated": n, "needed": MIN_RATED, "active": n >= MIN_RATED}


def _post_text(run: dict) -> str:
    text = run.get("draft") or (run.get("outputs", {}).get("linkedin") or {}).get("content", "")
    return (text or "").strip()[:SNIPPET_CHARS]


def _format(runs) -> str:
    if not runs:
        return "(none)"
    return "\n---\n".join(f"[rating {r['rating']}] {_post_text(r)}" for r in runs)


def _to_dict(result) -> dict:
    if isinstance(result, dict):
        return result
    text = re.sub(r"^```(?:json)?|```$", "", str(result).strip(), flags=re.M).strip()
    try:
        return json.loads(text)
    except (ValueError, TypeError):
        return {}


def strategist_node(state) -> dict:
    """Returns {"strategy": {...}} and, when rules exist, an updated research_notes."""
    info = {**status(), "rules": [], "called": False}
    if not info["active"]:
        return {"strategy": info}

    try:
        rows = history_db.rated_runs()
        top = [r for r in rows if r["rating"] >= 4][:TOP_N]
        low = [r for r in rows if r["rating"] <= 2][:LOW_N]
        if len(top) < 2:  # nothing to learn from yet
            return {"strategy": info}

        signature = ",".join(f"{r['id']}:{r['rating']}" for r in top + low)
        key = cache.make_key("strategy:" + signature, "")
        cached = cache.get(key)
        if cached:
            rules = cached["rules"]
        else:
            prompt = STRATEGIST_PROMPT.replace("{top}", _format(top)).replace("{low}", _format(low))
            data = _to_dict(call_gemini(prompt))
            rules = [str(x).strip() for x in (data.get("rules") or []) if str(x).strip()][:3]
            info["called"] = True
            if rules:
                cache.put(key, {"rules": rules})

        info["rules"] = rules
        if rules:
            block = (
                "\n\nSTYLE RULES learned from this creator's best-performing past posts (follow them):\n"
                + "\n".join(f"- {r}" for r in rules)
            )
            return {"strategy": info, "research_notes": str(state.get("research_notes", "")) + block}
    except Exception:  # noqa: BLE001 — the Strategist must never block a run
        pass
    return {"strategy": info}
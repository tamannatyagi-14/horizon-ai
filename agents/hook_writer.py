"""Hook writer: rewrites ONLY the opening hook of a finished post.

The rest of the post is never sent back through the model for rewriting, so it
stays word-for-word identical (cheap: one small call, no pipeline rerun).
"""
import copy
import re

from prompts.hook_prompt import HOOK_PROMPT
from utils.gemini_client import call_gemini
from utils.json_utils import to_dict

MAX_WORDS = {"linkedin": 35, "instagram": 25, "twitter": 30}
MAX_HOOK_PARAGRAPH_WORDS = 60
TWEET_LIMIT = 280


def split_hook(text: str):
    """Split a post into (hook, separator, rest). Hook = first paragraph, else first sentence."""
    text = (text or "").strip()
    head, sep, tail = text.partition("\n\n")
    if sep and len(head.split()) <= MAX_HOOK_PARAGRAPH_WORDS:
        return head, sep, tail
    m = re.match(r"(.+?[.!?])(\s+)(.+)", text, re.S)
    if m:
        return m.group(1), m.group(2), m.group(3)
    return text, "", ""


def regenerate_hook(platform: str, out: dict, tone: str, used: list):
    """Return (new_out, new_hook, old_hook). `out` is one platform's output dict."""
    new_out = copy.deepcopy(out)
    tweets = new_out.get("tweets")
    if tweets:
        old, sep, rest = tweets[0], "\n\n", "\n\n".join(tweets[1:])
    else:
        old, sep, rest = split_hook(new_out.get("content", ""))
    if not old:
        raise ValueError("There is no post text to rewrite yet.")

    tried = [h for h in used if h != old]
    prompt = (
        HOOK_PROMPT.replace("{platform}", platform.title())
        .replace("{tone}", tone)
        .replace("{hook}", old)
        .replace("{used}", "\n".join(f"- {h}" for h in tried) or "(none yet)")
        .replace("{rest}", rest or "(the hook is the whole post)")
        .replace("{max_words}", str(MAX_WORDS.get(platform, 30)))
        .replace("{extra}", " and under 250 characters" if platform == "twitter" else "")
    )
    hook = str(to_dict(call_gemini(prompt)).get("hook", "")).strip().strip('"“”')
    if not hook:
        raise ValueError("The model did not return a hook. Please try again.")
    if platform == "twitter" and len(hook) > TWEET_LIMIT:
        raise ValueError("The new hook was longer than a tweet. Please try again.")

    if tweets:
        new_out["tweets"][0] = hook
    else:
        new_out["content"] = hook + (sep + rest if rest else "")
    return new_out, hook, old
HOOK_PROMPT = """You are rewriting ONLY the opening hook of a {platform} post. Tone: {tone}.

CURRENT HOOK:
{hook}

HOOKS ALREADY TRIED (do not repeat their style or wording):
{used}

REST OF THE POST (context only, do NOT rewrite or repeat it):
{rest}

Write ONE new hook that:
- opens differently from every hook above (for example a surprising number, a bold claim, a short story moment, a contrarian take, or a direct question)
- stays true to the facts in the post; never invent numbers, names or achievements
- flows naturally into the rest of the post, in the same tone
- is at most {max_words} words{extra}

Return ONLY valid JSON, no markdown:
{"hook": "..."}"""
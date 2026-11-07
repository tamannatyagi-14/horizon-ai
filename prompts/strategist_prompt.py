STRATEGIST_PROMPT = """You are a content strategist. Below are social posts written for ONE creator. Each has the rating the creator gave after seeing how it performed (1 = flopped, 5 = did great).

BEST-PERFORMING POSTS (rating 4-5):
{top}

WORST-PERFORMING POSTS (rating 1-2):
{low}

Find patterns that separate the best from the worst: hook style, opening words, length, structure, tone, the kind of closing question, use of numbers or specifics.

Return exactly 3 style rules the writer should follow for the next post. Each rule must:
- be specific and actionable (never vague advice like "be engaging")
- be backed by a pattern you can actually see in the posts above
- be one sentence, at most 25 words

If there are no worst-performing posts, base the rules only on what the best posts have in common.

Return ONLY valid JSON, no markdown:
{"rules": ["...", "...", "..."]}"""
ENGAGEMENT_PROMPT = """You are a social media analyst. Score the post below for how likely it is to earn engagement. Judge ONLY what is written, be strict and do not flatter.

Score each from 0 to 100:
- hook_score: do the first two lines stop the scroll? A surprising fact, bold claim or tension scores high. A generic opener or "I am excited to..." scores low.
- cta_score: does it end with a clear, easy-to-answer question or invitation? No ask at all means under 20.
- emotion_score: does it create curiosity, pride, vulnerability, tension or humour? Flat, corporate writing scores low.

Also give ONE short, specific tip (max 20 words) to improve the weakest part.

Return ONLY valid JSON, no markdown:
{"hook_score": 0, "cta_score": 0, "emotion_score": 0, "tip": "..."}

POST:
{draft}"""
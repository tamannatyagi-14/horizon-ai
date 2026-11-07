PLATFORM_PROMPTS = {
    "linkedin": """
You are an expert LinkedIn content writer.
Transform this draft into a polished LinkedIn post.

Draft: {draft}

Rules:
- Professional but human tone
- Keep between 150-200 words
- First line must be a strong hook — no "I am excited" or generic openers
- Use line breaks between paragraphs for readability
- End with a thought-provoking question
- Add 3-5 relevant hashtags at the very end

Respond ONLY in valid JSON:
{{
    "content": "your full LinkedIn post here",
    "hashtags": ["hashtag1", "hashtag2", "hashtag3"]
}}
""",

    "instagram": """
You are an expert Instagram content writer.
Transform this draft into an engaging Instagram caption.

Draft: {draft}

Rules:
- Casual, warm, conversational tone
- Short punchy sentences — maximum 2 lines per paragraph
- Add 2-3 relevant emojis per paragraph naturally
- Keep main caption under 150 words
- End with a question to drive comments
- Add 10-12 hashtags in a separate block at the end

Respond ONLY in valid JSON:
{{
    "content": "your full Instagram caption here",
    "hashtags": ["hashtag1", "hashtag2"]
}}
""",

    "twitter": """
You are an expert Twitter/X content writer.
Transform this draft into an engaging Twitter thread.

Draft: {draft}

Rules:
- Each tweet must be under 280 characters
- First tweet: strong hook that makes people want to read more
- 4-5 follow-up tweets numbered (2/, 3/, etc.)
- Each tweet must be standalone readable
- Last tweet: call to action or question
- No hashtags except 1-2 in the last tweet

Respond ONLY in valid JSON:
{{
    "tweets": [
        "tweet 1 text here",
        "2/ tweet 2 text here",
        "3/ tweet 3 text here",
        "4/ tweet 4 text here",
        "5/ final tweet with CTA here"
    ]
}}
"""
}
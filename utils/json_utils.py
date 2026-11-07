import json
import re


def to_dict(result) -> dict:
    """Gemini sometimes returns a dict, sometimes JSON text in a markdown fence."""
    if isinstance(result, dict):
        return result
    text = re.sub(r"^```(?:json)?|```$", "", str(result).strip(), flags=re.M).strip()
    try:
        data = json.loads(text)
        return data if isinstance(data, dict) else {}
    except (ValueError, TypeError):
        return {}
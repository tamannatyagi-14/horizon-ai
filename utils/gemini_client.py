from google import genai
import json
import time
from config.settings import GEMINI_API_KEY, FLASH_LITE, FLASH

client = genai.Client(api_key=GEMINI_API_KEY)

def call_gemini(prompt: str, use_flash: bool = False, retries: int = 3) -> dict:
    """
    Gemini ko call karo aur JSON response return karo.
    use_flash=True sirf Writer agent ke liye hoga.
    """
    model = FLASH if use_flash else FLASH_LITE

    for attempt in range(retries):
        try:
            response = client.models.generate_content(
                model=model,
                contents=prompt
            )
            text = response.text.strip()


            if text.startswith("```"):
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]

            return json.loads(text)

        except json.JSONDecodeError:
            if attempt == retries - 1:
                return {"raw_text": response.text, "error": "JSON parse failed"}
            time.sleep(2 ** attempt)

        except Exception as e:
            if "429" in str(e):
                time.sleep(2 ** attempt)
            else:
                raise

    return {"error": "All retries failed"}

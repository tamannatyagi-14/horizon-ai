from dotenv import load_dotenv
import os

# .env file se API key load karo
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Model names
FLASH_LITE = "gemini-3.5-flash-lite"
FLASH = "gemini-3.5-flash-lite"           

# Pipeline settings
MAX_RETRIES = 3                         # Editor max retry count
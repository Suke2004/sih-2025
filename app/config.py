import os
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
TTS_MODEL = "tts_models/multilingual/multi-dataset/your_tts"

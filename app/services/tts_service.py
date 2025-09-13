import uuid
from TTS.api import TTS
from config import TTS_MODEL

tts = TTS(TTS_MODEL)

def generate_speech(text: str) -> str:
    file_name = f"speech_{uuid.uuid4().hex}.wav"
    tts.tts_to_file(text=text, file_path=file_name)
    return file_name

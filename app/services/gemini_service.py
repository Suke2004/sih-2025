import google.generativeai as genai
from config import GEMINI_API_KEY

genai.configure(api_key=GEMINI_API_KEY)

def analyze_image_with_gemini(image_bytes: bytes, prompt: str, mime_type: str) -> str:
    model = genai.GenerativeModel("gemini-2.5-pro-vision")
    response = model.generate_content(
        [prompt, {"mime_type": mime_type, "data": image_bytes}]
    )
    return response.text.strip()

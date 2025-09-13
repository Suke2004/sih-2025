import aiofiles
from fastapi import APIRouter, UploadFile, File, Form
from fastapi.responses import JSONResponse
from services.gemini_service import analyze_image_with_gemini
from services.tts_service import generate_speech

router = APIRouter()

# Load system prompt from file
with open("app/prompts/system_prompt.txt", "r", encoding="utf-8") as f:
    SYSTEM_PROMPT = f.read()

@router.post("/analyze-image/")
async def analyze_image(file: UploadFile = File(...), language: str = Form("English")):
    # Save uploaded file in memory
    image_bytes = await file.read()

    # Build system prompt
    system_prompt = SYSTEM_PROMPT.replace("{LANGUAGE}", language)

    # Gemini Vision API call
    text_response = analyze_image_with_gemini(image_bytes, system_prompt, file.content_type)

    # Generate audio with Coqui
    audio_file = generate_speech(text_response)

    return JSONResponse({
        "text": text_response,
        "audio_url": f"/get-audio/{audio_file}"
    })

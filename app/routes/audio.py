import os
from fastapi import APIRouter
from fastapi.responses import FileResponse

router = APIRouter()

@router.get("/get-audio/{filename}")
async def get_audio(filename: str):
    if os.path.exists(filename):
        return FileResponse(filename, media_type="audio/wav")
    return {"error": "File not found"}

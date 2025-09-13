from fastapi import FastAPI
from routes import analyse, audio

app = FastAPI(title="Vision + TTS Backend")

# Register routes
app.include_router(analyse.router)
app.include_router(audio.router)

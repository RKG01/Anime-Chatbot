from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from transformers import pipeline
import base64

# === MongoDB setup ===
from app.models import generate_reply
from app.db import messages_collection

# === FastAPI App ===
app = FastAPI(title="AI Chat + TTS API")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # you can restrict later
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =====================
# Chat Models & Routes
# =====================
@app.post("/chat")
def chat(user_message: dict):
    """
    Chat with the AI bot.
    Stores user + bot messages in MongoDB.
    """
    text = user_message.get("text", "")
    user_id = user_message.get("user_id", "guest")

    bot_reply = generate_reply(user_id, text)
    return {"reply": bot_reply}


@app.post("/clear")
def clear_chat(user: dict):
    """
    Clear chat history for a given user.
    """
    user_id = user.get("user_id", "guest")
    messages_collection.delete_many({"user_id": user_id})
    return {"status": "success", "message": f"Chat history cleared for {user_id}"}


@app.get("/history/{user_id}")
def get_history(user_id: str):
    """
    Fetch chat history for a given user.
    """
    messages = list(messages_collection.find({"user_id": user_id}).sort("_id", 1))
    history = [{"sender": m["sender"], "text": m["text"]} for m in messages]
    return {"history": history}


# =====================
# TTS Models & Routes
# =====================
# Load Hugging Face Anime TTS
tts = pipeline("text-to-speech", model="nyanko7/vits-anime2")

class TTSRequest(BaseModel):
    text: str

from fastapi.responses import StreamingResponse
import io
import soundfile as sf

@app.post("/tts")
def synthesize(req: TTSRequest):
    """
    Convert text into anime-style speech.
    Returns a .wav audio file stream.
    """
    speech = tts(req.text)
    audio_array = speech["audio"]

    # Save audio to buffer
    buffer = io.BytesIO()
    sf.write(buffer, audio_array, samplerate=speech["sampling_rate"], format="WAV")
    buffer.seek(0)

    return StreamingResponse(buffer, media_type="audio/wav")


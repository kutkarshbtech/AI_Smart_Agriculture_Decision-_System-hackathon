"""
Text-to-Speech endpoint using Amazon Polly.
Converts AI recommendations to audio for farmers.
"""
from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from io import BytesIO

router = APIRouter()


class TTSRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=3000)
    language: str = Field(default="hi", description="ISO 639-1 code (hi, en)")


@router.post("/synthesize")
async def synthesize_speech(req: TTSRequest):
    """
    Convert text to speech audio (MP3).
    Returns audio stream that can be played directly.
    Supports Hindi (Aditi) and English (Kajal) voices.
    """
    from app.services.polly_service import polly_service

    result = polly_service.synthesize_speech(
        text=req.text,
        language=req.language,
        output_format="mp3",
    )

    return StreamingResponse(
        BytesIO(result["audio_bytes"]),
        media_type=result["content_type"],
        headers={
            "Content-Disposition": "inline; filename=recommendation.mp3",
            "X-Voice-Id": result["voice_id"],
            "X-Language-Code": result["language_code"],
        },
    )


@router.get("/voices")
async def list_voices():
    """List available TTS voices for Indian languages."""
    from app.services.polly_service import VOICE_MAP
    return {
        "voices": {
            lang: {
                "voice_id": cfg["VoiceId"],
                "language_code": cfg["LanguageCode"],
                "engine": cfg["Engine"],
            }
            for lang, cfg in VOICE_MAP.items()
        }
    }

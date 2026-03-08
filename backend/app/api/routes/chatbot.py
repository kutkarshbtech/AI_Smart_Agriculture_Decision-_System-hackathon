"""
AI Chatbot endpoints.
Multilingual conversational interface for farmers.
Supports text and voice (speech-to-text via Amazon Transcribe).
"""
from fastapi import APIRouter, File, UploadFile, Form
from app.schemas.buyer_alert import ChatMessage, ChatResponse, VoiceChatResponse
from app.services.chatbot_service import chatbot_service

router = APIRouter()


@router.post("/message", response_model=ChatResponse)
async def send_message(chat: ChatMessage):
    """
    Send a message to the AI chatbot.
    Supports Hindi, English, and other Indian languages.
    """
    result = await chatbot_service.get_response(
        message=chat.message,
        language=chat.language,
        context=chat.context,
    )
    return result


@router.post("/voice", response_model=VoiceChatResponse)
async def send_voice_message(
    audio: UploadFile = File(..., description="Audio file (webm, wav, mp3, ogg)"),
    language: str = Form(default="hi", description="ISO 639-1 code or 'auto'"),
):
    """
    Send a voice message to the AI chatbot.
    The audio is transcribed via Amazon Transcribe, then passed to the chatbot.
    Supports Hindi, English, and other Indian languages.
    """
    from app.services.transcribe_service import transcribe_service

    # Read audio bytes
    audio_bytes = await audio.read()

    # Determine format from filename
    filename = audio.filename or "recording.webm"
    media_format = filename.rsplit(".", 1)[-1] if "." in filename else "webm"

    # Transcribe audio → text
    try:
        transcription = await transcribe_service.transcribe_audio(
            audio_bytes=audio_bytes,
            language=language,
            media_format=media_format,
        )
    except RuntimeError as e:
        error_msg = str(e)
        if "valid" in error_msg.lower() or "media" in error_msg.lower():
            return VoiceChatResponse(
                transcript="",
                transcript_confidence=0.0,
                detected_language="",
                reply="Sorry, the audio could not be processed. Please try recording again.",
                language=language if language != "auto" else "en",
                suggested_actions=["Try recording again", "Type your question instead"],
                sources=["Amazon Transcribe"],
            )
        raise

    transcript = transcription["transcript"]
    if not transcript.strip():
        return VoiceChatResponse(
            transcript="",
            transcript_confidence=0.0,
            detected_language=transcription["language_code"],
            reply="Sorry, I couldn't understand the audio. Please try again or type your question.",
            language=language if language != "auto" else "en",
            suggested_actions=[],
            sources=["Amazon Transcribe"],
        )

    # Map Transcribe language code back to our ISO 639-1
    detected = transcription["language_code"]  # e.g. "hi-IN"
    response_lang = detected.split("-")[0] if "-" in detected else language

    # Feed transcript to chatbot
    chat_result = await chatbot_service.get_response(
        message=transcript,
        language=response_lang,
    )

    return VoiceChatResponse(
        transcript=transcript,
        transcript_confidence=transcription["confidence"],
        detected_language=detected,
        reply=chat_result["reply"],
        language=chat_result["language"],
        suggested_actions=chat_result.get("suggested_actions", []),
        sources=["Amazon Transcribe"] + chat_result.get("sources", []),
    )


@router.get("/welcome")
async def get_welcome_message(language: str = "hi"):
    """Get a welcome/onboarding message for new users."""
    result = await chatbot_service.get_response(
        message="hello",
        language=language,
    )
    return result

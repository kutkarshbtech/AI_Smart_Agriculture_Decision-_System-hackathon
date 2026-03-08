"""
Text-to-Speech service using Amazon Polly.
Reads out AI recommendations to farmers in English and Hindi.
Uses Aditi (bilingual en-IN/hi-IN) and Kajal (neural en-IN) voices.
"""
from typing import Optional


# Voice configuration for Indian languages
VOICE_MAP = {
    "hi": {"VoiceId": "Aditi", "LanguageCode": "hi-IN", "Engine": "standard"},
    "en": {"VoiceId": "Kajal", "LanguageCode": "en-IN", "Engine": "neural"},
    # Fallback: Aditi can handle mixed Hindi-English text
    "mr": {"VoiceId": "Aditi", "LanguageCode": "hi-IN", "Engine": "standard"},
    "bn": {"VoiceId": "Aditi", "LanguageCode": "hi-IN", "Engine": "standard"},
    "gu": {"VoiceId": "Aditi", "LanguageCode": "hi-IN", "Engine": "standard"},
    "pa": {"VoiceId": "Aditi", "LanguageCode": "hi-IN", "Engine": "standard"},
}


class PollyService:
    """Text-to-Speech using Amazon Polly."""

    def synthesize_speech(
        self,
        text: str,
        language: str = "hi",
        output_format: str = "mp3",
    ) -> dict:
        """
        Convert text to speech audio.

        Args:
            text: Text to speak (max ~3000 chars for Polly).
            language: ISO 639-1 code (hi, en, etc.).
            output_format: mp3, ogg_vorbis, or pcm.

        Returns:
            dict with 'audio_bytes', 'content_type', 'voice_id'.
        """
        from app.core.aws_clients import get_polly_client

        client = get_polly_client()

        # Pick voice config
        voice_config = VOICE_MAP.get(language, VOICE_MAP["hi"])

        # Truncate very long text (Polly limit is ~3000 chars)
        if len(text) > 2900:
            text = text[:2900] + "..."

        response = client.synthesize_speech(
            Text=text,
            VoiceId=voice_config["VoiceId"],
            LanguageCode=voice_config["LanguageCode"],
            Engine=voice_config["Engine"],
            OutputFormat=output_format,
        )

        audio_bytes = response["AudioStream"].read()

        content_types = {
            "mp3": "audio/mpeg",
            "ogg_vorbis": "audio/ogg",
            "pcm": "audio/pcm",
        }

        return {
            "audio_bytes": audio_bytes,
            "content_type": content_types.get(output_format, "audio/mpeg"),
            "voice_id": voice_config["VoiceId"],
            "language_code": voice_config["LanguageCode"],
        }


polly_service = PollyService()

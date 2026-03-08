"""
Speech-to-Text service using Amazon Transcribe.
Converts farmer voice messages to text for the chatbot.
Supports Hindi, English, and other Indian languages.
"""
import json
import time
import uuid
from typing import Optional

from app.core.config import settings


# Language code mapping: our ISO 639-1 codes → Transcribe language codes
TRANSCRIBE_LANGUAGE_MAP = {
    "hi": "hi-IN",
    "en": "en-IN",  # Indian English
    "mr": "mr-IN",
    "ta": "ta-IN",
    "te": "te-IN",
    "bn": "bn-IN",
    "gu": "gu-IN",
    "kn": "kn-IN",
    "pa": "pa-IN",
    "ml": "ml-IN",
}

# Supported media formats
SUPPORTED_FORMATS = {"wav", "mp3", "ogg", "webm", "flac", "m4a", "mp4"}


class TranscribeService:
    """Speech-to-text using Amazon Transcribe (batch mode via S3)."""

    async def transcribe_audio(
        self,
        audio_bytes: bytes,
        language: str = "hi",
        media_format: str = "webm",
    ) -> dict:
        """
        Transcribe an audio clip to text.

        Args:
            audio_bytes: Raw audio file bytes.
            language: ISO 639-1 language code (hi, en, etc.).
            media_format: Audio format (webm, wav, mp3, ogg, etc.).

        Returns:
            dict with 'transcript', 'language_code', and 'confidence'.
        """
        from app.core.aws_clients import get_s3_client, get_transcribe_client

        # S3 client must use the same region as the Transcribe bucket
        s3 = get_s3_client(region_name=settings.TRANSCRIBE_REGION)
        transcribe = get_transcribe_client()

        # Normalize format
        fmt = media_format.lower().replace(".", "")
        if fmt not in SUPPORTED_FORMATS:
            fmt = "webm"  # default for browser recordings

        # Upload audio to S3
        job_id = f"swadesh-voice-{uuid.uuid4().hex[:12]}"
        s3_key = f"{settings.TRANSCRIBE_S3_PREFIX}{job_id}.{fmt}"
        bucket = settings.TRANSCRIBE_S3_BUCKET

        s3.put_object(
            Bucket=bucket,
            Key=s3_key,
            Body=audio_bytes,
            ContentType=f"audio/{fmt}",
        )

        try:
            # Build Transcribe job params
            transcribe_lang = TRANSCRIBE_LANGUAGE_MAP.get(language, "hi-IN")
            media_uri = f"s3://{bucket}/{s3_key}"

            job_params = {
                "TranscriptionJobName": job_id,
                "Media": {"MediaFileUri": media_uri},
                "MediaFormat": fmt if fmt != "m4a" else "mp4",
                "LanguageCode": transcribe_lang,
                "Settings": {
                    "ShowSpeakerLabels": False,
                },
            }

            # If language is uncertain, use auto-detection across Indian languages
            if language == "auto":
                del job_params["LanguageCode"]
                job_params["IdentifyLanguage"] = True
                job_params["LanguageOptions"] = [
                    "hi-IN", "en-IN", "ta-IN", "te-IN",
                    "bn-IN", "mr-IN", "gu-IN", "kn-IN",
                ]

            # Start transcription job
            transcribe.start_transcription_job(**job_params)

            # Poll until complete (short audio typically finishes in 5-15s)
            transcript_text = ""
            confidence = 0.0
            detected_lang = transcribe_lang

            for _ in range(30):  # max ~30 seconds
                time.sleep(1)
                status = transcribe.get_transcription_job(
                    TranscriptionJobName=job_id
                )
                job = status["TranscriptionJob"]

                if job["TranscriptionJobStatus"] == "COMPLETED":
                    # Fetch transcript from the result URI
                    import urllib.request
                    result_uri = job["Transcript"]["TranscriptFileUri"]
                    with urllib.request.urlopen(result_uri) as resp:
                        result = json.loads(resp.read().decode())

                    transcript_text = (
                        result.get("results", {})
                        .get("transcripts", [{}])[0]
                        .get("transcript", "")
                    )

                    # Get average confidence from items
                    items = result.get("results", {}).get("items", [])
                    confidences = [
                        float(item["alternatives"][0].get("confidence", 0))
                        for item in items
                        if item.get("alternatives")
                        and item["alternatives"][0].get("confidence")
                    ]
                    confidence = (
                        sum(confidences) / len(confidences) if confidences else 0.0
                    )

                    # Detected language (if auto-detect was used)
                    detected_lang = job.get("LanguageCode", transcribe_lang)
                    break

                elif job["TranscriptionJobStatus"] == "FAILED":
                    reason = job.get("FailureReason", "Unknown error")
                    raise RuntimeError(f"Transcription failed: {reason}")

            else:
                raise RuntimeError("Transcription timed out (30s)")

            return {
                "transcript": transcript_text,
                "language_code": detected_lang,
                "confidence": round(confidence, 3),
            }

        finally:
            # Clean up: delete S3 object and Transcribe job
            try:
                s3.delete_object(Bucket=bucket, Key=s3_key)
            except Exception:
                pass
            try:
                transcribe.delete_transcription_job(TranscriptionJobName=job_id)
            except Exception:
                pass


transcribe_service = TranscribeService()

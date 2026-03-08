# AI Chatbot API

**Prefix:** `/api/v1/chatbot`

Multilingual conversational AI for agricultural advice. Powered by Amazon Bedrock (Claude) with rule-based Hindi fallback. Supports text and voice input via Amazon Transcribe.

---

## `POST /api/v1/chatbot/message`

Send a text message to the AI chatbot.

### Request Body

```json
{
  "message": "मेरे टमाटर का भाव क्या है?",
  "language": "hi",
  "context": {
    "crop_name": "tomato",
    "location": "Pune"
  }
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `message` | string | ✅ | User's question |
| `language` | string | ❌ | ISO 639-1 code: `hi`, `en`, `ta`, `bn`, etc. (default: `hi`) |
| `context` | object | ❌ | Optional crop/location context for personalized advice |

### Response

```json
{
  "reply": "आपके टमाटर का आज का भाव ₹25/kg है। बाजार में कीमतें बढ़ रही हैं, 2 दिन इंतजार करें।",
  "language": "hi",
  "suggested_actions": [
    "Check mandi prices",
    "Assess quality",
    "Find buyers"
  ],
  "sources": ["Amazon Bedrock"]
}
```

### Supported Languages

| Code | Language |
|------|----------|
| `hi` | Hindi |
| `en` | English |
| `ta` | Tamil |
| `bn` | Bengali |
| `te` | Telugu |
| `mr` | Marathi |
| `gu` | Gujarati |
| `kn` | Kannada |
| `ml` | Malayalam |

---

## `POST /api/v1/chatbot/voice`

Send a voice message. Audio is transcribed via Amazon Transcribe, then passed to the chatbot.

### Request

`multipart/form-data`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `audio` | file | ✅ | Audio file (webm, wav, mp3, ogg) |
| `language` | string | ❌ | ISO 639-1 code or `auto` (default: `hi`) |

```bash
curl -X POST "/api/v1/chatbot/voice" \
  -F "audio=@recording.webm" \
  -F "language=hi"
```

### Response

```json
{
  "transcript": "मेरे आलू कब बेचूं?",
  "transcript_confidence": 0.92,
  "detected_language": "hi-IN",
  "reply": "आपके आलू अगले 5 दिन तक ताजे रहेंगे। कीमतें बढ़ रही हैं — 2 दिन और रुकें।",
  "language": "hi",
  "suggested_actions": ["Check price forecast", "Find cold storage"],
  "sources": ["Amazon Transcribe", "Amazon Bedrock"]
}
```

---

## `GET /api/v1/chatbot/welcome`

Get a welcome/onboarding message for new users.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `language` | string | `hi` | Language code |

```
GET /api/v1/chatbot/welcome?language=en
```

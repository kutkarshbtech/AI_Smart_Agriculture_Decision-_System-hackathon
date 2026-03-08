# Text-to-Speech API

**Prefix:** `/api/v1/tts`

Amazon Polly-powered text-to-speech for reading AI recommendations aloud. Uses high-quality Indian voices so farmers can listen instead of read.

---

## `POST /api/v1/tts/synthesize`

Convert text to speech audio (MP3). Returns an audio stream that can be played directly in the browser.

### Request Body

```json
{
  "text": "Your tomatoes are in excellent condition. Sell at ₹28/kg for best returns.",
  "language": "en"
}
```

| Field | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| `text` | string | ✅ | 1–3000 chars | Text to convert to speech |
| `language` | string | ❌ | — | `en` (English) or `hi` (Hindi). Default: `hi` |

### Response

**Content-Type:** `audio/mpeg`

Returns raw MP3 audio bytes as a streaming response. Headers include:

| Header | Description |
|--------|-------------|
| `Content-Disposition` | `inline; filename=recommendation.mp3` |
| `X-Voice-Id` | Polly voice used (e.g., `Kajal`) |
| `X-Language-Code` | Language code (e.g., `en-IN`) |

### Usage Example (JavaScript)

```javascript
const response = await axios.post('/api/v1/tts/synthesize', {
  text: 'Your produce is in good condition.',
  language: 'en'
}, { responseType: 'blob' });

const audioUrl = URL.createObjectURL(response.data);
const audio = new Audio(audioUrl);
audio.play();
```

### Usage Example (curl)

```bash
curl -X POST "/api/v1/tts/synthesize" \
  -H "Content-Type: application/json" \
  -d '{"text": "आपके टमाटर उत्कृष्ट हैं।", "language": "hi"}' \
  --output recommendation.mp3
```

---

## `GET /api/v1/tts/voices`

List available TTS voices for Indian languages.

### Response

```json
{
  "voices": {
    "en": {
      "voice_id": "Kajal",
      "language_code": "en-IN",
      "engine": "neural"
    },
    "hi": {
      "voice_id": "Aditi",
      "language_code": "hi-IN",
      "engine": "standard"
    }
  }
}
```

### Voice Details

| Language | Voice | Engine | Quality |
|----------|-------|--------|---------|
| English (Indian) | **Kajal** | Neural | High-quality, natural-sounding |
| Hindi | **Aditi** | Standard | Clear Hindi pronunciation |

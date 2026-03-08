"""
AI Chatbot service using Amazon Bedrock (Converse API).
Provides multilingual conversational interface for farmers.
Works with any Bedrock model (Nova Lite, Claude, etc.).
"""
import json
from typing import Dict, Any, List, Optional
from app.core.config import settings


# System prompt for the agricultural AI assistant
SYSTEM_PROMPT = """You are SwadeshAI, a helpful agricultural assistant for Indian farmers.
You help farmers with post-harvest decisions including:
- When and where to sell their produce
- How to store produce properly to reduce spoilage
- Understanding market prices and trends
- Connecting with local buyers
- Weather impact on their crops

IMPORTANT GUIDELINES:
- Respond in the language the farmer uses (Hindi, English, or regional languages)
- Keep responses simple, practical, and actionable
- Use familiar agricultural terminology
- Always prioritize the farmer's economic interest
- Provide specific numbers (prices, days, percentages) when available
- Be encouraging and supportive

If you're asked about something outside agriculture, politely redirect to farm-related topics."""


class ChatbotService:
    """AI chatbot powered by Amazon Bedrock."""

    async def get_response(
        self,
        message: str,
        language: str = "hi",
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Process a farmer's message and generate an AI response.
        Tries Bedrock first, falls back to rule-based response.
        In AWS_ONLY mode, Bedrock failure raises an error (no fallback).
        """
        try:
            return await self._bedrock_response(message, language, context)
        except Exception as e:
            if settings.AWS_ONLY:
                raise RuntimeError(
                    f"AWS_ONLY mode: Bedrock failed ({e}). "
                    "Rule-based fallback is disabled."
                )
            print(f"Bedrock unavailable ({e}), using rule-based fallback")
            return self._rule_based_response(message, language, context)

    async def _bedrock_response(
        self, message: str, language: str, context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Generate response using Amazon Bedrock Converse API (works with any model)."""
        from app.core.aws_clients import get_bedrock_runtime

        client = get_bedrock_runtime()

        # Build context-enriched prompt
        context_str = ""
        if context:
            context_str = f"\n\nCurrent farmer context: {json.dumps(context, default=str)}"

        lang_instruction = {
            "hi": "Respond in Hindi (Devanagari script).",
            "en": "Respond in English.",
            "mr": "Respond in Marathi.",
            "ta": "Respond in Tamil.",
            "te": "Respond in Telugu.",
            "bn": "Respond in Bengali.",
            "gu": "Respond in Gujarati.",
            "kn": "Respond in Kannada.",
            "pa": "Respond in Punjabi.",
        }.get(language, "Respond in Hindi.")

        system_text = f"{SYSTEM_PROMPT}\n\n{lang_instruction}{context_str}"

        response = client.converse(
            modelId=settings.BEDROCK_MODEL_ID,
            system=[{"text": system_text}],
            messages=[
                {
                    "role": "user",
                    "content": [{"text": message}],
                }
            ],
            inferenceConfig={
                "maxTokens": 500,
                "temperature": 0.7,
            },
        )

        reply_text = response["output"]["message"]["content"][0]["text"]

        # Extract suggested actions from the response
        suggested_actions = self._extract_actions(reply_text, context)

        return {
            "reply": reply_text,
            "language": language,
            "suggested_actions": suggested_actions,
            "sources": [f"Amazon Bedrock ({settings.BEDROCK_MODEL_ID})"],
        }

    def _rule_based_response(
        self, message: str, language: str, context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Fallback rule-based responses for common queries."""
        msg_lower = message.lower()

        # Pattern matching for common farmer queries
        responses = {
            "hi": self._get_hindi_response(msg_lower, context),
            "en": self._get_english_response(msg_lower, context),
        }

        response_data = responses.get(language, responses["en"])

        return {
            "reply": response_data["reply"],
            "language": language,
            "suggested_actions": response_data.get("actions", []),
            "sources": ["rule-based"],
        }

    def _get_english_response(
        self, msg: str, context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """English rule-based responses."""
        if any(w in msg for w in ["price", "rate", "cost", "sell"]):
            return {
                "reply": "I can help you find the best price for your produce! "
                         "Please upload your produce details or tell me what crop you want to sell, "
                         "and I'll check today's market prices and recommend the best selling strategy.",
                "actions": [
                    {"type": "navigate", "label": "Check Market Prices", "target": "pricing"},
                    {"type": "navigate", "label": "Find Buyers", "target": "buyers"},
                ],
            }
        elif any(w in msg for w in ["spoil", "rot", "fresh", "shelf life", "storage"]):
            return {
                "reply": "To help assess spoilage risk, I need to know:\n"
                         "1. What crop do you have?\n"
                         "2. When was it harvested?\n"
                         "3. How is it currently stored?\n\n"
                         "You can also upload a photo for quality assessment!",
                "actions": [
                    {"type": "navigate", "label": "Check Spoilage Risk", "target": "spoilage"},
                    {"type": "action", "label": "Upload Photo", "target": "quality_check"},
                ],
            }
        elif any(w in msg for w in ["weather", "rain", "temperature"]):
            return {
                "reply": "I can check the weather for your location and tell you how it affects "
                         "your stored produce. Share your location or city name to get started.",
                "actions": [
                    {"type": "action", "label": "Check Weather", "target": "weather"},
                ],
            }
        elif any(w in msg for w in ["buyer", "shop", "market", "mandi"]):
            return {
                "reply": "I can connect you with verified buyers near your location! "
                         "Tell me your crop type and quantity, and I'll find the best matches.",
                "actions": [
                    {"type": "navigate", "label": "Find Buyers", "target": "buyers"},
                ],
            }
        elif any(w in msg for w in ["hello", "hi", "help", "start"]):
            return {
                "reply": "Welcome to SwadeshAI! 🌾 I'm here to help you:\n\n"
                         "• Get the best price for your produce\n"
                         "• Check spoilage risk and storage advice\n"
                         "• Find nearby buyers and shops\n"
                         "• Understand weather impact on your crops\n\n"
                         "What would you like to do today?",
                "actions": [
                    {"type": "navigate", "label": "Check Prices", "target": "pricing"},
                    {"type": "navigate", "label": "Assess Quality", "target": "quality_check"},
                    {"type": "navigate", "label": "Find Buyers", "target": "buyers"},
                ],
            }
        else:
            return {
                "reply": "I can help you with:\n"
                         "• Market prices & selling advice\n"
                         "• Spoilage risk assessment\n"
                         "• Finding nearby buyers\n"
                         "• Weather-based storage tips\n\n"
                         "Please ask me about any of these topics!",
                "actions": [],
            }

    def _get_hindi_response(
        self, msg: str, context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Hindi rule-based responses (transliterated keywords)."""
        if any(w in msg for w in ["price", "bhav", "daam", "rate", "bech", "sell", "कीमत", "भाव", "दाम", "बेच"]):
            return {
                "reply": "मैं आपकी फसल के लिए सबसे अच्छी कीमत खोजने में मदद कर सकता हूं! "
                         "कृपया अपनी फसल का नाम और मात्रा बताएं, "
                         "मैं आज की मंडी कीमतें देखकर आपको बेहतरीन सलाह दूंगा।",
                "actions": [
                    {"type": "navigate", "label": "मंडी भाव देखें", "target": "pricing"},
                    {"type": "navigate", "label": "खरीदार खोजें", "target": "buyers"},
                ],
            }
        elif any(w in msg for w in ["kharab", "sada", "taza", "storage", "खराब", "सड़ा", "ताज़ा"]):
            return {
                "reply": "खराब होने का खतरा जानने के लिए बताएं:\n"
                         "1. कौन सी फसल है?\n"
                         "2. कब काटी गई?\n"
                         "3. कैसे रखी है?\n\n"
                         "फोटो भेजकर भी गुणवत्ता जांच करा सकते हैं!",
                "actions": [
                    {"type": "navigate", "label": "खराबी जांचें", "target": "spoilage"},
                    {"type": "action", "label": "फोटो भेजें", "target": "quality_check"},
                ],
            }
        elif any(w in msg for w in ["hello", "hi", "namaste", "help", "madad", "नमस्ते", "मदद"]):
            return {
                "reply": "स्वदेशAI में आपका स्वागत है! 🌾 मैं आपकी मदद कर सकता हूं:\n\n"
                         "• अपनी फसल का सही दाम जानें\n"
                         "• खराब होने का खतरा जांचें\n"
                         "• नज़दीकी खरीदार खोजें\n"
                         "• मौसम की जानकारी पाएं\n\n"
                         "आज आप क्या करना चाहेंगे?",
                "actions": [
                    {"type": "navigate", "label": "मंडी भाव", "target": "pricing"},
                    {"type": "navigate", "label": "गुणवत्ता जांच", "target": "quality_check"},
                    {"type": "navigate", "label": "खरीदार खोजें", "target": "buyers"},
                ],
            }
        else:
            return {
                "reply": "मैं इन विषयों में आपकी मदद कर सकता हूं:\n"
                         "• मंडी भाव और बिक्री सलाह\n"
                         "• खराबी का खतरा\n"
                         "• नज़दीकी खरीदार\n"
                         "• मौसम आधारित भंडारण सुझाव\n\n"
                         "कृपया इनमें से किसी भी विषय पर पूछें!",
                "actions": [],
            }

    def _extract_actions(
        self, reply: str, context: Optional[Dict] = None
    ) -> List[Dict[str, Any]]:
        """Extract suggested actions from the AI response."""
        actions = []
        reply_lower = reply.lower()

        if any(w in reply_lower for w in ["price", "sell", "market", "कीमत", "बेच"]):
            actions.append({"type": "navigate", "label": "Check Prices", "target": "pricing"})
        if any(w in reply_lower for w in ["buyer", "shop", "खरीदार"]):
            actions.append({"type": "navigate", "label": "Find Buyers", "target": "buyers"})
        if any(w in reply_lower for w in ["spoil", "storage", "cold", "खराब"]):
            actions.append({"type": "navigate", "label": "Storage Advice", "target": "spoilage"})

        return actions[:3]  # Max 3 suggested actions


# Singleton
chatbot_service = ChatbotService()

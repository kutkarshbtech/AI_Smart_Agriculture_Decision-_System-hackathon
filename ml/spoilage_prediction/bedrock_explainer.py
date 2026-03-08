"""
Causal Explanation Engine powered by Amazon Bedrock (Claude).

This is a key deck feature: "Causal Explanation Engine (Explainable AI)"
— explains WHY a recommendation is given using LLM-powered reasoning.

Capabilities:
    - Rich causal explanations in Hindi + English
    - "What-if" scenario analysis (e.g., "if you move to cold storage...")
    - Farmer-friendly language (low digital literacy)
    - Feature importance narrative from XGBoost model
    - Graceful fallback to template-based explanations when Bedrock is unavailable

AWS Services:
    - Amazon Bedrock (Claude) for explanation generation
    - Follows same Bedrock invocation pattern as chatbot_service.py

Usage:
    from bedrock_explainer import BedrockExplainer

    explainer = BedrockExplainer()
    explanation = explainer.explain(prediction_result)
    whatif = explainer.whatif_analysis(prediction_result, changes={"storage_type": "cold"})
"""

import os
import json
from typing import Dict, Any, Optional, List

from dataset import CROP_PROFILES, CROP_NAMES, RISK_LEVELS


# ── Bedrock Configuration ───────────────────────────────────────────

BEDROCK_REGION = os.environ.get("BEDROCK_REGION", "ap-south-1")
BEDROCK_MODEL_ID = os.environ.get(
    "BEDROCK_MODEL_ID", "amazon.nova-lite-v1:0"
)

# ── Prompts ─────────────────────────────────────────────────────────

EXPLANATION_SYSTEM_PROMPT = """You are SwadeshAI's Causal Explanation Engine — an agricultural AI expert
that explains spoilage predictions to Indian farmers in simple, clear language.

Your job is to translate ML model predictions into actionable causal explanations
that a farmer with basic literacy can understand.

RULES:
1. Explain WHY the prediction is what it is using cause → effect reasoning
2. Use specific numbers (temperature, days, percentages)
3. Compare current conditions to optimal conditions
4. Mention the Q10 rule in simple terms: "For every 10°C above optimal, spoilage doubles"
5. Explain what the farmer CAN control vs what they CANNOT
6. Always end with 1-2 specific actionable recommendations
7. Keep explanations under 150 words per language
8. Use familiar agricultural terms, not technical jargon"""

EXPLANATION_USER_TEMPLATE = """Generate a causal explanation for this spoilage prediction.
Provide the explanation in BOTH English AND Hindi (Devanagari script).

PREDICTION DATA:
- Crop: {crop} ({crop_hindi})
- Risk Level: {risk_level} ({risk_icon})
- Spoilage Probability: {spoilage_prob:.1%}
- Remaining Shelf Life: {remaining_days:.0f} days
- Storage Type: {storage_type}

CURRENT CONDITIONS:
- Temperature: {temperature}°C (Optimal: {opt_temp_min}–{opt_temp_max}°C)
- Humidity: {humidity}% (Optimal: {opt_hum_min}–{opt_hum_max}%)
- Days Since Harvest: {days_since_harvest}
- Transport Time: {transport_hours} hours
- Initial Quality: {initial_quality}/100

KEY RISK FACTORS FROM MODEL:
{risk_factors}

MODEL FEATURE IMPORTANCE (top factors for this prediction):
{feature_importance}

Respond in this exact JSON format:
{{
    "en": "English explanation here...",
    "hi": "Hindi explanation here...",
    "key_causes": ["cause1", "cause2", "cause3"],
    "controllable_factors": ["factor1", "factor2"],
    "uncontrollable_factors": ["factor1"]
}}"""

WHATIF_SYSTEM_PROMPT = """You are SwadeshAI's What-If Analysis Engine.
Given a farmer's current spoilage prediction and a proposed change,
explain what would happen if they made that change.

Be specific with numbers. Compare before vs after.
Respond in both English and Hindi."""

WHATIF_USER_TEMPLATE = """A farmer has this current spoilage prediction:
- Crop: {crop} ({crop_hindi})
- Current Risk: {current_risk} (Probability: {current_prob:.1%})
- Remaining Life: {current_remaining:.0f} days

Current conditions: {current_conditions}

PROPOSED CHANGE: {proposed_change}

After the change, the model predicts:
- New Risk: {new_risk} (Probability: {new_prob:.1%})
- New Remaining Life: {new_remaining:.0f} days

Explain the impact of this change to the farmer in both English and Hindi.
Be specific about improvement/worsening.

Respond in JSON format:
{{
    "en": "English what-if explanation...",
    "hi": "Hindi what-if explanation...",
    "improvement": true/false,
    "impact_summary": "brief one-line summary"
}}"""


class BedrockExplainer:
    """
    LLM-powered causal explanation engine using Amazon Bedrock.

    Generates rich, contextual, farmer-friendly explanations for
    spoilage predictions. Falls back to template-based explanations
    when Bedrock is unavailable.
    """

    def __init__(
        self,
        region: str = None,
        model_id: str = None,
        max_tokens: int = 800,
    ):
        self.region = region or BEDROCK_REGION
        self.model_id = model_id or BEDROCK_MODEL_ID
        self.max_tokens = max_tokens
        self._client = None
        self._bedrock_available = None

    def _get_client(self):
        """Lazy-initialize Bedrock client."""
        if self._client is None:
            try:
                import boto3
                session = boto3.Session(region_name=self.region)
                self._client = session.client("bedrock-runtime", region_name=self.region)
                self._bedrock_available = True
            except Exception as e:
                print(f"Bedrock client initialization failed: {e}")
                self._bedrock_available = False
        return self._client

    def _invoke_bedrock(self, system_prompt: str, user_message: str) -> str:
        """Invoke Bedrock via Converse API and return the response text."""
        client = self._get_client()
        if not client:
            raise RuntimeError("Bedrock client not available")

        response = client.converse(
            modelId=self.model_id,
            system=[{"text": system_prompt}],
            messages=[
                {
                    "role": "user",
                    "content": [{"text": user_message}],
                }
            ],
            inferenceConfig={
                "maxTokens": self.max_tokens,
                "temperature": 0.3,
            },
        )

        return response["output"]["message"]["content"][0]["text"]

    def _parse_json_response(self, response_text: str) -> Dict[str, Any]:
        """Extract JSON from LLM response (handles markdown code blocks)."""
        text = response_text.strip()

        # Try direct parse
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # Try extracting from markdown code block
        if "```json" in text:
            start = text.index("```json") + 7
            end = text.index("```", start)
            return json.loads(text[start:end].strip())

        if "```" in text:
            start = text.index("```") + 3
            end = text.index("```", start)
            return json.loads(text[start:end].strip())

        # Try finding JSON object
        start = text.index("{")
        end = text.rindex("}") + 1
        return json.loads(text[start:end])

    def explain(
        self,
        prediction: Dict[str, Any],
        feature_importance: Optional[Dict[str, float]] = None,
    ) -> Dict[str, Any]:
        """
        Generate a causal explanation for a spoilage prediction.

        Args:
            prediction: Output from SpoilagePredictor.predict()
            feature_importance: Optional feature importance dict from model

        Returns:
            Dict with 'en', 'hi' explanations, key_causes, controllable factors, source
        """
        try:
            return self._bedrock_explain(prediction, feature_importance)
        except Exception as e:
            print(f"Bedrock explanation failed ({e}), using template fallback")
            return self._template_explain(prediction)

    def _bedrock_explain(
        self,
        prediction: Dict[str, Any],
        feature_importance: Optional[Dict[str, float]] = None,
    ) -> Dict[str, Any]:
        """Generate explanation using Bedrock Claude."""
        inp = prediction["input_summary"]
        crop = prediction["crop"]
        profile = CROP_PROFILES[crop]

        # Build risk factors string
        risk_factors = []
        opt_temp = profile["optimal_temp"]
        opt_hum = profile["optimal_humidity"]

        if inp["temperature_c"] > opt_temp[1]:
            delta = inp["temperature_c"] - opt_temp[1]
            risk_factors.append(
                f"Temperature is {delta:.0f}°C above optimal — "
                f"Q10 rule: spoilage rate ~{2**(delta/10):.1f}x normal"
            )
        elif inp["temperature_c"] < opt_temp[0] and inp["temperature_c"] >= 0:
            risk_factors.append(
                f"Temperature {inp['temperature_c']}°C is below optimal — chilling injury risk"
            )

        if inp["humidity_pct"] < opt_hum[0]:
            risk_factors.append(
                f"Humidity {inp['humidity_pct']}% is below optimal {opt_hum[0]}% — moisture loss/wilting"
            )
        elif inp["humidity_pct"] > opt_hum[1]:
            risk_factors.append(
                f"Humidity {inp['humidity_pct']}% exceeds optimal {opt_hum[1]}% — mold growth risk"
            )

        if inp["transport_hours"] > 4:
            risk_factors.append(
                f"Transport of {inp['transport_hours']}h causes mechanical damage "
                f"(sensitivity: {profile['damage_sensitivity']:.0%})"
            )

        risk_str = "\n".join(f"- {r}" for r in risk_factors) if risk_factors else "- No major deviations"

        # Feature importance string
        if feature_importance:
            fi_str = "\n".join(
                f"- {k}: {v:.4f}" for k, v in list(feature_importance.items())[:5]
            )
        else:
            fi_str = "- Not available for this prediction"

        user_msg = EXPLANATION_USER_TEMPLATE.format(
            crop=crop,
            crop_hindi=prediction["crop_hindi"],
            risk_level=prediction["risk_level"],
            risk_icon=prediction["risk_icon"],
            spoilage_prob=prediction["spoilage_probability"],
            remaining_days=prediction["remaining_shelf_life_days"],
            storage_type=inp["storage_type"],
            temperature=inp["temperature_c"],
            opt_temp_min=opt_temp[0],
            opt_temp_max=opt_temp[1],
            humidity=inp["humidity_pct"],
            opt_hum_min=opt_hum[0],
            opt_hum_max=opt_hum[1],
            days_since_harvest=inp["days_since_harvest"],
            transport_hours=inp["transport_hours"],
            initial_quality=inp.get("initial_quality", 85),
            risk_factors=risk_str,
            feature_importance=fi_str,
        )

        response_text = self._invoke_bedrock(EXPLANATION_SYSTEM_PROMPT, user_msg)
        parsed = self._parse_json_response(response_text)

        return {
            "en": parsed.get("en", ""),
            "hi": parsed.get("hi", ""),
            "key_causes": parsed.get("key_causes", []),
            "controllable_factors": parsed.get("controllable_factors", []),
            "uncontrollable_factors": parsed.get("uncontrollable_factors", []),
            "source": "Amazon Bedrock (Claude)",
        }

    def _template_explain(self, prediction: Dict[str, Any]) -> Dict[str, Any]:
        """Template-based fallback when Bedrock is unavailable."""
        inp = prediction["input_summary"]
        crop = prediction["crop"]
        profile = CROP_PROFILES[crop]
        hindi_name = prediction["crop_hindi"]
        opt_temp = profile["optimal_temp"]
        opt_hum = profile["optimal_humidity"]
        remaining = prediction["remaining_shelf_life_days"]
        risk = prediction["risk_level"]

        parts_en = []
        parts_hi = []
        key_causes = []
        controllable = []
        uncontrollable = []

        # Harvest age
        days = inp["days_since_harvest"]
        parts_en.append(f"Your {crop} batch was harvested {days} day(s) ago.")
        parts_hi.append(f"आपकी {hindi_name} की खेप {days} दिन पहले काटी गई थी।")
        uncontrollable.append("harvest_age")

        # Remaining shelf life
        parts_en.append(f"Estimated remaining shelf life: {remaining:.0f} days.")
        parts_hi.append(f"अनुमानित बची हुई शेल्फ लाइफ: {remaining:.0f} दिन।")

        # Temperature
        temp = inp["temperature_c"]
        if temp > opt_temp[1]:
            delta = temp - opt_temp[1]
            factor = 2 ** (delta / 10)
            parts_en.append(
                f"Storage temperature ({temp}°C) is {delta:.0f}°C above optimal "
                f"({opt_temp[0]}–{opt_temp[1]}°C). "
                f"By the Q10 rule, spoilage rate is ~{factor:.1f}x faster than normal."
            )
            parts_hi.append(
                f"भंडारण तापमान ({temp}°C) इष्टतम ({opt_temp[0]}–{opt_temp[1]}°C) से "
                f"{delta:.0f}°C अधिक है। Q10 नियम के अनुसार, खराबी ~{factor:.1f} गुना तेज़ है।"
            )
            key_causes.append(f"Temperature {delta:.0f}°C above optimal")
            controllable.append("storage_temperature")
        elif temp < opt_temp[0] and temp >= 0:
            parts_en.append(
                f"Temperature ({temp}°C) is below optimal — risk of chilling injury."
            )
            parts_hi.append(
                f"तापमान ({temp}°C) इष्टतम से कम है — ठंड से नुकसान का ख़तरा।"
            )
            key_causes.append("Temperature below optimal (chilling risk)")
            controllable.append("storage_temperature")

        # Humidity
        hum = inp["humidity_pct"]
        if hum < opt_hum[0]:
            parts_en.append(
                f"Humidity ({hum}%) is below optimal ({opt_hum[0]}–{opt_hum[1]}%), "
                f"causing moisture loss and wilting."
            )
            parts_hi.append(
                f"नमी ({hum}%) इष्टतम ({opt_hum[0]}–{opt_hum[1]}%) से कम है, "
                f"जिससे नमी खोने और मुरझाने का ख़तरा है।"
            )
            key_causes.append("Low humidity causing moisture loss")
            controllable.append("humidity")
        elif hum > opt_hum[1]:
            parts_en.append(
                f"Humidity ({hum}%) exceeds optimal ({opt_hum[0]}–{opt_hum[1]}%), "
                f"promoting mold and bacterial growth."
            )
            parts_hi.append(
                f"नमी ({hum}%) इष्टतम ({opt_hum[0]}–{opt_hum[1]}%) से अधिक है, "
                f"जिससे फफूंद और बैक्टीरिया बढ़ सकते हैं।"
            )
            key_causes.append("High humidity promoting mold")
            controllable.append("humidity")

        # Transport
        transport = inp["transport_hours"]
        if transport > 4:
            parts_en.append(f"Transit time of {transport:.0f} hours adds mechanical stress.")
            parts_hi.append(f"{transport:.0f} घंटे की यात्रा से यांत्रिक तनाव बढ़ता है।")
            key_causes.append(f"Long transit ({transport:.0f}h)")
            uncontrollable.append("transport_time")

        # Storage type
        if inp["storage_type"] == "ambient" and risk in ("high", "critical"):
            parts_en.append(
                f"Ambient storage without temperature control accelerates degradation. "
                f"Cold storage at {opt_temp[0]}–{opt_temp[1]}°C could extend life significantly."
            )
            parts_hi.append(
                f"बिना तापमान नियंत्रण के भंडारण से खराबी तेज़ होती है। "
                f"{opt_temp[0]}–{opt_temp[1]}°C पर कोल्ड स्टोरेज से शेल्फ लाइफ काफ़ी बढ़ सकती है।"
            )
            controllable.append("storage_type")

        # Risk conclusion
        risk_conclusions = {
            "low": {
                "en": "Overall, your produce is in good condition. You can wait for better market prices.",
                "hi": "कुल मिलाकर, आपकी उपज अच्छी स्थिति में है। बेहतर बाज़ार भाव का इंतज़ार कर सकते हैं।",
            },
            "medium": {
                "en": "Monitor conditions closely and plan to sell within the week.",
                "hi": "स्थिति पर नज़र रखें और इस हफ्ते बेचने की योजना बनाएं।",
            },
            "high": {
                "en": "Sell within 1-2 days to prevent significant losses.",
                "hi": "भारी नुकसान से बचने के लिए 1-2 दिन में बेच दें।",
            },
            "critical": {
                "en": "URGENT: Sell today. Every hour of delay increases losses.",
                "hi": "तुरंत बेचें! हर घंटे की देरी से नुकसान बढ़ रहा है।",
            },
        }
        conclusion = risk_conclusions.get(risk, risk_conclusions["medium"])
        parts_en.append(conclusion["en"])
        parts_hi.append(conclusion["hi"])

        return {
            "en": " ".join(parts_en),
            "hi": " ".join(parts_hi),
            "key_causes": key_causes,
            "controllable_factors": controllable,
            "uncontrollable_factors": uncontrollable,
            "source": "template-based (Bedrock unavailable)",
        }

    def whatif_analysis(
        self,
        prediction: Dict[str, Any],
        new_prediction: Dict[str, Any],
        change_description: str,
    ) -> Dict[str, Any]:
        """
        Generate a what-if explanation comparing two predictions.

        Args:
            prediction: Original prediction from SpoilagePredictor
            new_prediction: Prediction after the proposed change
            change_description: Human-readable description of the change

        Returns:
            Dict with before/after comparison and explanation
        """
        try:
            return self._bedrock_whatif(prediction, new_prediction, change_description)
        except Exception as e:
            print(f"Bedrock what-if failed ({e}), using template fallback")
            return self._template_whatif(prediction, new_prediction, change_description)

    def _bedrock_whatif(
        self,
        prediction: Dict[str, Any],
        new_prediction: Dict[str, Any],
        change_description: str,
    ) -> Dict[str, Any]:
        """What-if analysis using Bedrock Claude."""
        inp = prediction["input_summary"]
        current_conditions = (
            f"Temperature: {inp['temperature_c']}°C, "
            f"Humidity: {inp['humidity_pct']}%, "
            f"Storage: {inp['storage_type']}, "
            f"Days since harvest: {inp['days_since_harvest']}"
        )

        user_msg = WHATIF_USER_TEMPLATE.format(
            crop=prediction["crop"],
            crop_hindi=prediction["crop_hindi"],
            current_risk=prediction["risk_level"],
            current_prob=prediction["spoilage_probability"],
            current_remaining=prediction["remaining_shelf_life_days"],
            current_conditions=current_conditions,
            proposed_change=change_description,
            new_risk=new_prediction["risk_level"],
            new_prob=new_prediction["spoilage_probability"],
            new_remaining=new_prediction["remaining_shelf_life_days"],
        )

        response_text = self._invoke_bedrock(WHATIF_SYSTEM_PROMPT, user_msg)
        parsed = self._parse_json_response(response_text)

        return {
            "en": parsed.get("en", ""),
            "hi": parsed.get("hi", ""),
            "improvement": parsed.get("improvement", False),
            "impact_summary": parsed.get("impact_summary", ""),
            "before": {
                "risk_level": prediction["risk_level"],
                "spoilage_probability": prediction["spoilage_probability"],
                "remaining_days": prediction["remaining_shelf_life_days"],
            },
            "after": {
                "risk_level": new_prediction["risk_level"],
                "spoilage_probability": new_prediction["spoilage_probability"],
                "remaining_days": new_prediction["remaining_shelf_life_days"],
            },
            "change": change_description,
            "source": "Amazon Bedrock (Claude)",
        }

    def _template_whatif(
        self,
        prediction: Dict[str, Any],
        new_prediction: Dict[str, Any],
        change_description: str,
    ) -> Dict[str, Any]:
        """Template-based what-if fallback."""
        old_remaining = prediction["remaining_shelf_life_days"]
        new_remaining = new_prediction["remaining_shelf_life_days"]
        old_prob = prediction["spoilage_probability"]
        new_prob = new_prediction["spoilage_probability"]
        crop = prediction["crop"]
        hindi = prediction["crop_hindi"]
        improvement = new_prob < old_prob

        if improvement:
            delta_days = new_remaining - old_remaining
            delta_prob = old_prob - new_prob
            en = (
                f"If you {change_description.lower()}, your {crop} shelf life would increase "
                f"by ~{delta_days:.0f} days (from {old_remaining:.0f} to {new_remaining:.0f} days). "
                f"Spoilage probability would drop from {old_prob:.0%} to {new_prob:.0%}. "
                f"Risk level changes from {prediction['risk_level']} to {new_prediction['risk_level']}. "
                f"This change is recommended."
            )
            hi = (
                f"अगर आप {change_description.lower()} करें, तो आपकी {hindi} की शेल्फ लाइफ "
                f"~{delta_days:.0f} दिन बढ़ जाएगी ({old_remaining:.0f} से {new_remaining:.0f} दिन)। "
                f"खराबी की संभावना {old_prob:.0%} से {new_prob:.0%} हो जाएगी। "
                f"जोखिम स्तर {prediction['risk_level']} से {new_prediction['risk_level']} हो जाएगा। "
                f"यह बदलाव करना फ़ायदेमंद है।"
            )
        else:
            en = (
                f"If you {change_description.lower()}, your {crop} would see reduced shelf life "
                f"(from {old_remaining:.0f} to {new_remaining:.0f} days). "
                f"Spoilage risk would increase from {old_prob:.0%} to {new_prob:.0%}. "
                f"This change is NOT recommended."
            )
            hi = (
                f"अगर आप {change_description.lower()} करें, तो आपकी {hindi} की शेल्फ लाइफ "
                f"कम हो जाएगी ({old_remaining:.0f} से {new_remaining:.0f} दिन)। "
                f"खराबी का ख़तरा {old_prob:.0%} से {new_prob:.0%} बढ़ जाएगा। "
                f"यह बदलाव करना उचित नहीं है।"
            )

        return {
            "en": en,
            "hi": hi,
            "improvement": improvement,
            "impact_summary": (
                f"{'Improves' if improvement else 'Worsens'}: "
                f"{prediction['risk_level']} → {new_prediction['risk_level']}"
            ),
            "before": {
                "risk_level": prediction["risk_level"],
                "spoilage_probability": prediction["spoilage_probability"],
                "remaining_days": prediction["remaining_shelf_life_days"],
            },
            "after": {
                "risk_level": new_prediction["risk_level"],
                "spoilage_probability": new_prediction["spoilage_probability"],
                "remaining_days": new_prediction["remaining_shelf_life_days"],
            },
            "change": change_description,
            "source": "template-based (Bedrock unavailable)",
        }


# Singleton
bedrock_explainer = BedrockExplainer()

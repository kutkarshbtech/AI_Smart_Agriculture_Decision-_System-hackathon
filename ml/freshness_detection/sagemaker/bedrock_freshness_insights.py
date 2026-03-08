"""
Amazon Bedrock insight engine for the SwadeshAI Freshness Detection pipeline.

Architecture
────────────
    Image
      │
      ▼
    SageMaker Endpoint  (computer-vision only)
      │  returns structured JSON with `bedrock_context` field
      ▼
    BedrockFreshnessInsights.get_insights()
      │  injects CV results into a Claude prompt
      ▼
    Amazon Bedrock (Claude)
      │
      ▼
    Bilingual insights + recommendations (English + Hindi)

Usage
─────
    from bedrock_freshness_insights import BedrockFreshnessInsights

    # 1. Get CV result from SageMaker
    cv_result = invoke_sagemaker_endpoint(image_bytes)   # dict

    # 2. Call Bedrock for insights
    insights = BedrockFreshnessInsights()
    response = insights.get_insights(cv_result)

    print(response["english"])
    print(response["hindi"])
    print(response["action"])          # sell | monitor | process | discard
    print(response["price_impact"])    # estimated price impact string

Environment variables
─────────────────────
    BEDROCK_REGION          AWS region for Bedrock (default: us-east-1)
    BEDROCK_MODEL_ID        Bedrock model to use (default: Amazon Nova Lite)
"""

import json
import os
from typing import Any, Dict, Optional

# ── Bedrock configuration ────────────────────────────────────────────────────

BEDROCK_REGION  = os.environ.get("BEDROCK_REGION", "us-east-1")
BEDROCK_MODEL_ID = os.environ.get(
    "BEDROCK_MODEL_ID",
    "amazon.nova-lite-v1:0",
)

MAX_TOKENS = 1024
TEMPERATURE = 0.3   # Low temperature: consistent, factual advice

# ── Prompts ──────────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """\
You are SwadeshAI's Agricultural Intelligence Engine — an expert in Indian
produce quality assessment and post-harvest management.

You receive structured output from a computer-vision freshness detector and
translate it into clear, actionable insights for Indian farmers.

RULES:
1. Provide insights in BOTH English AND Hindi (Devanagari script).
2. Keep each language section under 120 words — concise and practical.
3. Use simple, non-technical language suitable for farmers with basic literacy.
4. Always include:
   - A 1-sentence summary of the produce condition.
   - A recommended action (sell / monitor / process / discard).
   - The likely price impact in the local mandi market.
   - 1-2 specific storage or handling tips relevant to the crop.
5. Ground all advice in Indian agricultural realities (mandi prices, local
   storage practices, seasonal context).
6. Do NOT repeat the raw numbers verbatim — interpret them meaningfully.
7. Output valid JSON only, matching the schema shown in the user message.
"""

USER_TEMPLATE = """\
Here is the freshness detection result from the computer-vision model:

{bedrock_context}

Please analyse this and return a JSON object with EXACTLY this schema:

{{
  "action":        "<one of: sell | monitor | process | discard>",
  "urgency":       "<one of: immediate | within_24h | within_3_days | no_rush>",
  "price_impact":  "<brief string, e.g. 'Full mandi price achievable' or '30-50% discount expected'>",
  "english": {{
    "summary":     "<1-sentence condition summary>",
    "insight":     "<2-3 sentence detailed insight>",
    "tips":        ["<tip 1>", "<tip 2>"]
  }},
  "hindi": {{
    "summary":     "<1-sentence condition summary in Hindi>",
    "insight":     "<2-3 sentence detailed insight in Hindi>",
    "tips":        ["<tip 1 in Hindi>", "<tip 2 in Hindi>"]
  }},
  "causal_factors": ["<key factor 1>", "<key factor 2>"]
}}

Return ONLY the JSON object — no markdown, no extra text.
"""

# ── Fallback templates (when Bedrock is unavailable) ────────────────────────

_FALLBACK: Dict[str, Dict] = {
    "fresh_high": {
        "action": "sell",
        "urgency": "within_3_days",
        "price_impact": "Full mandi price achievable",
        "english": {
            "summary": "Produce is fresh and market-ready.",
            "insight": (
                "The computer-vision model detected high freshness. "
                "Sell within 2–3 days to capture peak price."
            ),
            "tips": [
                "Store in a cool, ventilated space until sale.",
                "Handle carefully to avoid bruising during transport.",
            ],
        },
        "hindi": {
            "summary": "उत्पाद ताज़ा और बाज़ार के लिए तैयार है।",
            "insight": (
                "कंप्यूटर विज़न मॉडल ने उच्च ताज़गी का पता लगाया। "
                "अधिकतम मूल्य पाने के लिए 2-3 दिनों में बेचें।"
            ),
            "tips": [
                "बिक्री तक ठंडी और हवादार जगह पर रखें।",
                "परिवहन के दौरान चोट लगने से बचाएं।",
            ],
        },
        "causal_factors": ["High freshness confidence", "No visible spoilage markers"],
    },
    "fresh_low": {
        "action": "monitor",
        "urgency": "within_24h",
        "price_impact": "10–15% below peak price possible",
        "english": {
            "summary": "Produce appears fresh but model confidence is moderate.",
            "insight": (
                "The detection confidence is below 80%. "
                "Inspect manually and sell quickly to avoid quality deterioration."
            ),
            "tips": [
                "Sort and remove any visibly damaged pieces.",
                "Sell at the nearest mandi within 24 hours.",
            ],
        },
        "hindi": {
            "summary": "उत्पाद ताज़ा दिखता है लेकिन मॉडल का विश्वास मध्यम है।",
            "insight": (
                "पहचान का विश्वास 80% से कम है। "
                "मैन्युअल रूप से जाँचें और गुणवत्ता में गिरावट से बचने के लिए जल्दी बेचें।"
            ),
            "tips": [
                "दिखने में क्षतिग्रस्त टुकड़ों को अलग करें।",
                "24 घंटों के भीतर नज़दीकी मंडी में बेचें।",
            ],
        },
        "causal_factors": ["Moderate confidence", "Borderline freshness scores"],
    },
    "rotten_high": {
        "action": "discard",
        "urgency": "immediate",
        "price_impact": "Not sellable at mandi; consider composting",
        "english": {
            "summary": "Significant spoilage detected — not suitable for sale.",
            "insight": (
                "The model detected clear signs of spoilage with high confidence. "
                "Discard or process immediately to prevent contaminating fresh produce nearby."
            ),
            "tips": [
                "Separate spoiled produce from fresh batches immediately.",
                "Use for composting or biogas to recover some value.",
            ],
        },
        "hindi": {
            "summary": "महत्वपूर्ण खराबी का पता चला — बिक्री के लिए उपयुक्त नहीं।",
            "insight": (
                "मॉडल ने उच्च विश्वास के साथ खराबी के स्पष्ट संकेत पाए। "
                "पास की ताज़ी फसल को दूषित होने से बचाने के लिए तुरंत अलग करें।"
            ),
            "tips": [
                "खराब उत्पाद को तुरंत ताज़े उत्पाद से अलग करें।",
                "कुछ मूल्य वापस पाने के लिए खाद या बायोगैस में उपयोग करें।",
            ],
        },
        "causal_factors": ["High spoilage confidence", "Damage score elevated"],
    },
    "rotten_low": {
        "action": "process",
        "urgency": "within_24h",
        "price_impact": "30–50% discount; consider processing unit sale",
        "english": {
            "summary": "Spoilage signs detected but model confidence is moderate.",
            "insight": (
                "Some spoilage is likely. Consider selling quickly at a discounted price "
                "or to a food-processing unit rather than holding in storage."
            ),
            "tips": [
                "Contact local processing units or juice manufacturers.",
                "Sell at discounted price at the nearest mandi today.",
            ],
        },
        "hindi": {
            "summary": "खराबी के संकेत मिले लेकिन मॉडल का विश्वास मध्यम है।",
            "insight": (
                "कुछ खराबी संभावित है। रखने की बजाय कम कीमत पर जल्दी बेचने या "
                "खाद्य प्रसंस्करण इकाई को बेचने पर विचार करें।"
            ),
            "tips": [
                "स्थानीय प्रसंस्करण इकाइयों या जूस निर्माताओं से संपर्क करें।",
                "आज नज़दीकी मंडी में कम दाम पर बेचें।",
            ],
        },
        "causal_factors": ["Moderate spoilage confidence", "Partial damage markers"],
    },
}


def _fallback_response(cv_result: Dict[str, Any]) -> Dict[str, Any]:
    """Return a template-based response when Bedrock is unavailable."""
    status = cv_result.get("freshness_status", "fresh")
    conf   = cv_result.get("confidence", 0.5)

    if status == "fresh" and conf >= 0.8:
        key = "fresh_high"
    elif status == "fresh":
        key = "fresh_low"
    elif conf >= 0.8:
        key = "rotten_high"
    else:
        key = "rotten_low"

    result = dict(_FALLBACK[key])
    result["source"] = "fallback_template"
    return result


# ── Main class ───────────────────────────────────────────────────────────────

class BedrockFreshnessInsights:
    """
    Calls Amazon Bedrock (Claude) to generate insights from a CV detection result.

    Example
    ───────
        insights = BedrockFreshnessInsights()
        result   = insights.get_insights(cv_result)
        # result["english"]["summary"]  → English summary
        # result["hindi"]["insight"]    → Hindi insight
        # result["action"]             → sell | monitor | process | discard
    """

    def __init__(
        self,
        region:   Optional[str] = None,
        model_id: Optional[str] = None,
        profile:  Optional[str] = None,
    ):
        self.region   = region   or BEDROCK_REGION
        self.model_id = model_id or BEDROCK_MODEL_ID
        self.profile  = profile  or os.environ.get("AWS_PROFILE")
        self._client  = None  # lazy-initialised

    def _get_client(self):
        if self._client is None:
            import boto3
            from botocore.exceptions import NoCredentialsError, NoRegionError
            try:
                session = boto3.Session(
                    profile_name=self.profile,
                    region_name=self.region,
                )
                self._client = session.client("bedrock-runtime")
            except Exception as exc:
                raise RuntimeError(
                    f"Failed to create Bedrock client: {exc}\n"
                    "Fix credentials with one of:\n"
                    "  aws configure                          # interactive setup\n"
                    "  aws configure --profile <name>         # named profile\n"
                    "  export AWS_PROFILE=<name>              # use existing profile\n"
                    "  export AWS_ACCESS_KEY_ID=...           # env-var credentials"
                ) from exc
        return self._client

    # ── Public API ───────────────────────────────────────────────────────────

    def get_insights(
        self,
        cv_result: Dict[str, Any],
        extra_context: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Generate insights for a freshness CV result.

        Parameters
        ──────────
        cv_result:      JSON dict returned by the SageMaker freshness endpoint.
                        Must contain at minimum: freshness_status, crop_type,
                        confidence, quality_grade, bedrock_context.
        extra_context:  Optional free-text to append to the prompt (e.g., current
                        season, location, market conditions).

        Returns
        ───────
        dict with keys: action, urgency, price_impact, english, hindi,
                        causal_factors, source ("bedrock" | "fallback_template")
        """
        bedrock_ctx = cv_result.get("bedrock_context", "")
        if not bedrock_ctx:
            # Build a minimal context string if the field is absent
            bedrock_ctx = (
                f"Crop: {cv_result.get('crop_type', 'unknown').replace('_', ' ').title()}\n"
                f"Freshness Status: {cv_result.get('freshness_status', 'unknown').upper()}\n"
                f"Confidence: {round(cv_result.get('confidence', 0) * 100, 1)}%\n"
                f"Quality Grade: {cv_result.get('quality_grade', 'N/A')} "
                f"(score {cv_result.get('quality_score', 'N/A')}/100)"
            )

        if extra_context:
            bedrock_ctx += f"\n\nAdditional context:\n{extra_context}"

        user_message = USER_TEMPLATE.format(bedrock_context=bedrock_ctx)

        try:
            raw = self._invoke_bedrock(user_message)
            result = json.loads(raw)
            result["source"] = "bedrock"
            return result
        except json.JSONDecodeError:
            # Claude returned text around the JSON — extract it
            import re
            match = re.search(r"\{.*\}", raw, re.DOTALL)
            if match:
                result = json.loads(match.group())
                result["source"] = "bedrock"
                return result
            # If still failing, use fallback
            return _fallback_response(cv_result)
        except Exception:
            return _fallback_response(cv_result)

    def get_batch_insights(
        self,
        cv_results: list,
        extra_context: Optional[str] = None,
    ) -> list:
        """
        Generate insights for a list of CV results.

        Returns a list of insight dicts in the same order as `cv_results`.
        """
        return [
            self.get_insights(r, extra_context=extra_context)
            for r in cv_results
        ]

    # ── Internal ─────────────────────────────────────────────────────────────

    def _invoke_bedrock(self, user_message: str) -> str:
        """Send a Converse API request to Bedrock and return the raw text reply."""
        client = self._get_client()

        response = client.converse(
            modelId=self.model_id,
            system=[{"text": SYSTEM_PROMPT}],
            messages=[
                {
                    "role": "user",
                    "content": [{"text": user_message}],
                }
            ],
            inferenceConfig={
                "maxTokens": MAX_TOKENS,
                "temperature": TEMPERATURE,
            },
        )

        return response["output"]["message"]["content"][0]["text"]


# ── Convenience function ─────────────────────────────────────────────────────

def get_freshness_insights(
    cv_result: Dict[str, Any],
    extra_context: Optional[str] = None,
    region:   Optional[str] = None,
    model_id: Optional[str] = None,
    profile:  Optional[str] = None,
) -> Dict[str, Any]:
    """
    Module-level shortcut — no class instantiation required.

    Example
    ───────
        from bedrock_freshness_insights import get_freshness_insights
        insights = get_freshness_insights(sagemaker_cv_output)
    """
    engine = BedrockFreshnessInsights(region=region, model_id=model_id, profile=profile)
    return engine.get_insights(cv_result, extra_context=extra_context)


# ── CLI demo ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse
    import sys

    sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent.parent.parent.parent))

    parser = argparse.ArgumentParser(
        description="Test BedrockFreshnessInsights with a dummy or real CV result"
    )
    parser.add_argument("--cv-result", type=str, help="Path to a JSON file with CV result")
    parser.add_argument("--endpoint",  type=str, help="SageMaker endpoint name to invoke first")
    parser.add_argument("--image",     type=str, help="Image path (requires --endpoint)")
    parser.add_argument("--region",    type=str, default=BEDROCK_REGION)
    parser.add_argument("--model-id",  type=str, default=BEDROCK_MODEL_ID)
    parser.add_argument(
        "--profile", type=str,
        default=os.environ.get("AWS_PROFILE"),
        help="AWS named profile (from ~/.aws/credentials). "
             "Also reads AWS_PROFILE env var.",
    )
    args = parser.parse_args()

    if args.cv_result:
        with open(args.cv_result) as f:
            cv_result = json.load(f)
    elif args.endpoint and args.image:
        import boto3
        from botocore.exceptions import NoCredentialsError, ProfileNotFound

        try:
            session = boto3.Session(profile_name=args.profile, region_name=args.region)
            runtime = session.client("sagemaker-runtime")
        except ProfileNotFound as exc:
            print(f"\nError: {exc}")
            print("Available profiles:")
            try:
                for p in boto3.Session().available_profiles:
                    print(f"  {p}")
            except Exception:
                pass
            sys.exit(1)

        img_suffix = args.image.lower()
        content_type = "image/png" if img_suffix.endswith(".png") else "image/jpeg"

        try:
            with open(args.image, "rb") as f:
                img_bytes = f.read()
            resp = runtime.invoke_endpoint(
                EndpointName=args.endpoint,
                ContentType=content_type,
                Body=img_bytes,
            )
        except NoCredentialsError:
            print(
                "\nError: No AWS credentials found.\n"
                "Fix with one of:\n"
                "  aws configure                          # interactive setup\n"
                "  aws configure --profile <name>         # named profile\n"
                "  python bedrock_freshness_insights.py --profile <name> ...\n"
                "  export AWS_PROFILE=<name>              # use existing profile\n"
                "  export AWS_ACCESS_KEY_ID=...           # env-var credentials\n"
                "\nTo run against a synthetic result instead (no AWS needed):\n"
                "  python bedrock_freshness_insights.py"
            )
            sys.exit(1)

        cv_result = json.loads(resp["Body"].read())
        print("\n── SageMaker CV Result ──────────────────────────────────")
        print(json.dumps(cv_result, ensure_ascii=False, indent=2))
    else:
        # Demo with a synthetic CV result
        cv_result = {
            "predicted_class": "fresh_tomato",
            "freshness_status": "fresh",
            "crop_type": "tomato",
            "hindi_label": "ताज़ा टमाटर",
            "confidence": 0.94,
            "quality_score": 88,
            "freshness_score": 91,
            "damage_score": 8,
            "ripeness_level": 82,
            "quality_grade": "A",
            "top_predictions": [
                {"class": "fresh_tomato",  "confidence": 0.94, "hindi": "ताज़ा टमाटर"},
                {"class": "fresh_capsicum","confidence": 0.04, "hindi": "ताज़ी शिमला मिर्च"},
            ],
            "inference_time_ms": 42.3,
            "bedrock_context": (
                "Crop: Tomato (ताज़ा टमाटर)\n"
                "Freshness Status: FRESH\n"
                "Confidence: 94.0%\n"
                "Quality Grade: A (score 88/100)\n"
                "Freshness Score: 91/100\n"
                "Damage Score: 8/100\n"
                "Ripeness Level: 82/100\n"
                "Top alternative predictions: fresh_capsicum (4.0%), rotten_tomato (0.8%)"
            ),
        }
        print("Using synthetic demo CV result (tomato, fresh, 94% confidence)\n")

    engine = BedrockFreshnessInsights(
        region=args.region,
        model_id=args.model_id,
        profile=args.profile,
    )
    insights = engine.get_insights(cv_result)

    print("\n── Bedrock Insights ─────────────────────────────────────")
    print(f"Action:        {insights['action']}")
    print(f"Urgency:       {insights['urgency']}")
    print(f"Price Impact:  {insights['price_impact']}")
    print(f"Source:        {insights['source']}")
    print(f"\n[English]")
    print(f"  Summary: {insights['english']['summary']}")
    print(f"  Insight: {insights['english']['insight']}")
    for tip in insights["english"]["tips"]:
        print(f"  • {tip}")
    print(f"\n[Hindi]")
    print(f"  सारांश: {insights['hindi']['summary']}")
    print(f"  विवरण:  {insights['hindi']['insight']}")
    for tip in insights["hindi"]["tips"]:
        print(f"  • {tip}")
    print(f"\nCausal Factors: {', '.join(insights.get('causal_factors', []))}")

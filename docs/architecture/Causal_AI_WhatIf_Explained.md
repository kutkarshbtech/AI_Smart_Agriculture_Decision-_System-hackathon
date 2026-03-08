# SwadeshAI — Causal AI & What-If Feature Explained

---

## Causal AI (DoWhy)

This is a **statistical causal inference engine** built with Microsoft Research's [DoWhy library](https://github.com/py-why/dowhy) — it goes beyond correlations to answer **"does X cause Y?"** with mathematical rigor.

### How It Works

The service (`backend/app/services/causal_service.py`) answers **3 causal questions**:

| Question | Treatment | Outcome | Confounders Controlled |
|---|---|---|---|
| Does cold storage **cause** less spoilage? | Cold vs Ambient storage | Spoilage rate (%) | Temperature, humidity, initial quality, crop age |
| Does high temperature **cause** price changes? | >35°C vs normal | Market price (₹/kg) | Season, rainfall, market demand |
| Does quality grade **cause** a price premium? | Excellent vs average quality | Selling price (₹/kg) | Crop freshness, market location, harvest season |

### The 4-Step Pipeline (per analysis)

1. **Data Generation** — Generates 400–600 realistic synthetic data points with embedded ground-truth causal effects (e.g., cold storage reduces spoilage by exactly 15 percentage points in the data). In production, this swaps to real farm transaction data.

2. **Causal Graph Definition** — Defines an explicit DAG (Directed Acyclic Graph) via DoWhy's `CausalModel`:
   ```python
   model = CausalModel(
       data=data,
       treatment='storage_type_cold',
       outcome='spoilage_rate',
       common_causes=['temperature', 'humidity', 'initial_quality', 'crop_age_days'],
   )
   ```
   This tells DoWhy what the confounders are — variables that influence *both* the treatment and the outcome.

3. **Estimation** — Uses one of two methods:
   - **Propensity Score Matching** (for storage→spoilage) — matches treated/untreated units by their probability of receiving treatment, mimicking a randomized experiment
   - **Linear Regression with Backdoor Adjustment** (for weather→prices, quality→premium) — estimates the treatment effect while statistically controlling for confounders

4. **Refutation Testing** — Validates robustness:
   - **Random Common Cause refuter** — adds a random extra confounder; the estimate should remain stable
   - **Placebo Treatment refuter** — replaces the real treatment with a random variable; the estimated effect should drop to ~0

### What It Returns

Each analysis returns:
- **Average Treatment Effect (ATE)** — e.g., "cold storage reduces spoilage by 18.4 percentage points"
- **Confidence level** — High/Medium based on effect magnitude and robustness tests
- **Causal mechanism** — e.g., "Cold storage → Lower microbial activity → Slower enzymatic degradation → Reduced moisture loss → Lower spoilage rate"
- **Actionable recommendation** — e.g., "Invest in cold storage for tomato — roughly 18% less spoilage"
- **Data summary** — means for treatment/control groups
- **Sensitivity robust** flag — does the effect survive refutation tests?

### Why Not Just Correlation?

Correlation might show "farmers with cold storage also have less spoilage" — but that could be because richer farmers both own cold storage AND buy better quality seed. DoWhy's backdoor adjustment isolates the *causal* effect of storage alone by controlling for temperature, humidity, quality, and age.

### API Endpoints

```
GET /api/v1/causal/storage-spoilage?crop_name=tomato&quality_grade=good
GET /api/v1/causal/weather-prices?crop_name=tomato&location=Lucknow
GET /api/v1/causal/quality-premium?crop_name=tomato
```

---

## What-If Scenario Engine

This is implemented at **two levels**:

### 1. Pricing What-If (XGBoost Model)

**File:** `backend/ml/pricing/model.py` — `what_if()` method

The `what_if()` method on the XGBoost pricing model:
- Takes the **original 25-feature vector** and the **base price prediction**
- **Mutates one or more features** (e.g., change `storage_temp` from 30→4, or `quality_code` from 1→3)
- **Re-runs the XGBoost model** with the modified vector
- Returns the **price delta** in ₹ and % terms

```python
def what_if(self, base_prediction, feature_overrides, crop_name, original_features):
    modified = dict(original_features)
    modified.update(feature_overrides)
    vec = features_to_vector(modified)

    if self.is_trained and HAS_XGB:
        new_ideal = self._ml_predict(vec, modified)
    else:
        new_ideal = self._rule_predict(modified, crop_name)

    change = new_ideal - base_prediction["ideal_price"]
    pct = (change / base_prediction["ideal_price"] * 100)

    return {
        "original_ideal_price": orig_ideal,
        "new_ideal_price": round(new_ideal, 2),
        "price_change": round(change, 2),
        "price_change_pct": round(pct, 1),
        "overrides_applied": feature_overrides,
    }
```

The pricing service (`backend/app/services/pricing_service.py`) auto-generates **3 scenarios** for every price recommendation:

| Scenario | What It Mutates | Example Output |
|---|---|---|
| "If quality improves to excellent" | `quality_code` → 3.0 | +₹4.52/kg (+12.3%) |
| "If moved to cold storage (4°C)" | `is_cold_storage` → 1, `storage_temp` → 4 | +₹3.18/kg (+8.7%) |
| "If temperature rises by 5°C" | `storage_temp` += 5, `spoilage_risk_code` += 0.33 | -₹2.91/kg (-7.9%) |

This is a **counterfactual intervention** — "what would the model predict if you changed this one thing?"

### 2. Spoilage What-If (Bedrock Explainer)

**File:** `ml/spoilage_prediction/bedrock_explainer.py` — `BedrockExplainer` class

The `BedrockExplainer.whatif_analysis()` method:

1. Takes the **original spoilage prediction** (risk level, probability, remaining days)
2. Takes a **new prediction** after changing conditions (e.g., switching to cold storage)
3. Feeds both into Amazon Bedrock with a structured prompt asking it to **explain the difference to a farmer in Hindi + English**
4. Returns:
   - Bilingual explanation (EN + HI Devanagari)
   - `improvement: true/false`
   - Before/after comparison (risk level, probability, remaining days)
   - One-line impact summary

#### Bedrock Prompt Used

```
WHATIF_SYSTEM_PROMPT = """You are SwadeshAI's What-If Analysis Engine.
Given a farmer's current spoilage prediction and a proposed change,
explain what would happen if they made that change.
Be specific with numbers. Compare before vs after.
Respond in both English and Hindi."""
```

#### Template Fallback (when Bedrock is unavailable)

Generates the same structured output without an LLM — e.g.:

> *"अगर आप cold storage में रखें, तो आपकी टमाटर की शेल्फ लाइफ ~5 दिन बढ़ जाएगी (3 से 8 दिन)। खराबी की संभावना 72% से 28% हो जाएगी। यह बदलाव करना फ़ायदेमंद है।"*

#### Output Structure

```json
{
    "en": "English what-if explanation...",
    "hi": "Hindi what-if explanation...",
    "improvement": true,
    "impact_summary": "Improves: high → low",
    "before": {
        "risk_level": "high",
        "spoilage_probability": 0.72,
        "remaining_days": 3
    },
    "after": {
        "risk_level": "low",
        "spoilage_probability": 0.28,
        "remaining_days": 8
    },
    "change": "Move to cold storage",
    "source": "Amazon Bedrock (Claude)"
}
```

---

## Causal Explanation Engine (Bedrock-Powered)

**File:** `ml/spoilage_prediction/bedrock_explainer.py` — `BedrockExplainer.explain()` method

Separate from DoWhy, this uses **Amazon Bedrock (Nova Lite)** to generate rich causal *narratives* explaining individual spoilage predictions:

### What It Does

1. Takes a spoilage prediction result (crop, risk level, probability, conditions)
2. Computes **risk factors** from the data:
   - Temperature delta from optimal + Q10 acceleration factor
   - Humidity deviation + mold/wilting risk
   - Transport time + mechanical damage sensitivity
3. Sends all data to Bedrock with a structured prompt requiring JSON output
4. Returns bilingual explanation + key causes + controllable vs uncontrollable factors

### System Prompt Highlights

```
RULES:
1. Explain WHY the prediction is what it is using cause → effect reasoning
2. Use specific numbers (temperature, days, percentages)
3. Compare current conditions to optimal conditions
4. Mention the Q10 rule: "For every 10°C above optimal, spoilage doubles"
5. Explain what the farmer CAN control vs what they CANNOT
6. Always end with 1-2 specific actionable recommendations
7. Keep explanations under 150 words per language
```

### Template Fallback Example

When Bedrock is unavailable, the template engine generates:

> **English:** "Your tomato batch was harvested 3 day(s) ago. Estimated remaining shelf life: 5 days. Storage temperature (35°C) is 7°C above optimal (10–28°C). By the Q10 rule, spoilage rate is ~1.6x faster than normal. Humidity (85%) exceeds optimal (85–95%), promoting mold and bacterial growth. Sell within 1-2 days to prevent significant losses."
>
> **Hindi:** "आपकी टमाटर की खेप 3 दिन पहले काटी गई थी। अनुमानित बची हुई शेल्फ लाइफ: 5 दिन। भंडारण तापमान (35°C) इष्टतम (10–28°C) से 7°C अधिक है। Q10 नियम के अनुसार, खराबी ~1.6 गुना तेज़ है। भारी नुकसान से बचने के लिए 1-2 दिन में बेच दें।"

---

## Key Difference: Causal AI vs What-If

| | Causal AI (DoWhy) | What-If Engine |
|---|---|---|
| **Question** | "Does X *cause* Y across the population?" | "What would happen to *my* crop if I changed X?" |
| **Method** | Statistical causal inference with confounder adjustment | Counterfactual model re-prediction |
| **Scope** | Population-level Average Treatment Effect | Individual prediction perturbation |
| **Output** | Statistical significance, robustness tests, causal mechanisms | ₹/kg price change, shelf life change, bilingual farmer explanation |
| **Library** | Microsoft DoWhy | XGBoost re-inference + Amazon Bedrock LLM |

Together they form SwadeshAI's **Explainable AI** layer — the Causal AI proves *why* something matters statistically, and the What-If engine shows *your specific* farmer what would happen if they act on it.

---

## Files Involved

| File | Role |
|---|---|
| `backend/app/services/causal_service.py` | DoWhy causal inference (3 analyses) |
| `backend/app/api/routes/causal.py` | API endpoints for causal analysis |
| `backend/ml/pricing/model.py` | XGBoost `what_if()` for pricing counterfactuals |
| `backend/app/services/pricing_service.py` | Auto-generates 3 what-if scenarios per price recommendation |
| `ml/spoilage_prediction/bedrock_explainer.py` | Bedrock-powered causal explanations + what-if for spoilage |
| `ml/spoilage_prediction/demo_app.py` | Streamlit demo with what-if analysis UI |
| `dashboard/app.py` | Dashboard Causal AI page (DoWhy UI) |
| `frontend/src/components/CausalAnalysis.jsx` | React frontend causal analysis component |

---

*Generated from SwadeshAI codebase analysis — March 2026*

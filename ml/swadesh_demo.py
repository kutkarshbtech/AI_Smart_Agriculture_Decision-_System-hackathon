"""
SwadeshAI — Unified Hackathon Demo App
AWS AI for Bharat Hackathon

Combines two core AI features:
  1. 🥦 Freshness Detection   — MobileNetV2 CNN image classifier (fresh vs rotten)
  2. 📦 Spoilage Prediction   — XGBoost multi-output risk predictor (shelf life, probability, risk level)

Both features include:
  - Hindi + English output
  - Farmer-friendly recommendations
  - Amazon Bedrock (Claude) causal explanations with template fallback

Run:
    streamlit run swadesh_demo.py
"""

import sys
import json
import io
import importlib.util
from pathlib import Path

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from PIL import Image

# ── Path constants ─────────────────────────────────────────────────
ML_DIR         = Path(__file__).parent
FRESHNESS_DIR  = ML_DIR / "freshness_detection"
SPOILAGE_DIR   = ML_DIR / "spoilage_prediction"

def _load_module(name: str, file_path: Path, plain_alias: str | None = None):
    """
    Load a Python module from an explicit file path.

    `plain_alias`: if given, also registers the module under that bare name in
    sys.modules so that other modules in the same package that do
    `from dataset import ...` or `from model import ...` resolve correctly.
    """
    spec = importlib.util.spec_from_file_location(name, file_path)
    mod  = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    if plain_alias:
        sys.modules[plain_alias] = mod
    spec.loader.exec_module(mod)
    return mod

# ── Freshness modules ──────────────────────────────────────────────
# Add freshness dir first; also register each module under its plain name
# so that fd_model / fd_inf internal imports (`from dataset import …`) work.
sys.path.insert(0, str(FRESHNESS_DIR))
fd_dataset  = _load_module("fd_dataset",  FRESHNESS_DIR / "dataset.py",  plain_alias="dataset")
fd_model    = _load_module("fd_model",    FRESHNESS_DIR / "model.py",    plain_alias="model")
fd_inf      = _load_module("fd_inf",      FRESHNESS_DIR / "inference.py")

# ── Spoilage modules ───────────────────────────────────────────────
# Override the plain aliases so that sp_model / sp_inf internal imports
# (`from dataset import FEATURE_COLUMNS`, `from model import SpoilageModel`)
# resolve to the *spoilage* versions, not the freshness ones.
sys.path.insert(0, str(SPOILAGE_DIR))
sp_dataset  = _load_module("sp_dataset",  SPOILAGE_DIR / "dataset.py",  plain_alias="dataset")
sp_model    = _load_module("sp_model",    SPOILAGE_DIR / "model.py",    plain_alias="model")
sp_inf      = _load_module("sp_inf",      SPOILAGE_DIR / "inference.py")

FreshnessDetector  = fd_inf.FreshnessDetector
SpoilagePredictor  = sp_inf.SpoilagePredictor
CROP_PROFILES      = sp_dataset.CROP_PROFILES

# ── Page config ────────────────────────────────────────────────────
st.set_page_config(
    page_title="SwadeshAI Demo",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS ────────────────────────────────────────────────────────────
st.markdown("""
<style>
    /* Header */
    .main-header {
        background: linear-gradient(135deg, #1a6b3c 0%, #2d9e5f 55%, #f7a800 100%);
        padding: 1.2rem 2rem; border-radius: 12px;
        margin-bottom: 1.2rem; color: white;
    }
    .main-header h1 { margin: 0; font-size: 1.9rem; }
    .main-header p  { margin: 0.2rem 0 0; opacity: 0.9; font-size: 0.95rem; }

    /* freshness badges */
    .badge-fresh  { display:inline-block; background:#28a745; color:white;
                    padding:.3rem .8rem; border-radius:20px; font-weight:700; font-size:1rem; }
    .badge-rotten { display:inline-block; background:#dc3545; color:white;
                    padding:.3rem .8rem; border-radius:20px; font-weight:700; font-size:1rem; }

    /* quality score ring text */
    .score-big { font-size:3rem; font-weight:800; line-height:1; }

    /* risk cards */
    .risk-low      { background:#d4edda; border-left:5px solid #28a745; color:#155724; }
    .risk-medium   { background:#fff3cd; border-left:5px solid #ffc107; color:#856404; }
    .risk-high     { background:#ffe0b2; border-left:5px solid #ff9800; color:#7b3f00; }
    .risk-critical { background:#f8d7da; border-left:5px solid #dc3545; color:#721c24; }
    .risk-card { padding:1rem 1.4rem; border-radius:10px; margin-bottom:1rem;
                 font-weight:bold; font-size:1.05rem; }

    /* rec cards */
    .rec-card { background:white; border-radius:8px; padding:.7rem 1rem;
                margin-bottom:.45rem; border-left:4px solid #2d9e5f;
                box-shadow:0 1px 3px rgba(0,0,0,.08); }
    .rec-card.critical { border-left-color:#dc3545; }
    .rec-card.high     { border-left-color:#ff9800; }
    .rec-card.moderate { border-left-color:#ffc107; }

    /* explanation box */
    .expl-box { background:#f0f7ff; border:1px solid #bee3f8;
                border-radius:8px; padding:.9rem 1.1rem; }

    /* aws badge */
    .aws-badge { display:inline-block; background:#ff9900; color:white;
                 padding:.15rem .55rem; border-radius:4px;
                 font-size:.72rem; font-weight:bold; }
    .tmpl-badge { display:inline-block; background:#6c757d; color:white;
                  padding:.15rem .55rem; border-radius:4px; font-size:.72rem; }

    /* metric progress bar */
    .mbar-wrap { margin-bottom:.6rem; }
    .mbar-label { display:flex; justify-content:space-between;
                  font-size:.82rem; font-weight:600; margin-bottom:3px; }
    .mbar-track { height:10px; background:#e9ecef; border-radius:6px; overflow:hidden; }
    .mbar-fill  { height:100%; border-radius:6px; transition:width .4s ease; }

    /* price card */
    .price-card { background: linear-gradient(135deg,#1a6b3c,#2d9e5f);
                  color:white; border-radius:10px; padding:.9rem 1.2rem;
                  text-align:center; }
    .price-card .price-main { font-size:1.7rem; font-weight:800; line-height:1.1; }
    .price-card .price-sub  { font-size:.8rem; opacity:.85; margin-top:3px; }
</style>
""", unsafe_allow_html=True)

# ── Shared constants ───────────────────────────────────────────────
RISK_COLORS = {"low":"#28a745","medium":"#ffc107","high":"#ff9800","critical":"#dc3545"}
RISK_BG     = {"low":"#d4edda","medium":"#fff3cd","high":"#ffe0b2","critical":"#f8d7da"}
FRESHNESS_MODEL_PATH = str(FRESHNESS_DIR / "models" / "freshness_v1_best.pth")
SAMPLE_DIR           = FRESHNESS_DIR / "samples" / "real_test"

# ── Mandi (wholesale market) price table — ₹/kg at Grade-A quality ──
# Sources: Agmarknet average April–Nov 2024 (indicative only)
MANDI_PRICES = {
    # crop_type         (min_rs, max_rs, unit)
    "apple":            (70,  130, "kg"),
    "banana":           (25,   55, "dozen"),
    "bell_pepper":      (35,   70, "kg"),
    "bellpepper":       (35,   70, "kg"),
    "carrot":           (18,   38, "kg"),
    "cucumber":         (12,   28, "kg"),
    "mango":            (55,  110, "kg"),
    "okra":             (20,   45, "kg"),
    "orange":           (35,   75, "kg"),
    "potato":           (12,   25, "kg"),
    "strawberry":       (180, 320, "kg"),
    "tomato":           (15,   40, "kg"),
    "bitter_gourd":     (20,   45, "kg"),
    "capsicum":         (35,   70, "kg"),
}

# Quality grade multiplier on top price
_GRADE_MULT = {"A": 1.0, "B": 0.75, "C": 0.45, "D": 0.20,
               "excellent": 1.0, "good": 0.75, "average": 0.45, "poor": 0.20}


def _compute_extended_metrics(result: dict) -> dict:
    """
    Derive damage_score, ripeness_level, and mandi price estimate from
    the FreshnessDetector result dict.

    Uses the same formulas as the SageMaker inference handler so the
    numbers match the results_v3 PNG reports.
    """
    status = result["freshness_status"]
    conf   = result["confidence"]
    top    = result["top_predictions"]

    # Estimate rotten_sum from top-5 predictions
    rotten_sum = sum(
        p["confidence"] for p in top if p["class"].startswith("rotten_")
    )

    if status == "fresh":
        damage   = int(max(0,   (1 - conf) * 40 + rotten_sum * 30))
        ripeness = int(min(100, 60 + conf * 35))
    else:
        damage   = int(min(100, 40 + conf * 55))
        ripeness = int(max(10,  80 - conf * 60))

    # Price estimate — apply grade OR rotten discount against the BASE price
    # (never stack both, which collapses cheap crops to ₹0)
    crop      = result["crop_type"]
    grade     = result["quality_grade"]           # e.g. "excellent" / "A"
    price_row = MANDI_PRICES.get(crop, (20, 50, "kg"))
    base_min, base_max = price_row[0], price_row[1]
    p_unit    = price_row[2]

    if status == "fresh":
        mult  = _GRADE_MULT.get(grade, 0.6)
        p_min = max(1, int(base_min * mult))
        p_max = max(1, int(base_max * mult))
    else:
        # Rotten: 10-30% of base price depending on damage severity
        # High damage (conf high) → closer to 10%; low damage → up to 30%
        rotten_mult = max(0.08, 0.30 - conf * 0.22)
        p_min = max(1, int(base_min * rotten_mult))
        p_max = max(1, int(base_max * rotten_mult))

    return {
        "damage_score":   min(100, max(0, damage)),
        "ripeness_level": min(100, max(0, ripeness)),
        "price_min":      p_min,
        "price_max":      p_max,
        "price_unit":     p_unit,
        "price_grade":    grade,
    }

# ── Cached loaders ─────────────────────────────────────────────────
@st.cache_resource(show_spinner="Loading Freshness Detection model…")
def load_freshness_detector():
    return FreshnessDetector(model_path=FRESHNESS_MODEL_PATH, confidence_threshold=0.5)

@st.cache_resource(show_spinner="Loading Spoilage Prediction model…")
def load_spoilage_predictor(use_bedrock: bool = False):
    return SpoilagePredictor(
        model_dir=str(SPOILAGE_DIR / "models"),
        model_prefix="spoilage_v1",
        use_bedrock=use_bedrock,
    )

# ──────────────────────────────────────────────────────────────────
# HEADER
# ──────────────────────────────────────────────────────────────────
st.markdown("""
<div class="main-header">
  <h1>🌾 SwadeshAI &nbsp;—&nbsp; AI for Indian Farmers</h1>
  <p>
    Freshness Detection &nbsp;·&nbsp; Spoilage Prediction &nbsp;·&nbsp;
    Hindi + English &nbsp;·&nbsp; Powered by Amazon Bedrock &amp; SageMaker
  </p>
</div>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────────
# NAVIGATION
# ──────────────────────────────────────────────────────────────────
page = st.radio(
    "Feature",
    ["🥦 Freshness Detection", "📦 Spoilage Prediction", "📊 Dashboard"],
    horizontal=True,
    label_visibility="collapsed",
)
st.markdown("---")


# ══════════════════════════════════════════════════════════════════
# PAGE 1 — FRESHNESS DETECTION
# ══════════════════════════════════════════════════════════════════
if page == "🥦 Freshness Detection":

    st.markdown("### 🥦 Freshness Detection")
    st.markdown(
        "Upload a photo of your produce. The CNN model (MobileNetV2) identifies "
        "whether it is **fresh** or **rotten** and gives farmer-friendly advice."
    )

    # ── Image source toggle ─────────────────────────────────────────
    src = st.radio("Image source", ["📤 Upload photo", "🖼️ Use sample image"], horizontal=True)

    pil_image = None

    if src == "📤 Upload photo":
        # Clear any stale sample selection when switching to upload mode
        st.session_state.pop("fd_selected_sample", None)
        uploaded = st.file_uploader(
            "Upload fruit / vegetable photo",
            type=["jpg", "jpeg", "png", "webp"],
        )
        if uploaded:
            pil_image = Image.open(uploaded).convert("RGB")

    else:  # ── Sample image gallery ─────────────────────────────────
        all_samples = sorted(SAMPLE_DIR.glob("*.png")) + sorted(SAMPLE_DIR.glob("*.jpg"))
        fresh_imgs  = [p for p in all_samples if p.stem.startswith("fresh_")]
        rotten_imgs = [p for p in all_samples if p.stem.startswith("rotten_")]

        def _crop_label(path: Path) -> str:
            return path.stem.split("_", 1)[-1].replace("_", " ").title()

        def _render_row(imgs, row_label, color):
            st.markdown(
                f'<span style="font-weight:700;color:{color};font-size:.95rem">{row_label}</span>',
                unsafe_allow_html=True,
            )
            cols = st.columns(len(imgs))
            for col, img_path in zip(cols, imgs):
                with col:
                    is_selected = st.session_state.get("fd_selected_sample") == img_path.name
                    border = f"3px solid {color}" if is_selected else "2px solid transparent"
                    st.markdown(
                        f'<div style="border:{border};border-radius:8px;overflow:hidden">',
                        unsafe_allow_html=True,
                    )
                    st.image(str(img_path), use_container_width=True)
                    st.markdown('</div>', unsafe_allow_html=True)
                    btn_label = "✓ Selected" if is_selected else _crop_label(img_path)
                    if st.button(btn_label, key=f"btn_{img_path.stem}",
                                 use_container_width=True):
                        st.session_state["fd_selected_sample"] = img_path.name
                        st.rerun()

        _render_row(fresh_imgs,  "🟢  Fresh Produce",  "#28a745")
        st.markdown("")
        _render_row(rotten_imgs, "🔴  Rotten Produce", "#dc3545")

        selected_name = st.session_state.get("fd_selected_sample")
        if selected_name and (SAMPLE_DIR / selected_name).exists():
            pil_image = Image.open(SAMPLE_DIR / selected_name).convert("RGB")
        else:
            st.info("Click any image above to run prediction.")

    if pil_image:
        col_img, col_res = st.columns([1, 1.6])

        with col_img:
            st.image(pil_image, use_container_width=True, caption="Input image")

        with col_res:
            with st.spinner("Running freshness detection…"):
                detector = load_freshness_detector()
                result   = detector.predict_from_pil(pil_image)

            freshness  = result["freshness_status"]
            crop       = result["crop_type"].replace("_", " ").title()
            hindi      = result["hindi_label"]
            confidence = result["confidence"]
            grade      = result["quality_grade"]
            grade_up   = grade.upper()
            score      = result["freshness_score"]
            rec        = result["recommendations"]
            ext        = _compute_extended_metrics(result)
            damage     = ext["damage_score"]
            ripeness   = ext["ripeness_level"]

            # Status badge
            badge_cls = "badge-fresh" if freshness == "fresh" else "badge-rotten"
            icon      = "🟢" if freshness == "fresh" else "🔴"
            st.markdown(f"""
            <span class="{badge_cls}">{icon} {freshness.upper()}</span>
            &nbsp;&nbsp;
            <span style="font-size:1.2rem;font-weight:600">{crop}</span>
            &nbsp;
            <span style="color:#666">({hindi})</span>
            """, unsafe_allow_html=True)
            st.markdown("")

            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Confidence",      f"{confidence:.0%}")
            m2.metric("Quality Grade",   grade_up)
            m3.metric("Freshness",       f"{score}%")
            m4.metric("Damage",          f"{damage}%")

            st.markdown("")

            # ── Four metric progress bars ──────────────────────────
            def _bar(label, value, color, suffix="%"):
                st.markdown(f"""
                <div class="mbar-wrap">
                  <div class="mbar-label">
                    <span>{label}</span><span style="color:{color}">{value}{suffix}</span>
                  </div>
                  <div class="mbar-track">
                    <div class="mbar-fill" style="width:{value}%;background:{color}"></div>
                  </div>
                </div>""", unsafe_allow_html=True)

            freshness_color = "#28a745" if score >= 70 else ("#ffc107" if score >= 40 else "#dc3545")
            damage_color    = "#dc3545" if damage >= 60 else ("#ffc107" if damage >= 30 else "#28a745")
            ripeness_color  = "#2196f3" if ripeness >= 70 else ("#ffc107" if ripeness >= 40 else "#9e9e9e")

            _bar("🌿 Freshness",  score,    freshness_color)
            _bar("⚠️ Damage",     damage,   damage_color)
            _bar("🍃 Ripeness",   ripeness, ripeness_color)

            # ── Market price estimate ──────────────────────────────
            p_min  = ext["price_min"]
            p_max  = ext["price_max"]
            p_unit = ext["price_unit"]
            price_note = "🔴 Severely discounted (spoiled)" if freshness == "rotten" else \
                         f"✅ Grade {grade_up} market rate"
            st.markdown(f"""
            <div class="price-card" style="margin-top:.6rem">
              <div class="price-sub">Estimated Mandi Price</div>
              <div class="price-main">₹{p_min}–₹{p_max} / {p_unit}</div>
              <div class="price-sub">{price_note}</div>
            </div>
            """, unsafe_allow_html=True)

        # Recommendations
        st.markdown("---")
        col_en, col_hi = st.columns(2)
        urgency_color = {"low":"#28a745","medium":"#ffc107","high":"#ff9800","critical":"#dc3545"}
        urg = rec.get("urgency","low")

        with col_en:
            st.markdown("**📋 Recommendation (English)**")
            st.markdown(f"""
            <div style="background:#f8f9fa;border-left:4px solid {urgency_color.get(urg,'#2d9e5f')};
                        border-radius:6px;padding:.8rem 1rem;margin-bottom:.5rem">
                {rec['english']}
            </div>
            <div style="background:#f8f9fa;border-radius:6px;padding:.6rem 1rem;
                        font-size:.9rem;color:#555">
                🏪 <em>{rec.get('storage_advice_en','')}</em>
            </div>
            """, unsafe_allow_html=True)

        with col_hi:
            st.markdown("**📋 सिफ़ारिश (हिंदी)**")
            st.markdown(f"""
            <div style="background:#f8f9fa;border-left:4px solid {urgency_color.get(urg,'#2d9e5f')};
                        border-radius:6px;padding:.8rem 1rem;margin-bottom:.5rem">
                {rec['hindi']}
            </div>
            <div style="background:#f8f9fa;border-radius:6px;padding:.6rem 1rem;
                        font-size:.9rem;color:#555">
                🏪 <em>{rec.get('storage_advice_hi','')}</em>
            </div>
            """, unsafe_allow_html=True)

        # Top-K predictions
        with st.expander("🔬 Top model predictions"):
            top = result["top_predictions"]
            fig_top = go.Figure(go.Bar(
                x=[p["confidence"] for p in top],
                y=[f"{p['class']} ({p['hindi']})" for p in top],
                orientation="h",
                marker_color=["#28a745" if "fresh" in p["class"] else "#dc3545"
                              for p in top],
                text=[f"{p['confidence']:.1%}" for p in top],
                textposition="outside",
            ))
            fig_top.update_layout(
                xaxis=dict(range=[0,1], tickformat=".0%", showgrid=False),
                yaxis=dict(showgrid=False),
                height=200, margin=dict(l=10,r=10,t=10,b=10),
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            )
            st.plotly_chart(fig_top, use_container_width=True)
            st.caption(f"Inference time: {result['inference_time_ms']} ms")

    elif src == "📤 Upload photo":
        # Upload mode — nothing uploaded yet
        if SAMPLE_DIR.exists():
            all_s   = sorted(SAMPLE_DIR.glob("*.png"))
            fresh_s  = [p for p in all_s if p.stem.startswith("fresh_")]
            rotten_s = [p for p in all_s if p.stem.startswith("rotten_")]
            st.markdown("---")
            st.markdown("**Try a sample — or switch to *Use sample image* mode:**")
            st.markdown('<span style="font-weight:600;color:#28a745">🟢 Fresh</span>',
                        unsafe_allow_html=True)
            fc = st.columns(len(fresh_s))
            for col, p in zip(fc, fresh_s):
                col.image(str(p), caption=p.stem.split("_",1)[-1].title(),
                          use_container_width=True)
            st.markdown('<span style="font-weight:600;color:#dc3545">🔴 Rotten</span>',
                        unsafe_allow_html=True)
            rc = st.columns(len(rotten_s))
            for col, p in zip(rc, rotten_s):
                col.image(str(p), caption=p.stem.split("_",1)[-1].title(),
                          use_container_width=True)


# ══════════════════════════════════════════════════════════════════
# PAGE 2 — SPOILAGE PREDICTION
# ══════════════════════════════════════════════════════════════════
elif page == "📦 Spoilage Prediction":

    st.markdown("### 📦 Spoilage Prediction")
    st.markdown(
        "Enter current storage conditions. The XGBoost model predicts spoilage "
        "probability, remaining shelf life, and risk level."
    )

    CROPS = sorted(CROP_PROFILES.keys())
    CROP_DISPLAY = {c: f"{c.title()} — {CROP_PROFILES[c]['hindi']}" for c in CROPS}

    # ── Sidebar controls ──────────────────────────────────────────
    with st.sidebar:
        st.markdown("## 🌿 Storage Conditions")

        crop = st.selectbox("Crop", CROPS,
                            format_func=lambda c: CROP_DISPLAY[c],
                            index=CROPS.index("tomato"))
        profile  = CROP_PROFILES[crop]
        opt_temp = profile["optimal_temp"]
        opt_hum  = profile["optimal_humidity"]

        st.markdown(f"<small style='color:#666'>Optimal: <b>{opt_temp[0]}–{opt_temp[1]}°C</b> | "
                    f"<b>{opt_hum[0]}–{opt_hum[1]}%</b> humidity</small>", unsafe_allow_html=True)

        temperature      = st.slider("Temperature (°C)", -5, 50, 30)
        humidity         = st.slider("Humidity (%)", 20, 100, 65)
        days_harvest     = st.slider("Days Since Harvest", 0, 30, 3)
        storage_type     = st.radio("Storage", ["ambient","cold"], horizontal=True,
                                    format_func=lambda x: "🌡️ Ambient" if x=="ambient" else "❄️ Cold")
        transport_hours  = st.slider("Transport (hours)", 0, 24, 2)
        initial_quality  = st.slider("Initial Quality", 50, 100, 85)

        st.markdown("---")
        use_bedrock = st.toggle("🤖 Bedrock Explanations", value=False)
        if use_bedrock:
            st.markdown('<span class="aws-badge">☁️ Amazon Bedrock</span>', unsafe_allow_html=True)

        predict_btn = st.button("🔍 Predict", type="primary", use_container_width=True)

    # ── Run prediction ────────────────────────────────────────────
    predictor = load_spoilage_predictor()
    if use_bedrock and not predictor.use_bedrock:
        predictor.use_bedrock = True
        try:
            from bedrock_explainer import BedrockExplainer
            predictor._explainer = BedrockExplainer()
        except Exception:
            predictor.use_bedrock = False
    elif not use_bedrock:
        predictor.use_bedrock = False

    result = predictor.predict(
        crop=crop, temperature=temperature, humidity=humidity,
        days_since_harvest=days_harvest, storage_type=storage_type,
        transport_hours=transport_hours, initial_quality=initial_quality,
    )
    st.session_state["sp_result"] = result

    risk      = result["risk_level"]
    prob      = result["spoilage_probability"]
    remaining = result["remaining_shelf_life_days"]
    icon      = result["risk_icon"]

    # Risk banner
    st.markdown(f"""
    <div class="risk-card risk-{risk}">
        {icon} &nbsp;
        {result['crop_hindi']} ({crop.title()}) &nbsp;—&nbsp;
        <span style="text-transform:uppercase">{risk} RISK</span>
        &nbsp;|&nbsp; Spoilage: {prob:.0%}
        &nbsp;|&nbsp; {remaining:.0f} days remaining
    </div>
    """, unsafe_allow_html=True)

    col_metrics = st.columns(4)
    col_metrics[0].metric("Risk Level",   risk.upper())
    col_metrics[1].metric("Probability",  f"{prob:.0%}")
    col_metrics[2].metric("Shelf Life",   f"{remaining:.0f} days")
    col_metrics[3].metric("Storage",      storage_type.title())

    st.markdown("---")
    col_left, col_right = st.columns([1, 1])

    # Charts
    with col_left:
        # Risk probability bar
        rp = result["risk_probabilities"]
        fig_r = go.Figure(go.Bar(
            x=list(rp.values()),
            y=[l.upper() for l in rp.keys()],
            orientation="h",
            marker_color=[RISK_COLORS[l] for l in rp.keys()],
            text=[f"{v:.1%}" for v in rp.values()],
            textposition="outside",
        ))
        fig_r.update_layout(
            title="Risk Probability Breakdown",
            xaxis=dict(range=[0,1], tickformat=".0%", showgrid=False),
            yaxis=dict(showgrid=False),
            height=220, margin=dict(l=10,r=10,t=40,b=10),
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig_r, use_container_width=True)

        # Conditions vs optimal
        opt_mid_t = sum(opt_temp) / 2
        opt_mid_h = sum(opt_hum)  / 2
        fig_c = go.Figure()
        fig_c.add_trace(go.Bar(
            name="Current",
            x=["Temperature (°C)", "Humidity (%)"],
            y=[temperature, humidity],
            marker_color=["#dc3545" if abs(temperature-opt_mid_t)>5 else "#28a745",
                          "#dc3545" if abs(humidity-opt_mid_h)>5    else "#28a745"],
            text=[f"{temperature}°C", f"{humidity}%"], textposition="outside",
        ))
        fig_c.add_trace(go.Bar(
            name="Optimal",
            x=["Temperature (°C)", "Humidity (%)"],
            y=[opt_mid_t, opt_mid_h],
            marker_color=["rgba(45,158,95,.4)","rgba(45,158,95,.4)"],
            text=[f"{opt_mid_t:.0f}°C", f"{opt_mid_h:.0f}%"], textposition="outside",
        ))
        fig_c.update_layout(
            title="Current vs Optimal Conditions", barmode="group",
            height=230, margin=dict(l=10,r=10,t=40,b=10),
            legend=dict(orientation="h", y=-0.25),
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            yaxis=dict(showgrid=False),
        )
        st.plotly_chart(fig_c, use_container_width=True)

    # Recommendations
    with col_right:
        st.markdown("#### 📋 Recommendations")
        for rec in result["recommendations"]:
            urg = rec.get("urgency","none")
            cls = urg if urg in ("critical","high","moderate") else ""
            st.markdown(f"""
            <div class="rec-card {cls}">
                <div style="font-weight:600">{rec.get('icon','→')} {rec['en']}</div>
                <div style="font-size:.9rem;color:#555;margin-top:3px">{rec['hi']}</div>
            </div>
            """, unsafe_allow_html=True)

    # Explanation
    st.markdown("---")
    st.markdown("#### 🧠 Causal Explanation")
    exp    = result["explanation"]
    source = result.get("explanation_source","template-based")
    badge  = ('<span class="aws-badge">☁️ Amazon Bedrock</span>'
              if "Bedrock" in source else
              '<span class="tmpl-badge">📄 Template-based</span>')

    col_en, col_hi = st.columns(2)
    with col_en:
        st.markdown(f"""
        <div class="expl-box">
            <strong>🇬🇧 English</strong><br><br>{exp['en']}<br><br>{badge}
        </div>""", unsafe_allow_html=True)
    with col_hi:
        st.markdown(f"""
        <div class="expl-box">
            <strong>🇮🇳 हिंदी</strong><br><br>{exp['hi']}
        </div>""", unsafe_allow_html=True)

    if "key_causes" in exp and exp["key_causes"]:
        with st.expander("Key causes identified by model"):
            for c in exp["key_causes"]:
                st.markdown(f"  - {c}")

    # What-if
    st.markdown("---")
    with st.expander("🔄 What-If Analysis"):
        st.markdown("Propose a change and see how it affects the prediction.")
        wi_c1, wi_c2 = st.columns(2)
        with wi_c1:
            new_temp    = st.slider("New Temperature", -5, 50, int(temperature), key="wi_t")
            new_hum     = st.slider("New Humidity",    20, 100, int(humidity),    key="wi_h")
        with wi_c2:
            new_stor    = st.radio("New Storage", ["ambient","cold"], key="wi_s",
                                   format_func=lambda x: "🌡️ Ambient" if x=="ambient" else "❄️ Cold")
            new_trans   = st.slider("New Transport (h)", 0, 24, int(transport_hours), key="wi_tr")

        quick1, quick2, quick3 = st.columns(3)
        if quick1.button("❄️ Optimal Cold Storage"):
            st.session_state["wi_t"] = int(sum(opt_temp)/2)
            st.session_state["wi_h"] = int(sum(opt_hum)/2)
            st.session_state["wi_s"] = "cold"
            st.rerun()
        if quick2.button("💧 Fix Humidity"):
            st.session_state["wi_h"] = int(sum(opt_hum)/2)
            st.rerun()
        if quick3.button("🚚 Halve Transport"):
            st.session_state["wi_tr"] = max(0, int(transport_hours)//2)
            st.rerun()

        if st.button("⚡ Run What-If", type="primary"):
            changes = {}
            if new_temp  != temperature:     changes["temperature"]     = new_temp
            if new_hum   != humidity:        changes["humidity"]        = new_hum
            if new_stor  != storage_type:    changes["storage_type"]    = new_stor
            if new_trans != transport_hours: changes["transport_hours"] = new_trans

            if not changes:
                st.warning("No changes detected.")
            else:
                wi = predictor.whatif(result, changes)
                st.session_state["wi_result"] = wi

        if "wi_result" in st.session_state:
            wi  = st.session_state["wi_result"]
            imp = wi.get("improvement", False)
            tag = "✅ IMPROVEMENT" if imp else "⚠️ WORSENING"
            color = "#28a745" if imp else "#dc3545"

            st.markdown(f"""
            <div style="display:flex;gap:1rem;margin:.5rem 0">
                <div style="flex:1;background:{RISK_BG[wi['before']['risk_level']]};
                            border-radius:8px;padding:.7rem 1rem;text-align:center">
                    <strong>Before</strong><br>
                    {wi['before']['risk_level'].upper()}<br>
                    {wi['before']['spoilage_probability']:.0%} &nbsp;·&nbsp;
                    {wi['before']['remaining_days']:.0f}d
                </div>
                <div style="display:flex;align-items:center;font-size:1.5rem">→</div>
                <div style="flex:1;background:{RISK_BG[wi['after']['risk_level']]};
                            border-radius:8px;padding:.7rem 1rem;text-align:center">
                    <strong>After</strong><br>
                    {wi['after']['risk_level'].upper()}<br>
                    {wi['after']['spoilage_probability']:.0%} &nbsp;·&nbsp;
                    {wi['after']['remaining_days']:.0f}d
                </div>
            </div>
            <div style="background:{color};color:white;border-radius:8px;
                        padding:.4rem 1rem;text-align:center;font-weight:bold;margin-bottom:.5rem">
                {tag} — {wi['impact_summary']}
            </div>
            """, unsafe_allow_html=True)

            wc1, wc2 = st.columns(2)
            wc1.markdown(f'<div class="expl-box"><strong>EN</strong><br><br>{wi["en"]}</div>',
                         unsafe_allow_html=True)
            wc2.markdown(f'<div class="expl-box"><strong>HI</strong><br><br>{wi["hi"]}</div>',
                         unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════
# PAGE 3 — DASHBOARD
# ══════════════════════════════════════════════════════════════════
elif page == "📊 Dashboard":

    st.markdown("### 📊 Pre-computed Demo Results")
    st.markdown("10 diverse crop scenarios across all risk levels.")

    demo_file = SPOILAGE_DIR / "data" / "demo_results.json"
    if not demo_file.exists():
        st.error(f"Demo results not found at `{demo_file}`. "
                 "Run `python inference.py` inside `spoilage_prediction/` first.")
        st.stop()

    with open(demo_file) as f:
        batch = json.load(f)

    # Summary table
    rows = [{
        "Crop":          r["crop"].title(),
        "Hindi":         r["crop_hindi"],
        "Risk":          r["risk_level"].upper(),
        "Prob (%)":      f"{r['spoilage_probability']:.0%}",
        "Life (days)":   int(r["remaining_shelf_life_days"]),
        "Temp (°C)":     r["input_summary"]["temperature_c"],
        "Humidity (%)":  r["input_summary"]["humidity_pct"],
        "Storage":       r["input_summary"]["storage_type"],
    } for r in batch]

    df = pd.DataFrame(rows)
    RISK_CELL = {"LOW":"background-color:#d4edda;color:#155724",
                 "MEDIUM":"background-color:#fff3cd;color:#856404",
                 "HIGH":"background-color:#ffe0b2;color:#7b3f00",
                 "CRITICAL":"background-color:#f8d7da;color:#721c24"}

    st.dataframe(
        df.style.applymap(lambda v: RISK_CELL.get(v,""), subset=["Risk"])
                .set_properties(**{"text-align":"center"}),
        use_container_width=True, hide_index=True,
    )

    st.markdown("---")
    col_pie, col_bar = st.columns(2)

    with col_pie:
        rc = df["Risk"].value_counts()
        fig_pie = go.Figure(go.Pie(
            labels=rc.index, values=rc.values,
            marker_colors=[RISK_COLORS[r.lower()] for r in rc.index],
            hole=0.45, textinfo="label+percent",
        ))
        fig_pie.update_layout(title="Risk Distribution", height=280,
                               margin=dict(l=10,r=10,t=40,b=10),
                               paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig_pie, use_container_width=True)

    with col_bar:
        bs = sorted(batch, key=lambda r: r["spoilage_probability"], reverse=True)
        fig_bar = go.Figure(go.Bar(
            x=[r["crop"].title() for r in bs],
            y=[r["spoilage_probability"] for r in bs],
            marker_color=[RISK_COLORS[r["risk_level"]] for r in bs],
            text=[f"{r['spoilage_probability']:.0%}" for r in bs],
            textposition="outside",
        ))
        fig_bar.update_layout(
            title="Spoilage Probability by Crop",
            yaxis=dict(tickformat=".0%", range=[0,1.2], showgrid=False),
            xaxis=dict(tickangle=-30), height=280,
            margin=dict(l=10,r=10,t=40,b=60),
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    # Scatter
    st.markdown("#### Shelf Life vs Spoilage Probability")
    scatter_df = pd.DataFrame([{
        "Crop":            r["crop"].title(),
        "Shelf Life (d)":  r["remaining_shelf_life_days"],
        "Spoilage Prob":   r["spoilage_probability"],
        "Risk":            r["risk_level"].upper(),
        "Storage":         r["input_summary"]["storage_type"],
        "Temp":            r["input_summary"]["temperature_c"],
    } for r in batch])

    fig_sc = px.scatter(
        scatter_df, x="Shelf Life (d)", y="Spoilage Prob",
        color="Risk", size="Temp", text="Crop",
        color_discrete_map={"LOW":"#28a745","MEDIUM":"#ffc107",
                            "HIGH":"#ff9800","CRITICAL":"#dc3545"},
        hover_data=["Storage","Temp"],
    )
    fig_sc.update_traces(textposition="top center")
    fig_sc.update_layout(
        yaxis=dict(tickformat=".0%", showgrid=False),
        xaxis=dict(showgrid=False),
        height=380, margin=dict(l=10,r=10,t=20,b=10),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig_sc, use_container_width=True)

    # ── About strip ──────────────────────────────────────────────
    st.markdown("---")
    c1, c2, c3 = st.columns(3)
    c1.markdown("""
**🥦 Freshness Detection**
- MobileNetV2 CNN
- 26 classes (13 crops × fresh/rotten)
- Input: photo (jpg/png)
- Output: fresh/rotten, confidence, quality grade
    """)
    c2.markdown("""
**📦 Spoilage Prediction**
- XGBoost (3 sub-models)
- 16 Indian crops
- Input: storage conditions
- Output: days, probability, risk level
    """)
    c3.markdown("""
**☁️ AWS Services**
- Amazon Bedrock (Claude 3) — Explainability
- Amazon SageMaker — Model endpoints
- Region: ap-south-1
    """)

# ── Footer ──────────────────────────────────────────────────────
st.markdown("""
<div style="text-align:center;color:#888;font-size:.8rem;padding:1.5rem 0 0">
    SwadeshAI &nbsp;·&nbsp; AWS AI for Bharat Hackathon &nbsp;·&nbsp;
    MobileNetV2 · XGBoost · Amazon Bedrock · Amazon SageMaker · Streamlit
</div>
""", unsafe_allow_html=True)

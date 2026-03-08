"""
SwadeshAI — Freshness → Price Recommendation Demo
Hackathon demo: AWS AI for Bharat Hackathon

Full pipeline:
    📸 Upload Photo → 🔬 AI Freshness Detection → 💰 Mandi-Grounded Price Recommendation

Run with:
    cd SwadeshAI/backend
    PYTHONPATH=. streamlit run demo_quality_price.py
"""

import sys
import asyncio
from pathlib import Path

import streamlit as st
import plotly.graph_objects as go

# ── Path setup ──────────────────────────────────────────────────────
sys.path.insert(0, str(Path(__file__).parent))

from app.services.quality_service import quality_service
from app.services.pricing_service import pricing_service
from app.services.mandi_service import mandi_client, _cache


# ── Page config ─────────────────────────────────────────────────────
st.set_page_config(
    page_title="SwadeshAI — Quality → Price",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ───────────────────────────────────────────────────────
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #1a6b3c 0%, #2d9e5f 50%, #f7a800 100%);
        padding: 1.5rem 2rem;
        border-radius: 12px;
        margin-bottom: 1.5rem;
        color: white;
    }
    .main-header h1 { margin: 0; font-size: 2rem; }
    .main-header p  { margin: 0.25rem 0 0; opacity: 0.9; font-size: 1rem; }

    .grade-excellent { background: #d4edda; border-left: 5px solid #28a745; }
    .grade-good      { background: #cce5ff; border-left: 5px solid #007bff; }
    .grade-average   { background: #fff3cd; border-left: 5px solid #ffc107; }
    .grade-poor      { background: #f8d7da; border-left: 5px solid #dc3545; }

    .price-card {
        background: #f0f7ff;
        border: 1px solid #bee3f8;
        border-radius: 12px;
        padding: 1.25rem;
        text-align: center;
    }
    .price-card .label { font-size: 0.8rem; color: #4a5568; text-transform: uppercase; }
    .price-card .value { font-size: 2.2rem; font-weight: bold; color: #1a6b3c; }
    .price-card .sub   { font-size: 0.85rem; color: #718096; }

    .pipeline-step {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 0.75rem 1rem;
        text-align: center;
        font-weight: 600;
    }
    .pipeline-arrow { text-align: center; font-size: 1.5rem; padding-top: 0.5rem; color: #a0aec0; }

    .mandi-row {
        background: #f8f9fa;
        border-radius: 6px;
        padding: 0.5rem 0.75rem;
        margin-bottom: 0.35rem;
        border-left: 3px solid #2d9e5f;
    }

    .quality-note {
        background: #edf2f7;
        border-radius: 8px;
        padding: 1rem;
        margin-top: 0.5rem;
        font-size: 0.95rem;
    }
</style>
""", unsafe_allow_html=True)


# ── Header ──────────────────────────────────────────────────────────
st.markdown("""
<div class="main-header">
    <h1>🌾 SwadeshAI — Quality → Price Recommendation</h1>
    <p>📸 Upload a photo of your produce → 🔬 AI detects freshness →
       💰 Get mandi-grounded price recommendation</p>
</div>
""", unsafe_allow_html=True)

# ── Pipeline visual ─────────────────────────────────────────────────
p1, pa1, p2, pa2, p3, pa3, p4 = st.columns([1, 0.3, 1, 0.3, 1, 0.3, 1])
with p1:
    st.markdown('<div class="pipeline-step">📸 Upload<br>Produce Photo</div>', unsafe_allow_html=True)
with pa1:
    st.markdown('<div class="pipeline-arrow">→</div>', unsafe_allow_html=True)
with p2:
    st.markdown('<div class="pipeline-step">🔬 AI Freshness<br>Detection</div>', unsafe_allow_html=True)
with pa2:
    st.markdown('<div class="pipeline-arrow">→</div>', unsafe_allow_html=True)
with p3:
    st.markdown('<div class="pipeline-step">📊 Live Mandi<br>Prices</div>', unsafe_allow_html=True)
with pa3:
    st.markdown('<div class="pipeline-arrow">→</div>', unsafe_allow_html=True)
with p4:
    st.markdown('<div class="pipeline-step">💰 Price<br>Recommendation</div>', unsafe_allow_html=True)

st.markdown("---")

# ── Supported crops ─────────────────────────────────────────────────
SUPPORTED_CROPS = [
    "apple", "banana", "bell_pepper", "bitter_gourd", "capsicum",
    "carrot", "cucumber", "mango", "okra", "orange",
    "potato", "strawberry", "tomato",
]

CROP_HINDI = {
    "apple": "सेब", "banana": "केला", "bell_pepper": "शिमला मिर्च",
    "bitter_gourd": "करेला", "capsicum": "शिमला मिर्च", "carrot": "गाजर",
    "cucumber": "खीरा", "mango": "आम", "okra": "भिंडी",
    "orange": "संतरा", "potato": "आलू", "strawberry": "स्ट्रॉबेरी",
    "tomato": "टमाटर",
}

GRADE_COLORS = {
    "excellent": "#28a745",
    "good": "#007bff",
    "average": "#ffc107",
    "poor": "#dc3545",
}

GRADE_TO_SPOILAGE = {
    "excellent": "low",
    "good": "low",
    "average": "medium",
    "poor": "high",
}


# ── Sidebar ─────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🌿 Produce Details")

    crop_name = st.selectbox(
        "Crop",
        options=SUPPORTED_CROPS,
        format_func=lambda c: f"{c.replace('_', ' ').title()} — {CROP_HINDI.get(c, '')}",
        index=SUPPORTED_CROPS.index("tomato"),
    )

    quantity_kg = st.number_input("Quantity (kg)", min_value=1.0, value=100.0, step=10.0)

    storage_type = st.radio(
        "Storage Type",
        options=["ambient", "cold", "controlled"],
        format_func=lambda x: {"ambient": "🌡️ Ambient", "cold": "❄️ Cold Storage", "controlled": "🔬 Controlled"}[x],
        horizontal=True,
    )

    state_filter = st.text_input(
        "State (for mandi prices)",
        placeholder="e.g. Maharashtra, Karnataka",
        help="Leave empty for nationwide prices",
    )

    st.markdown("---")
    st.markdown("### 📷 Upload Image")
    uploaded_file = st.file_uploader(
        "Upload produce photo",
        type=["jpg", "jpeg", "png", "webp"],
        help="Take a clear photo of your produce for quality assessment",
    )

    use_simulation = st.toggle(
        "🎲 Use Simulated Quality",
        value=False,
        help="Skip image upload — use simulated quality grades for demo",
    )

    run_btn = st.button("🔍 Analyze & Get Price", type="primary", width="stretch")


# ── Main area ───────────────────────────────────────────────────────
tab_result, tab_mandi, tab_about = st.tabs([
    "📊 Quality + Price Result",
    "🏪 Live Mandi Prices",
    "ℹ️ About",
])


def run_analysis():
    """Run the full quality → price pipeline."""
    with st.spinner("🔬 Analyzing produce quality..."):
        if use_simulation or uploaded_file is None:
            quality_result = quality_service._simulate_assessment(crop_name)
            quality_result["_simulated"] = True
        else:
            image_bytes = uploaded_file.read()
            loop = asyncio.new_event_loop()
            try:
                quality_result = loop.run_until_complete(
                    quality_service.assess_quality_from_image(image_bytes, crop_name)
                )
            finally:
                loop.close()
            quality_result["_simulated"] = False

    with st.spinner("💰 Generating price recommendation..."):
        quality_grade = quality_result["overall_grade"]
        spoilage_risk = GRADE_TO_SPOILAGE.get(quality_grade, "medium")

        price_rec = pricing_service.generate_price_recommendation(
            crop_name=crop_name,
            quantity_kg=quantity_kg,
            quality_grade=quality_grade,
            spoilage_risk=spoilage_risk,
            storage_type=storage_type,
        )

    with st.spinner("📊 Fetching live mandi prices..."):
        _cache.clear()
        state = state_filter.strip() if state_filter else None
        mandi_result = mandi_client.fetch_prices_sync(
            crop_name, state=state, limit=20,
        )

    return quality_result, price_rec, mandi_result


# ── Run & cache results ─────────────────────────────────────────────
if run_btn or "last_analysis" not in st.session_state:
    if not use_simulation and uploaded_file is None and run_btn:
        st.warning("Please upload a produce photo or enable 'Use Simulated Quality'")
        st.stop()

    if use_simulation or uploaded_file is not None:
        quality_result, price_rec, mandi_result = run_analysis()
        st.session_state["last_analysis"] = (quality_result, price_rec, mandi_result)
    elif "last_analysis" not in st.session_state:
        # First load with simulation
        quality_result = quality_service._simulate_assessment(crop_name)
        quality_result["_simulated"] = True
        quality_grade = quality_result["overall_grade"]
        spoilage_risk = GRADE_TO_SPOILAGE.get(quality_grade, "medium")
        price_rec = pricing_service.generate_price_recommendation(
            crop_name=crop_name, quantity_kg=quantity_kg,
            quality_grade=quality_grade, spoilage_risk=spoilage_risk,
            storage_type=storage_type,
        )
        mandi_result = mandi_client.fetch_prices_sync(crop_name, limit=20)
        st.session_state["last_analysis"] = (quality_result, price_rec, mandi_result)

if "last_analysis" in st.session_state:
    quality_result, price_rec, mandi_result = st.session_state["last_analysis"]
else:
    st.info("Configure your produce details in the sidebar and click 'Analyze & Get Price'")
    st.stop()


# ═══════════════════════════════════════════════════════════
# TAB 1: Quality + Price Result
# ═══════════════════════════════════════════════════════════
with tab_result:
    grade = quality_result["overall_grade"]
    grade_color = GRADE_COLORS.get(grade, "#6c757d")
    is_sim = quality_result.get("_simulated", False)

    # ── Quality Assessment Card ──────────────────────────────
    st.markdown("### 🔬 Quality Assessment")
    if is_sim:
        st.caption("⚠️ Simulated quality — upload a real photo for accurate assessment")

    # Show uploaded image if available
    if uploaded_file is not None and not is_sim:
        col_img, col_quality = st.columns([1, 2])
        with col_img:
            uploaded_file.seek(0)
            st.image(uploaded_file, caption=f"{crop_name.replace('_', ' ').title()}", width="stretch")
    else:
        col_quality = st.container()

    with col_quality if uploaded_file and not is_sim else st.container():
        q1, q2, q3, q4 = st.columns(4)
        with q1:
            st.metric("Quality Grade", grade.upper())
        with q2:
            st.metric("Quality Score", f"{quality_result['quality_score']}/100")
        with q3:
            st.metric("Freshness", quality_result.get("freshness_status", "N/A").title())
        with q4:
            st.metric("Ripeness", quality_result.get("ripeness_level", "N/A").title())

        # Quality gauge
        fig_q = go.Figure(go.Indicator(
            mode="gauge+number",
            value=quality_result["quality_score"],
            title={"text": "Quality Score"},
            gauge={
                "axis": {"range": [0, 100]},
                "bar": {"color": grade_color},
                "steps": [
                    {"range": [0, 40], "color": "#f8d7da"},
                    {"range": [40, 65], "color": "#fff3cd"},
                    {"range": [65, 85], "color": "#cce5ff"},
                    {"range": [85, 100], "color": "#d4edda"},
                ],
                "threshold": {
                    "line": {"color": "black", "width": 3},
                    "value": quality_result["quality_score"],
                },
            },
        ))
        fig_q.update_layout(height=220, margin=dict(l=20, r=20, t=40, b=10))
        st.plotly_chart(fig_q, width="stretch", key="quality_gauge")

    # Defects
    defects = quality_result.get("defects_detected", [])
    if defects:
        st.warning(f"**Defects detected:** {', '.join(defects)}")

    # Recommendations from quality service
    recs = quality_result.get("recommendations", {})
    if recs:
        rec_en = recs.get("english", "")
        rec_hi = recs.get("hindi", "")
        if rec_en:
            col_en, col_hi = st.columns(2)
            with col_en:
                st.info(f"🇬🇧 {rec_en}")
            with col_hi:
                if rec_hi:
                    st.info(f"🇮🇳 {rec_hi}")

    st.markdown("---")

    # ── Price Recommendation Card ────────────────────────────
    st.markdown("### 💰 Price Recommendation")

    source = price_rec.get("price_source", "simulated")
    source_badge = (
        '<span style="background:#28a745;color:white;padding:0.2rem 0.5rem;'
        'border-radius:4px;font-size:0.75rem;font-weight:bold">'
        '📡 Live Mandi Data</span>'
        if source == "data.gov.in" else
        '<span style="background:#6c757d;color:white;padding:0.2rem 0.5rem;'
        'border-radius:4px;font-size:0.75rem;font-weight:bold">'
        '🔄 Simulated Data</span>'
    )
    model_badge = (
        '<span style="background:#007bff;color:white;padding:0.2rem 0.5rem;'
        'border-radius:4px;font-size:0.75rem;font-weight:bold">'
        f'🧠 {price_rec.get("model_type", "xgboost").upper()}</span>'
    )
    st.markdown(f"Data Source: {source_badge} &nbsp;&nbsp; Model: {model_badge}", unsafe_allow_html=True)

    # Price cards
    pc1, pc2, pc3 = st.columns(3)
    with pc1:
        st.markdown(f"""
        <div class="price-card">
            <div class="label">Floor Price (Seller-Protected)</div>
            <div class="value">₹{price_rec['recommended_min_price']}</div>
            <div class="sub">per kg</div>
        </div>
        """, unsafe_allow_html=True)
    with pc2:
        st.markdown(f"""
        <div class="price-card" style="border: 2px solid #1a6b3c;">
            <div class="label">⭐ Ideal Price</div>
            <div class="value" style="color:#1a6b3c">₹{price_rec['ideal_price']}</div>
            <div class="sub">per kg (AI recommended)</div>
        </div>
        """, unsafe_allow_html=True)
    with pc3:
        st.markdown(f"""
        <div class="price-card">
            <div class="label">Upper Range</div>
            <div class="value">₹{price_rec['price_range_upper']}</div>
            <div class="sub">per kg</div>
        </div>
        """, unsafe_allow_html=True)

    # Total value estimate
    ideal = price_rec["ideal_price"]
    total_value = round(ideal * quantity_kg, 2)
    st.markdown(f"""
    <div class="quality-note" style="text-align:center;font-size:1.1rem">
        📦 <strong>{quantity_kg:.0f} kg</strong> of {crop_name.replace('_', ' ').title()}
        &nbsp;×&nbsp; ₹{ideal}/kg &nbsp;=&nbsp;
        <strong style="color:#1a6b3c;font-size:1.3rem">₹{total_value:,.2f}</strong>
        estimated value
    </div>
    """, unsafe_allow_html=True)

    # Action recommendation
    action = price_rec.get("action", "sell_now")
    action_text = price_rec.get("action_text", "")
    action_icons = {"sell_now": "🟢", "wait": "🟡", "store": "🔵"}
    st.markdown(f"""
    <div class="quality-note">
        <strong>{action_icons.get(action, '→')} Action: {action.replace('_', ' ').upper()}</strong>
        <br>{action_text}
    </div>
    """, unsafe_allow_html=True)

    # Quality-based price note
    grade_note = {
        "excellent": f"✅ Excellent quality detected! Your produce can command premium prices. Ideal: ₹{ideal}/kg.",
        "good": f"👍 Good quality produce. Fair market rates expected. Recommended: ₹{ideal}/kg.",
        "average": f"⚠️ Average quality — sell quickly before further deterioration. Realistic price: ₹{ideal}/kg.",
        "poor": f"❌ Poor quality — sell immediately or route to processing units. Expected: ₹{ideal}/kg.",
    }
    st.markdown(f"""
    <div class="quality-note grade-{grade}">
        {grade_note.get(grade, '')}
    </div>
    """, unsafe_allow_html=True)

    # MSP note
    msp = price_rec.get("msp_note")
    if msp:
        st.success(msp)

    # What-if scenarios
    whatifs = price_rec.get("what_if_scenarios", [])
    if whatifs:
        st.markdown("#### 🔄 What-If Scenarios")
        for wi in whatifs:
            st.markdown(f"""
            <div class="mandi-row">
                <strong>{wi['scenario']}</strong><br>
                Price change: {wi['price_change']} → New ideal: ₹{wi['new_ideal_price']}/kg<br>
                <em>{wi['recommendation']}</em>
            </div>
            """, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════
# TAB 2: Live Mandi Prices
# ═══════════════════════════════════════════════════════════
with tab_mandi:
    st.markdown("### 🏪 Live Mandi Prices from data.gov.in")

    records = mandi_result.get("records", [])
    total = mandi_result.get("total", 0)
    api_error = mandi_result.get("api_error")

    if api_error:
        st.warning(f"⚠️ API issue: {api_error}. Showing cached or simulated data.")

    if not records:
        st.info("No mandi price records available. Check your MANDI_API_KEY in .env")
    else:
        st.markdown(f"**{len(records)} mandis** reporting (out of {total} total)")

        # Summary metrics
        modals = [r["modal_price_per_kg"] for r in records]
        mins = [r["min_price_per_kg"] for r in records]
        maxs = [r["max_price_per_kg"] for r in records]

        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.metric("Avg Price", f"₹{sum(modals)/len(modals):.2f}/kg")
        with m2:
            st.metric("Lowest", f"₹{min(mins):.2f}/kg")
        with m3:
            st.metric("Highest", f"₹{max(maxs):.2f}/kg")
        with m4:
            states = list({r.get("state", "") for r in records})
            st.metric("States", len(states))

        # Mandi price chart
        sorted_records = sorted(records, key=lambda x: -x["modal_price_per_kg"])

        fig_mandi = go.Figure()
        fig_mandi.add_trace(go.Bar(
            x=[f"{r['market']}, {r['state']}" for r in sorted_records[:15]],
            y=[r["modal_price_per_kg"] for r in sorted_records[:15]],
            marker_color="#2d9e5f",
            text=[f"₹{r['modal_price_per_kg']}" for r in sorted_records[:15]],
            textposition="outside",
            hovertemplate="%{x}<br>₹%{y}/kg<extra></extra>",
        ))
        fig_mandi.update_layout(
            title=f"Mandi Prices for {crop_name.replace('_', ' ').title()} (₹/kg)",
            yaxis=dict(title="Price (₹/kg)", showgrid=False),
            xaxis=dict(tickangle=-40),
            margin=dict(l=10, r=10, t=40, b=80),
            height=400,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig_mandi, width="stretch", key="mandi_chart")

        # Table
        st.markdown("#### Detailed Prices")
        for r in sorted_records:
            st.markdown(f"""
            <div class="mandi-row">
                <strong>{r['market']}</strong>, {r['district']}, {r['state']}
                &nbsp;—&nbsp;
                ₹{r['modal_price_per_kg']}/kg
                (Min: ₹{r['min_price_per_kg']}, Max: ₹{r['max_price_per_kg']})
                &nbsp;|&nbsp; {r.get('variety', '')}
                &nbsp;|&nbsp; {r.get('arrival_date', '')}
            </div>
            """, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════
# TAB 3: About
# ═══════════════════════════════════════════════════════════
with tab_about:
    st.markdown("### ℹ️ About This Demo")

    col_a, col_b = st.columns(2)

    with col_a:
        st.markdown("""
**Full Pipeline**
1. **📸 Image Upload** — Farmer takes a photo of their produce
2. **🔬 AI Quality Detection** — MobileNetV2 model classifies freshness
   - Fresh vs Rotten detection (26 classes)
   - Quality grading: Excellent / Good / Average / Poor
   - Defect detection and ripeness estimation
3. **📊 Live Mandi Prices** — data.gov.in API fetches daily prices
   - 200+ mandis across India
   - Real-time commodity prices (₹/quintal → ₹/kg)
4. **💰 Price Recommendation** — XGBoost ML model
   - Quality-adjusted pricing (fresh = premium, damaged = discount)
   - Seller-protected floor price (MSP-aware)
   - 3-day price forecast
   - What-if scenarios

**Quality → Price Mapping**

| Quality Grade | Spoilage Risk | Price Impact |
|--------------|---------------|--------------|
| Excellent | Low | Premium (+15-20%) |
| Good | Low | Market rate |
| Average | Medium | Below market (-10%) |
| Poor | High | Steep discount (-25%+) |
        """)

    with col_b:
        st.markdown("""
**Supported Crops (13)**

| Produce | Hindi |
|---------|-------|
| Apple | सेब |
| Banana | केला |
| Bell Pepper | शिमला मिर्च |
| Carrot | गाजर |
| Cucumber | खीरा |
| Mango | आम |
| Okra | भिंडी |
| Orange | संतरा |
| Potato | आलू |
| Strawberry | स्ट्रॉबेरी |
| Tomato | टमाटर |

**AWS Services**

| Service | Role |
|---------|------|
| SageMaker | MobileNetV2 freshness model hosting |
| Bedrock | Causal explanations (Hindi + English) |
| data.gov.in | Live mandi commodity prices |

**Tech Stack**: FastAPI · XGBoost · MobileNetV2 · ONNX · Streamlit
        """)

    st.markdown("---")
    st.markdown("""
    <div style="text-align:center; color:#888; font-size:0.85rem; padding:1rem">
        SwadeshAI &nbsp;|&nbsp; AWS AI for Bharat Hackathon &nbsp;|&nbsp;
        Freshness Detection + Mandi Pricing Pipeline
    </div>
    """, unsafe_allow_html=True)

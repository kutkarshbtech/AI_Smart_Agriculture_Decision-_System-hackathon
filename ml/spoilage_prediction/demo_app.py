"""
SwadeshAI — Spoilage Prediction Demo App
Hackathon demo: AWS AI for Bharat Hackathon

Run with:
    streamlit run demo_app.py
"""

import sys
import json
from pathlib import Path

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

# ── Path setup ──────────────────────────────────────────────────────
sys.path.insert(0, str(Path(__file__).parent))
from inference import SpoilagePredictor
from dataset import CROP_PROFILES, CROP_NAMES

# ── Page config ─────────────────────────────────────────────────────
st.set_page_config(
    page_title="SwadeshAI — Spoilage Predictor",
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

    .risk-card {
        padding: 1.2rem 1.5rem;
        border-radius: 10px;
        text-align: center;
        font-weight: bold;
        font-size: 1.1rem;
        margin-bottom: 1rem;
    }
    .risk-low      { background: #d4edda; border-left: 5px solid #28a745; color: #155724; }
    .risk-medium   { background: #fff3cd; border-left: 5px solid #ffc107; color: #856404; }
    .risk-high     { background: #ffe0b2; border-left: 5px solid #ff9800; color: #7b3f00; }
    .risk-critical { background: #f8d7da; border-left: 5px solid #dc3545; color: #721c24; }

    .metric-box {
        background: #f8f9fa;
        border-radius: 8px;
        padding: 1rem;
        text-align: center;
        border: 1px solid #e9ecef;
    }
    .metric-box .label { font-size: 0.8rem; color: #6c757d; text-transform: uppercase; }
    .metric-box .value { font-size: 1.8rem; font-weight: bold; color: #212529; }

    .rec-card {
        background: white;
        border-radius: 8px;
        padding: 0.75rem 1rem;
        margin-bottom: 0.5rem;
        border-left: 4px solid #2d9e5f;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    .rec-card.critical { border-left-color: #dc3545; }
    .rec-card.high     { border-left-color: #ff9800; }
    .rec-card.moderate { border-left-color: #ffc107; }
    .rec-card.none     { border-left-color: #28a745; }

    .explanation-box {
        background: #f0f7ff;
        border: 1px solid #bee3f8;
        border-radius: 8px;
        padding: 1rem 1.25rem;
        margin-top: 0.5rem;
    }

    .aws-badge {
        display: inline-block;
        background: #ff9900;
        color: white;
        padding: 0.2rem 0.6rem;
        border-radius: 4px;
        font-size: 0.75rem;
        font-weight: bold;
        margin-top: 0.5rem;
    }

    .hindi-text { font-size: 1.05rem; color: #444; }
    .whatif-arrow { font-size: 1.5rem; text-align: center; padding-top: 1.5rem; }
</style>
""", unsafe_allow_html=True)

# ── Load predictor (cached) ──────────────────────────────────────────
@st.cache_resource
def load_predictor():
    return SpoilagePredictor(model_dir="models")

predictor = load_predictor()

# ── Crop options ─────────────────────────────────────────────────────
CROPS = sorted(CROP_PROFILES.keys())
CROP_DISPLAY = {
    c: f"{c.title()} — {CROP_PROFILES[c]['hindi']}"
    for c in CROPS
}
RISK_COLORS = {
    "low":      "#28a745",
    "medium":   "#ffc107",
    "high":     "#ff9800",
    "critical": "#dc3545",
}
RISK_BG = {
    "low":      "#d4edda",
    "medium":   "#fff3cd",
    "high":     "#ffe0b2",
    "critical": "#f8d7da",
}

# ─────────────────────────────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="main-header">
    <h1>🌾 SwadeshAI — Spoilage Predictor</h1>
    <p>AI-powered produce spoilage risk prediction for Indian farmers &nbsp;|&nbsp;
       Powered by XGBoost + Amazon Bedrock (Claude)</p>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🌿 Crop Conditions")
    st.markdown("Enter your current storage conditions:")

    crop = st.selectbox(
        "Crop",
        options=CROPS,
        format_func=lambda c: CROP_DISPLAY[c],
        index=CROPS.index("tomato"),
    )

    profile = CROP_PROFILES[crop]
    opt_temp = profile["optimal_temp"]
    opt_hum  = profile["optimal_humidity"]

    st.markdown(f"""
    <small style="color:#666">
    Optimal: <b>{opt_temp[0]}–{opt_temp[1]}°C</b> &nbsp;|&nbsp;
    <b>{opt_hum[0]}–{opt_hum[1]}%</b> humidity
    </small>
    """, unsafe_allow_html=True)

    temperature = st.slider(
        "Temperature (°C)",
        min_value=-5, max_value=50, value=30, step=1,
        help=f"Optimal: {opt_temp[0]}–{opt_temp[1]}°C",
    )
    humidity = st.slider(
        "Humidity (%)",
        min_value=20, max_value=100, value=65, step=1,
        help=f"Optimal: {opt_hum[0]}–{opt_hum[1]}%",
    )
    days_since_harvest = st.slider(
        "Days Since Harvest",
        min_value=0, max_value=30, value=3,
    )
    storage_type = st.radio(
        "Storage Type",
        options=["ambient", "cold"],
        format_func=lambda x: "🌡️ Ambient (No cooling)" if x == "ambient" else "❄️ Cold Storage",
        horizontal=True,
    )
    transport_hours = st.slider(
        "Transport Time (hours)",
        min_value=0, max_value=24, value=2,
    )
    initial_quality = st.slider(
        "Initial Quality Score",
        min_value=50, max_value=100, value=85,
        help="Quality of produce at harvest (50=poor, 100=excellent)",
    )

    st.markdown("---")
    run_bedrock = st.toggle(
        "🤖 Bedrock Explanations",
        value=False,
        help="Use Amazon Bedrock (Claude) for richer causal explanations. "
             "Requires AWS credentials. Falls back to templates if unavailable.",
    )
    if run_bedrock:
        st.markdown('<span class="aws-badge">☁️ Amazon Bedrock</span>', unsafe_allow_html=True)

    predict_btn = st.button("🔍 Predict Spoilage Risk", type="primary", use_container_width=True)

# ─────────────────────────────────────────────────────────────────────
# TABS
# ─────────────────────────────────────────────────────────────────────
tab_predict, tab_whatif, tab_batch, tab_about = st.tabs([
    "📊 Live Prediction",
    "🔄 What-If Analysis",
    "📋 Batch Demo Results",
    "ℹ️ About",
])

# ─────────────────────────────────────────────────────────────────────
# TAB 1 — LIVE PREDICTION
# ─────────────────────────────────────────────────────────────────────
with tab_predict:
    # Auto-predict on sidebar change
    if "last_result" not in st.session_state or predict_btn:
        with st.spinner("Running spoilage prediction..."):
            # Swap use_bedrock if needed
            if run_bedrock and not predictor.use_bedrock:
                predictor.use_bedrock = True
                try:
                    from bedrock_explainer import BedrockExplainer
                    predictor._explainer = BedrockExplainer()
                except Exception:
                    predictor.use_bedrock = False
            elif not run_bedrock:
                predictor.use_bedrock = False

            result = predictor.predict(
                crop=crop,
                temperature=temperature,
                humidity=humidity,
                days_since_harvest=days_since_harvest,
                storage_type=storage_type,
                transport_hours=transport_hours,
                initial_quality=initial_quality,
            )
            st.session_state["last_result"] = result
    else:
        result = st.session_state["last_result"]

    risk      = result["risk_level"]
    prob      = result["spoilage_probability"]
    remaining = result["remaining_shelf_life_days"]
    icon      = result["risk_icon"]

    # ── Risk banner ────────────────────────────────────────────────
    st.markdown(f"""
    <div class="risk-card risk-{risk}">
        {icon} &nbsp; {result['crop_hindi']} ({crop.title()}) &nbsp;—&nbsp;
        {risk.upper()} RISK &nbsp;|&nbsp;
        Spoilage Probability: {prob:.0%} &nbsp;|&nbsp;
        Shelf Life Remaining: {remaining:.0f} days
    </div>
    """, unsafe_allow_html=True)

    # ── Metric columns ─────────────────────────────────────────────
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Risk Level", risk.upper(), delta=None)
    with col2:
        st.metric("Spoilage Probability", f"{prob:.0%}")
    with col3:
        st.metric("Remaining Shelf Life", f"{remaining:.0f} days")
    with col4:
        st.metric("Storage", storage_type.title())

    st.markdown("---")
    col_chart, col_recs = st.columns([1, 1])

    # ── Risk probability gauge ─────────────────────────────────────
    with col_chart:
        st.markdown("#### Risk Probability Breakdown")
        risk_probs = result["risk_probabilities"]
        fig = go.Figure(go.Bar(
            x=list(risk_probs.values()),
            y=[l.upper() for l in risk_probs.keys()],
            orientation="h",
            marker_color=[RISK_COLORS[l] for l in risk_probs.keys()],
            text=[f"{v:.1%}" for v in risk_probs.values()],
            textposition="outside",
            hovertemplate="%{y}: %{x:.1%}<extra></extra>",
        ))
        fig.update_layout(
            xaxis=dict(range=[0, 1], tickformat=".0%", showgrid=False),
            yaxis=dict(showgrid=False),
            margin=dict(l=10, r=10, t=10, b=10),
            height=200,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig, use_container_width=True)

        # ── Condition comparison ───────────────────────────────────
        st.markdown("#### Conditions vs Optimal")
        opt_temp_mid = sum(opt_temp) / 2
        opt_hum_mid  = sum(opt_hum) / 2

        temp_delta = temperature - opt_temp_mid
        hum_delta  = humidity    - opt_hum_mid

        fig2 = go.Figure()
        fig2.add_trace(go.Bar(
            name="Current",
            x=["Temperature (°C)", "Humidity (%)"],
            y=[temperature, humidity],
            marker_color=["#dc3545" if abs(temp_delta) > 5 else "#28a745",
                          "#dc3545" if abs(hum_delta)  > 5 else "#28a745"],
            text=[f"{temperature}°C", f"{humidity}%"],
            textposition="outside",
        ))
        fig2.add_trace(go.Bar(
            name="Optimal (mid)",
            x=["Temperature (°C)", "Humidity (%)"],
            y=[opt_temp_mid, opt_hum_mid],
            marker_color=["rgba(45,158,95,0.4)", "rgba(45,158,95,0.4)"],
            text=[f"{opt_temp_mid:.0f}°C", f"{opt_hum_mid:.0f}%"],
            textposition="outside",
        ))
        fig2.update_layout(
            barmode="group",
            margin=dict(l=10, r=10, t=10, b=10),
            height=220,
            legend=dict(orientation="h", y=-0.2),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            yaxis=dict(showgrid=False),
        )
        st.plotly_chart(fig2, use_container_width=True)

    # ── Recommendations ────────────────────────────────────────────
    with col_recs:
        st.markdown("#### 📋 Recommendations")
        for rec in result["recommendations"]:
            urgency = rec.get("urgency", "none")
            border_cls = urgency if urgency in ("critical", "high", "moderate") else "none"
            st.markdown(f"""
            <div class="rec-card {border_cls}">
                <div style="font-weight:600">{rec.get('icon','→')} {rec['en']}</div>
                <div class="hindi-text" style="margin-top:4px;font-size:0.9rem">
                    {rec['hi']}
                </div>
            </div>
            """, unsafe_allow_html=True)

    # ── Explanation ────────────────────────────────────────────────
    st.markdown("#### 🧠 Causal Explanation")
    exp = result["explanation"]
    source = result.get("explanation_source", "template-based")
    badge = (
        '<span class="aws-badge">☁️ Amazon Bedrock (Claude)</span>'
        if "Bedrock" in source else
        '<span style="background:#6c757d;color:white;padding:0.2rem 0.5rem;border-radius:4px;font-size:0.75rem">📄 Template-based</span>'
    )

    col_en, col_hi = st.columns(2)
    with col_en:
        st.markdown(f"""
        <div class="explanation-box">
            <strong>English 🇬🇧</strong><br><br>
            {exp['en']}
            <br><br>{badge}
        </div>
        """, unsafe_allow_html=True)
    with col_hi:
        st.markdown(f"""
        <div class="explanation-box">
            <strong>हिंदी 🇮🇳</strong><br><br>
            <span class="hindi-text">{exp['hi']}</span>
        </div>
        """, unsafe_allow_html=True)

    # Key causes (if Bedrock or enhanced template)
    if "key_causes" in exp and exp["key_causes"]:
        st.markdown("**Key Causes:**")
        for cause in exp["key_causes"]:
            st.markdown(f"  - {cause}")


# ─────────────────────────────────────────────────────────────────────
# TAB 2 — WHAT-IF ANALYSIS
# ─────────────────────────────────────────────────────────────────────
with tab_whatif:
    st.markdown("### 🔄 What-If Scenario Analysis")
    st.markdown(
        "Explore how changes to storage conditions affect spoilage risk. "
        "The model re-runs prediction with the proposed changes and compares the outcome."
    )

    base_result = st.session_state.get("last_result")
    if base_result is None:
        st.info("Run a prediction first from the sidebar, then come back here.")
    else:
        st.markdown(f"**Base scenario:** {base_result['crop_hindi']} ({base_result['crop'].title()}) — "
                    f"{base_result['risk_icon']} {base_result['risk_level'].upper()}, "
                    f"{base_result['spoilage_probability']:.0%} probability, "
                    f"{base_result['remaining_shelf_life_days']:.0f} days remaining")

        st.markdown("---")
        st.markdown("#### Propose Changes")
        wi_col1, wi_col2, wi_col3 = st.columns(3)

        base_inp = base_result["input_summary"]
        with wi_col1:
            new_temp = st.slider("New Temperature (°C)", -5, 50,
                                 value=int(base_inp["temperature_c"]), key="wi_temp")
            new_humidity = st.slider("New Humidity (%)", 20, 100,
                                     value=int(base_inp["humidity_pct"]), key="wi_hum")
        with wi_col2:
            new_storage = st.radio("New Storage Type", ["ambient", "cold"],
                                   index=0 if base_inp["storage_type"] == "ambient" else 1,
                                   format_func=lambda x: "🌡️ Ambient" if x == "ambient" else "❄️ Cold",
                                   key="wi_storage")
            new_transport = st.slider("New Transport (hours)", 0, 24,
                                      value=int(base_inp["transport_hours"]), key="wi_transport")
        with wi_col3:
            st.markdown("##### Quick Presets")
            if st.button("❄️ Move to Cold Storage"):
                p = CROP_PROFILES[base_result["crop"]]
                st.session_state["wi_temp"]     = int(sum(p["optimal_temp"]) / 2)
                st.session_state["wi_hum"]      = int(sum(p["optimal_humidity"]) / 2)
                st.session_state["wi_storage"]  = "cold"
                st.rerun()
            if st.button("🚚 Reduce Transport Time"):
                st.session_state["wi_transport"] = max(0, int(base_inp["transport_hours"]) - 4)
                st.rerun()
            if st.button("💧 Optimise Humidity"):
                p = CROP_PROFILES[base_result["crop"]]
                st.session_state["wi_hum"] = int(sum(p["optimal_humidity"]) / 2)
                st.rerun()

        if st.button("⚡ Run What-If Analysis", type="primary"):
            changes = {}
            if new_temp     != base_inp["temperature_c"]:  changes["temperature"]     = new_temp
            if new_humidity != base_inp["humidity_pct"]:   changes["humidity"]        = new_humidity
            if new_storage  != base_inp["storage_type"]:   changes["storage_type"]    = new_storage
            if new_transport!= base_inp["transport_hours"]:changes["transport_hours"] = new_transport

            if not changes:
                st.warning("No changes detected. Adjust at least one parameter above.")
            else:
                with st.spinner("Running what-if analysis..."):
                    whatif = predictor.whatif(base_result, changes)
                    st.session_state["whatif_result"] = whatif

        if "whatif_result" in st.session_state:
            wi = st.session_state["whatif_result"]
            st.markdown("---")
            st.markdown("#### Results")

            improved = wi.get("improvement", False)
            impact_color = "#28a745" if improved else "#dc3545"
            impact_label = "IMPROVEMENT ✅" if improved else "WORSENING ⚠️"

            st.markdown(f"""
            <div style="background:{RISK_BG[wi['before']['risk_level']]};
                        border-radius:8px;padding:0.75rem 1rem;margin-bottom:0.5rem">
                <strong>Before:</strong> {wi['before']['risk_level'].upper()} —
                {wi['before']['spoilage_probability']:.0%} probability,
                {wi['before']['remaining_days']:.0f} days
            </div>
            <div style="text-align:center;font-size:1.5rem;padding:0.25rem 0">↓</div>
            <div style="background:{RISK_BG[wi['after']['risk_level']]};
                        border-radius:8px;padding:0.75rem 1rem;margin-bottom:0.5rem">
                <strong>After:</strong> {wi['after']['risk_level'].upper()} —
                {wi['after']['spoilage_probability']:.0%} probability,
                {wi['after']['remaining_days']:.0f} days
            </div>
            <div style="background:{impact_color};color:white;border-radius:8px;
                        padding:0.5rem 1rem;text-align:center;font-weight:bold">
                {impact_label} — {wi['impact_summary']}
            </div>
            """, unsafe_allow_html=True)

            # Comparison chart
            fig_wi = go.Figure()
            cats = ["Spoilage Probability", "Remaining Shelf Life (days)"]
            before_vals = [wi["before"]["spoilage_probability"],
                           min(wi["before"]["remaining_days"], 60)]
            after_vals  = [wi["after"]["spoilage_probability"],
                           min(wi["after"]["remaining_days"], 60)]
            fig_wi.add_trace(go.Bar(name="Before", x=cats, y=before_vals,
                marker_color="#dc3545",
                text=[f"{before_vals[0]:.0%}", f"{before_vals[1]:.0f}d"],
                textposition="outside"))
            fig_wi.add_trace(go.Bar(name="After", x=cats, y=after_vals,
                marker_color="#28a745",
                text=[f"{after_vals[0]:.0%}", f"{after_vals[1]:.0f}d"],
                textposition="outside"))
            fig_wi.update_layout(
                barmode="group", height=280,
                margin=dict(l=10, r=10, t=20, b=10),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                yaxis=dict(showgrid=False),
            )
            st.plotly_chart(fig_wi, use_container_width=True)

            col_wi_en, col_wi_hi = st.columns(2)
            with col_wi_en:
                st.markdown(f"""
                <div class="explanation-box"><strong>🇬🇧 English</strong><br><br>{wi['en']}</div>
                """, unsafe_allow_html=True)
            with col_wi_hi:
                st.markdown(f"""
                <div class="explanation-box">
                    <strong>🇮🇳 हिंदी</strong><br><br>
                    <span class="hindi-text">{wi['hi']}</span>
                </div>
                """, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────
# TAB 3 — BATCH DEMO RESULTS
# ─────────────────────────────────────────────────────────────────────
with tab_batch:
    st.markdown("### 📋 Pre-computed Batch Demo Results")
    st.markdown("10 diverse test scenarios across all risk levels and crops.")

    demo_file = Path(__file__).parent / "data" / "demo_results.json"
    if demo_file.exists():
        with open(demo_file) as f:
            batch = json.load(f)

        # Summary table
        rows = []
        for r in batch:
            inp = r["input_summary"]
            rows.append({
                "Crop": r["crop"].title(),
                "Hindi": r["crop_hindi"],
                "Risk": r["risk_level"].upper(),
                "Prob (%)": f"{r['spoilage_probability']:.0%}",
                "Life (days)": int(r["remaining_shelf_life_days"]),
                "Temp (°C)": inp["temperature_c"],
                "Humidity (%)": inp["humidity_pct"],
                "Storage": inp["storage_type"],
                "Transport (h)": inp["transport_hours"],
            })

        df = pd.DataFrame(rows)

        def risk_colour(val):
            colours = {
                "LOW":      "background-color: #d4edda; color: #155724",
                "MEDIUM":   "background-color: #fff3cd; color: #856404",
                "HIGH":     "background-color: #ffe0b2; color: #7b3f00",
                "CRITICAL": "background-color: #f8d7da; color: #721c24",
            }
            return colours.get(val, "")

        styled = (
            df.style
            .applymap(risk_colour, subset=["Risk"])
            .set_properties(**{"text-align": "center"})
        )
        st.dataframe(styled, use_container_width=True, hide_index=True)

        st.markdown("---")

        col_pie, col_bar = st.columns(2)

        # Risk distribution pie
        with col_pie:
            risk_counts = df["Risk"].value_counts()
            fig_pie = go.Figure(go.Pie(
                labels=risk_counts.index,
                values=risk_counts.values,
                marker_colors=[RISK_COLORS[r.lower()] for r in risk_counts.index],
                hole=0.45,
                textinfo="label+percent",
            ))
            fig_pie.update_layout(
                title="Risk Distribution",
                margin=dict(l=10, r=10, t=40, b=10),
                height=280,
                paper_bgcolor="rgba(0,0,0,0)",
            )
            st.plotly_chart(fig_pie, use_container_width=True)

        # Spoilage probability by crop
        with col_bar:
            crops_sorted = sorted(batch, key=lambda r: r["spoilage_probability"], reverse=True)
            fig_bar = go.Figure(go.Bar(
                x=[r["crop"].title() for r in crops_sorted],
                y=[r["spoilage_probability"] for r in crops_sorted],
                marker_color=[RISK_COLORS[r["risk_level"]] for r in crops_sorted],
                text=[f"{r['spoilage_probability']:.0%}" for r in crops_sorted],
                textposition="outside",
                hovertemplate="%{x}: %{y:.0%}<extra></extra>",
            ))
            fig_bar.update_layout(
                title="Spoilage Probability by Crop",
                yaxis=dict(tickformat=".0%", range=[0, 1.15], showgrid=False),
                xaxis=dict(tickangle=-30),
                margin=dict(l=10, r=10, t=40, b=60),
                height=280,
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
            )
            st.plotly_chart(fig_bar, use_container_width=True)

        # Shelf life scatter
        st.markdown("#### Remaining Shelf Life vs Spoilage Probability")
        scatter_data = pd.DataFrame([{
            "Crop": r["crop"].title(),
            "Shelf Life (days)": r["remaining_shelf_life_days"],
            "Spoilage Prob":     r["spoilage_probability"],
            "Risk":              r["risk_level"].upper(),
            "Storage":           r["input_summary"]["storage_type"],
            "Temp (°C)":         r["input_summary"]["temperature_c"],
        } for r in batch])

        fig_scatter = px.scatter(
            scatter_data,
            x="Shelf Life (days)",
            y="Spoilage Prob",
            color="Risk",
            size="Temp (°C)",
            text="Crop",
            color_discrete_map={
                "LOW": "#28a745", "MEDIUM": "#ffc107",
                "HIGH": "#ff9800", "CRITICAL": "#dc3545",
            },
            hover_data=["Storage", "Temp (°C)"],
        )
        fig_scatter.update_traces(textposition="top center")
        fig_scatter.update_layout(
            yaxis=dict(tickformat=".0%", title="Spoilage Probability", showgrid=False),
            xaxis=dict(showgrid=False),
            height=380,
            margin=dict(l=10, r=10, t=20, b=10),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig_scatter, use_container_width=True)

    else:
        st.info("No demo results found. Run the following command to generate them:")
        st.code("python inference.py  # runs built-in demo and saves data/demo_results.json")


# ─────────────────────────────────────────────────────────────────────
# TAB 4 — ABOUT
# ─────────────────────────────────────────────────────────────────────
with tab_about:
    st.markdown("### ℹ️ About SwadeshAI Spoilage Predictor")

    col_a, col_b = st.columns(2)

    with col_a:
        st.markdown("""
**Model Architecture**
- 3 XGBoost sub-models (multi-output)
  - Shelf life regressor (days remaining)
  - Spoilage probability regressor (0–1)
  - Risk level classifier (Low / Medium / High / Critical)
- Trained on 50,000 synthetic samples
- 13 input features per prediction
- Performance: 87.5% risk accuracy, R² = 0.842

**Supported Crops (16)**
| Vegetables | Fruits | Grains |
|------------|--------|--------|
| Tomato (टमाटर) | Banana (केला) | Rice (चावल) |
| Potato (आलू) | Mango (आम) | Wheat (गेहूं) |
| Onion (प्याज) | Apple (सेब) | |
| Spinach (पालक) | Grape (अंगूर) | |
| Okra (भिंडी) | Guava (अमरूद) | |
| Cauliflower (फूलगोभी) | | |
| Brinjal (बैंगन) | | |
| Carrot (गाजर) | | |
| Capsicum (शिमला मिर्च) | | |
        """)

    with col_b:
        st.markdown("""
**AWS Services**

| Service | Role |
|---------|------|
| ☁️ Amazon Bedrock (Claude 3 Sonnet) | Causal Explanation Engine — generates farmer-friendly explanations in Hindi + English |
| 🚀 Amazon SageMaker | Model deployment — serverless or real-time endpoint |

**Science Behind Predictions**
- **Q10 Temperature Rule**: Spoilage rate doubles every 10°C above optimal
- **Humidity Impact**: Below-optimal → moisture loss/wilting; above → mold growth
- **Transport Damage**: Mechanical stress weighted by crop sensitivity
- **Respiration Rate**: Climacteric fruits (banana, mango) spoil faster
- **Sigmoid Decay**: Probability follows sigmoid curve centered at 60% of shelf life

**What-If Analysis**
The Causal Explanation Engine supports scenario comparison:
- "What if I move to cold storage?"
- "What if I reduce transport time?"
- Before vs after comparison with impact summary in Hindi + English
        """)

    st.markdown("---")
    st.markdown("""
    <div style="text-align:center; color:#888; font-size:0.85rem; padding:1rem">
        SwadeshAI &nbsp;|&nbsp; AWS AI for Bharat Hackathon &nbsp;|&nbsp;
        Built with XGBoost · Amazon Bedrock · Amazon SageMaker · Streamlit
    </div>
    """, unsafe_allow_html=True)

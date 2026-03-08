"""
Enhanced SwadeshAI Freshness Detection Demo

Features:
- Multi-level freshness grading (5 levels)
- Integrated spoilage prediction
- Damage assessment  
- Ripeness staging
- Unified recommendations
- Visual quality metrics

Run:
    cd SwadeshAI
    streamlit run ml/demo_enhanced_freshness.py --server.port 8512
"""

import sys
from pathlib import Path
from datetime import date, timedelta
import tempfile

import streamlit as st
import plotly.graph_objects as go
from PIL import Image
import numpy as np

# Add paths
sys.path.insert(0, str(Path(__file__).parent))

from integrated_quality_pipeline import IntegratedQualityPipeline


# ── Page config ─────────────────────────────────────────────────────
st.set_page_config(
    page_title="SwadeshAI Enhanced Freshness Detection",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ──────────────────────────────────────────────────────
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #1e7e34 0%, #28a745 50%, #48bb78 100%);
        padding: 2rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        color: white;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .main-header h1 { margin: 0; font-size: 2.5rem; font-weight: 700; }
    .main-header p  { margin: 0.5rem 0 0; opacity: 0.95; font-size: 1.1rem; }
    
    .metric-card {
        background: white;
        border-radius: 12px;
        padding: 1.5rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        border-left: 5px solid #28a745;
        margin-bottom: 1rem;
    }
    
    .grade-excellent { border-left-color: #28a745 !important; background: #d4edda; }
    .grade-good { border-left-color: #007bff !important; background: #cce5ff; }
    .grade-fair { border-left-color: #ffc107 !important; background: #fff3cd; }
    .grade-poor { border-left-color: #fd7e14 !important; background: #ffe5d0; }
    .grade-rotten { border-left-color: #dc3545 !important; background: #f8d7da; }
    
    .score-circle {
        width: 120px;
        height: 120px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 2rem;
        font-weight: bold;
        margin: 0 auto;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
    
    .urgency-low { color: #28a745; }
    .urgency-moderate { color: #ffc107; }
    .urgency-high { color: #fd7e14; }
    .urgency-critical { color: #dc3545; }
    
    .action-item {
        background: #f8f9fa;
        border-left: 3px solid #007bff;
        padding: 0.75rem 1rem;
        margin: 0.5rem 0;
        border-radius: 6px;
    }
    
    .storage-tip {
        background: #e7f5ff;
        border-left: 3px solid #1e7e34;
        padding: 0.75rem 1rem;
        margin: 0.5rem 0;
        border-radius: 6px;
    }
    
    .damage-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 12px;
        font-size: 0.85rem;
        font-weight: 600;
        margin: 0.25rem;
    }
    
    .badge-minimal { background: #d4edda; color: #155724; }
    .badge-minor { background: #fff3cd; color: #856404; }
    .badge-moderate { background: #ffe5d0; color: #8b4513; }
    .badge-severe { background: #f8d7da; color: #721c24; }
</style>
""", unsafe_allow_html=True)

# ── Header ──────────────────────────────────────────────────────────
st.markdown("""
<div class="main-header">
    <h1>🌾 SwadeshAI — Enhanced Freshness Detection</h1>
    <p>🔬 Multi-Level Quality Grading • 📊 Integrated Spoilage Prediction • 💡 Actionable Insights</p>
</div>
""", unsafe_allow_html=True)

# ── Initialize Pipeline ─────────────────────────────────────────────
@st.cache_resource
def load_pipeline():
    """Load the integrated pipeline once."""
    with st.spinner("🔧 Loading AI models..."):
        pipeline = IntegratedQualityPipeline(
            freshness_model_dir="ml/freshness_detection/models",
            spoilage_model_dir="ml/spoilage_prediction/models",
            enable_ml_spoilage=False  # Use heuristics for demo
        )
    return pipeline

try:
    pipeline = load_pipeline()
    st.success("✅ AI models loaded successfully", icon="✓")
except Exception as e:
    st.error(f"⚠️ Error loading models: {e}")
    st.info("Running in demo mode with simulated predictions")
    pipeline = None

# ── Sidebar: Input Configuration ────────────────────────────────────
st.sidebar.header("⚙️ Configuration")

# Image upload
uploaded_file = st.sidebar.file_uploader(
    "📸 Upload Produce Image",
    type=["jpg", "jpeg", "png"],
    help="Upload a clear photo of your produce"
)

# Crop selection
crop = st.sidebar.selectbox(
    "🌱 Crop Type",
    ["tomato", "banana", "mango", "apple", "potato", "onion", "carrot", "okra", "orange", "cucumber"],
    help="Select the type of produce (will auto-detect from image)"
)

# Storage conditions
st.sidebar.markdown("### 🏪 Storage Conditions")

storage_type = st.sidebar.radio(
    "Storage Type",
    ["ambient", "cold"],
    help="Current storage environment"
)

storage_temp = st.sidebar.slider(
    "Temperature (°C)",
    min_value=0,
    max_value=40,
    value=28 if storage_type == "ambient" else 8,
    help="Current storage temperature"
)

storage_humidity = st.sidebar.slider(
    "Humidity (%)",
    min_value=20,
    max_value=100,
    value=65 if storage_type == "ambient" else 85,
    help="Current storage humidity"
)

# Harvest info
st.sidebar.markdown("### 📅 Harvest Information")

harvest_days_ago = st.sidebar.number_input(
    "Days Since Harvest",
    min_value=0,
    max_value=30,
    value=2,
    help="How many days ago was this harvested?"
)

transport_hours = st.sidebar.number_input(
    "Transport Hours",
    min_value=0.0,
    max_value=48.0,
    value=0.0,
    step=0.5,
    help="Hours spent in transport"
)

# ── Main Content ────────────────────────────────────────────────────
if uploaded_file is not None:
    # Display uploaded image
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        image = Image.open(uploaded_file)
        st.image(image, caption="Uploaded Produce Image", use_container_width=True)
    
    # Save image temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_file:
        image.save(tmp_file.name)
        temp_path = tmp_file.name
    
    # Run analysis button
    if st.button("🔬 Analyze Quality", type="primary", use_container_width=True):
        with st.spinner("🧪 Analyzing produce quality..."):
            try:
                # Prepare inputs
                harvest_date = date.today() - timedelta(days=harvest_days_ago)
                
                # Run integrated analysis
                result = pipeline.analyze(
                    image_path=temp_path,
                    crop_name=crop,
                    harvest_date=harvest_date,
                    storage_temp=storage_temp,
                    storage_humidity=storage_humidity,
                    storage_type=storage_type,
                    transport_hours=transport_hours,
                )
                
                # Store in session state
                st.session_state['analysis_result'] = result
                st.session_state['analyzed'] = True
                
            except Exception as e:
                st.error(f"❌ Analysis failed: {e}")
                st.exception(e)

# ── Display Results ─────────────────────────────────────────────────
if st.session_state.get('analyzed', False) and 'analysis_result' in st.session_state:
    result = st.session_state['analysis_result']
    
    # Extract key metrics
    current_quality = result['current_quality']
    spoilage_pred = result['spoilage_prediction']
    action_plan = result['action_plan']
    storage_cond = result['storage_conditions']
    
    st.markdown("---")
    st.markdown("## 📊 Analysis Results")
    
    # === Row 1: Overall Summary ===
    st.markdown("### 🎯 Quality Summary")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        grade = current_quality['freshness_grade']
        score = current_quality['quality_score']
        st.markdown(f'<div class="metric-card grade-{grade}">', unsafe_allow_html=True)
        st.markdown(f"### {grade.upper()}")
        st.markdown(f"**Quality Score:** {score}/100")
        st.markdown(f"**Grade:** {current_quality['overall_grade']}")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        risk = spoilage_pred['risk_level']
        remaining = spoilage_pred['remaining_days']
        st.markdown(f'<div class="metric-card">', unsafe_allow_html=True)
        st.markdown(f"### {risk.upper()} RISK")
        st.markdown(f"**Shelf Life:** {remaining} days")
        st.markdown(f"**Probability:** {int(spoilage_pred['probability']*100)}%")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col3:
        damage = current_quality['damage_level']
        damage_score = current_quality['damage_score']
        st.markdown(f'<div class="metric-card">', unsafe_allow_html=True)
        st.markdown(f"### {damage.upper()}")
        st.markdown(f"**Damage Score:** {damage_score}/100")
        st.markdown(f"**Ripeness:** {current_quality.get('ripeness_stage', 'N/A')}")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col4:
        urgency = action_plan['urgency']
        sell_days = action_plan['sell_within_days']
        st.markdown(f'<div class="metric-card">', unsafe_allow_html=True)
        st.markdown(f"### {urgency.upper()}")
        st.markdown(f"**Sell Within:** {sell_days} day(s)")
        st.markdown(f"**Strategy:** {action_plan['price_strategy'].replace('_', ' ').title()}")
        st.markdown('</div>', unsafe_allow_html=True)
    
    # === Row 2: Visual Quality Gauge ===
    st.markdown("---")
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📈 Quality Metrics")
        
        # Create gauge chart
        fig = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=score,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': "Quality Score", 'font': {'size': 24}},
            delta={'reference': 70, 'increasing': {'color': "green"}},
            gauge={
                'axis': {'range': [None, 100], 'tickwidth': 1, 'tickcolor': "darkblue"},
                'bar': {'color': "darkgreen" if score >= 70 else "orange" if score >= 50 else "red"},
                'bgcolor': "white",
                'borderwidth': 2,
                'bordercolor': "gray",
                'steps': [
                    {'range': [0, 50], 'color': '#f8d7da'},
                    {'range': [50, 70], 'color': '#fff3cd'},
                    {'range': [70, 85], 'color': '#cce5ff'},
                    {'range': [85, 100], 'color': '#d4edda'}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 50
                }
            }
        ))
        fig.update_layout(height=300, margin=dict(l=20, r=20, t=50, b=20))
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("### 📊 Freshness Breakdown")
        
        # Create breakdown chart
        metrics = {
            'Freshness': current_quality['quality_score'],
            'Damage (Inv)': 100 - current_quality['damage_score'],
            'Confidence': int(current_quality['confidence'] * 100),
        }
        
        fig = go.Figure(data=[
            go.Bar(
                x=list(metrics.keys()),
                y=list(metrics.values()),
                marker_color=['#28a745', '#17a2b8', '#ffc107'],
                text=list(metrics.values()),
                textposition='auto',
            )
        ])
        fig.update_layout(
            yaxis_range=[0, 100],
            height=300,
            margin=dict(l=20, r=20, t=30, b=20),
            showlegend=False
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # === Row 3: Action Plan ===
    st.markdown("---")
    st.markdown("### 💡 Recommended Actions")
    
    col1, col2 = st.columns([3, 2])
    
    with col1:
        st.markdown("#### 🎯 Primary Actions")
        for action in action_plan['all_actions']:
            st.markdown(f'<div class="action-item">{action}</div>', unsafe_allow_html=True)
        
        if action_plan.get('storage_tips'):
            st.markdown("#### 🏪 Storage Tips")
            for tip in action_plan['storage_tips']:
                st.markdown(f'<div class="storage-tip">{tip}</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown("#### 📝 Summary")
        st.info(f"**English:** {action_plan['english_summary']}")
        st.success(f"**Hindi:** {action_plan['hindi_summary']}")
        
        st.markdown("#### ⏰ Timeline")
        urgency_class = f"urgency-{urgency}"
        st.markdown(f'<p class="{urgency_class}"><strong>Urgency:</strong> {urgency.upper()}</p>', unsafe_allow_html=True)
        st.markdown(f"**Sell Within:** {sell_days} day(s)")
        st.markdown(f"**Confidence:** {action_plan['confidence_level'].title()}")
    
    # === Row 4: Detailed Info (Expandable) ===
    st.markdown("---")
    with st.expander("🔍 Detailed Analysis", expanded=False):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("**Current State**")
            st.json({
                "crop": current_quality['crop'],
                "grade": current_quality['freshness_grade'],
                "score": current_quality['quality_score'],
                "damage_level": current_quality['damage_level'],
                "ripeness": current_quality.get('ripeness_stage', 'N/A'),
            })
        
        with col2:
            st.markdown("**Spoilage Forecast**")
            st.json({
                "risk": spoilage_pred['risk_level'],
                "probability": f"{spoilage_pred['probability']:.1%}",
                "remaining_days": spoilage_pred['remaining_days'],
                "total_shelf_life": spoilage_pred['estimated_total_shelf_life'],
            })
        
        with col3:
            st.markdown("**Storage Conditions**")
            st.json({
                "type": storage_cond['type'],
                "temperature": f"{storage_cond['temperature_c']}°C",
                "humidity": f"{storage_cond['humidity_pct']}%",
                "days_old": storage_cond['days_since_harvest'],
            })

else:
    # Placeholder when no image uploaded
    st.info("👆 Upload a produce image from the sidebar to begin analysis")
    
    st.markdown("---")
    st.markdown("## 🌟 Features")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        ### 🔬 Multi-Level Grading
        - **5-level freshness** (Excellent → Rotten)
        - Detailed quality scoring
        - Damage assessment
        - Ripeness staging
        """)
    
    with col2:
        st.markdown("""
        ### 📊 Spoilage Prediction
        - Shelf life estimation
        - Risk level classification
        - Storage condition analysis
        - Timeline forecasting
        """)
    
    with col3:
        st.markdown("""
        ### 💡 Smart Recommendations
        - Actionable selling advice
        - Storage optimization tips
        - Price strategy guidance
        - Bilingual support (EN/HI)
        """)
    
    st.markdown("---")
    st.markdown("### 📋 How It Works")
    st.markdown("""
    1. **Upload Image** 📸 - Take a clear photo of your produce
    2. **Configure Settings** ⚙️ - Enter storage conditions and harvest date
    3. **Analyze** 🔬 - AI analyzes current quality and predicts shelf life
    4. **Get Insights** 💡 - Receive actionable recommendations for selling/storage
    """)
    
    # Demo with sample images
    st.markdown("---")
    st.markdown("### 🎯 Try with Sample Images")
    
    sample_dir = Path("ml/freshness_detection/samples/real_test")
    if sample_dir.exists():
        samples = list(sample_dir.glob("*.jpg"))[:6]
        if samples:
            cols = st.columns(3)
            for idx, sample in enumerate(samples):
                with cols[idx % 3]:
                    st.image(str(sample), caption=sample.stem, use_container_width=True)

# ── Footer ──────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #6c757d; padding: 1rem;">
    <p><strong>SwadeshAI Enhanced Freshness Detection</strong></p>
    <p>Powered by Computer Vision + ML • Built for Indian Farmers 🇮🇳</p>
</div>
""", unsafe_allow_html=True)

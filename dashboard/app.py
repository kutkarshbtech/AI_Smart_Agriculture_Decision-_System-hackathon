"""
SwadeshAI — Interactive Demo Dashboard
Connect to the deployed AWS backend and explore:
  • Freshness Detection + Pricing Pipeline
  • Live Mandi Prices
  • AI Chatbot (Amazon Bedrock Nova Lite)

Usage:
    pip install streamlit requests plotly
    streamlit run dashboard/app.py
"""
import streamlit as st
import requests
import json
import time
from datetime import datetime

# ── Config ───────────────────────────────────────────────
DEFAULT_API = "http://swadesh-ai-alb-dev-426896629.ap-south-1.elb.amazonaws.com"

CROPS = [
    "tomato", "onion", "potato", "mango", "apple", "banana",
    "rice", "wheat", "carrot", "capsicum", "brinjal", "cabbage",
    "cauliflower", "cucumber", "grapes", "guava", "lemon",
    "okra", "peas", "spinach",
]

QUALITY_GRADES = ["excellent", "good", "average", "poor"]
SPOILAGE_RISKS = ["low", "medium", "high", "critical"]
STORAGE_TYPES = ["ambient", "cold", "controlled"]

STATES = [
    "Andhra Pradesh", "Bihar", "Delhi", "Gujarat", "Haryana",
    "Karnataka", "Kerala", "Madhya Pradesh", "Maharashtra",
    "Punjab", "Rajasthan", "Tamil Nadu", "Telangana",
    "Uttar Pradesh", "West Bengal",
]


# ── Page Config ──────────────────────────────────────────
st.set_page_config(
    page_title="SwadeshAI — Post-Harvest Intelligence",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ── Session state defaults ────────────────────────────────
if "auth_token" not in st.session_state:
    st.session_state.auth_token = None
if "auth_user" not in st.session_state:
    st.session_state.auth_user = None
if "auth_page" not in st.session_state:
    st.session_state.auth_page = "login"      # "login" | "register" | "otp"
if "otp_context" not in st.session_state:
    st.session_state.otp_context = {}          # temp store for mobile/user_type/demo_otp


# ── Sidebar (always shown) ───────────────────────────────
with st.sidebar:
    st.image("https://img.icons8.com/color/96/wheat.png", width=64)
    st.title("🌾 SwadeshAI")
    st.caption("AI-Powered Post-Harvest Decision Intelligence")
    st.divider()

    api_url = st.text_input("API Endpoint", value=DEFAULT_API)
    api_url = api_url.rstrip("/")
    API = f"{api_url}/api/v1"
    AUTH_API = f"{api_url}/api/auth"

    # Health check (cached for 30s to avoid blocking every interaction)
    @st.cache_data(ttl=30, show_spinner=False)
    def _check_health(url: str) -> tuple:
        """Returns (ok: bool, detail: str)."""
        for attempt in range(3):
            try:
                r = requests.get(f"{url}/health", timeout=10)
                if r.status_code == 200:
                    return True, "connected"
                return False, f"HTTP {r.status_code}"
            except Exception:
                if attempt < 2:
                    time.sleep(1)
        return False, "unreachable"

    ok, detail = _check_health(api_url)
    if ok:
        st.success("✅ Backend connected")
    else:
        st.warning(f"⚠️ Backend {detail} — click below to retry")
        if st.button("🔄 Retry"):
            _check_health.clear()
            st.rerun()

    # ── Logged-in user info & navigation ──────────────────
    if st.session_state.auth_token:
        st.divider()
        user = st.session_state.auth_user or {}
        st.markdown(f"👤 **{user.get('name', 'User')}**")
        st.caption(f"{user.get('user_type', '').title()} · {user.get('mobile_number', '')}")
        if st.button("🚪 Logout", key="sidebar_logout"):
            try:
                requests.post(
                    f"{AUTH_API}/logout",
                    headers={"Authorization": f"Bearer {st.session_state.auth_token}"},
                    timeout=5,
                )
            except Exception:
                pass
            st.session_state.auth_token = None
            st.session_state.auth_user = None
            st.session_state.auth_page = "login"
            st.rerun()

        st.divider()
        page = st.radio(
            "Navigate",
            [
                "🔬 Freshness + Pricing",
                "📸 Image Assessment",
                "💰 Price Recommendation",
                "📊 Mandi Prices",
                "📈 Trends & Forecast",
                "🔬 Causal AI",
                "🌤️ Weather",
                "🚚 Logistics",
                "🤖 AI Chatbot",
            ],
            index=0,
        )
    else:
        page = None  # not logged in — no navigation


# ═════════════════════════════════════════════════════════
#  Helper functions
# ═════════════════════════════════════════════════════════

def _request_with_retry(method: str, url: str, retries: int = 2, **kwargs):
    """HTTP request with automatic retry on timeout / connection errors."""
    kwargs.setdefault("timeout", 90)
    last_err = None
    for attempt in range(1, retries + 1):
        try:
            r = requests.request(method, url, **kwargs)
            r.raise_for_status()
            return r
        except requests.exceptions.HTTPError as e:
            st.error(f"API Error {e.response.status_code}: {e.response.text[:300]}")
            return None
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
            last_err = e
            if attempt < retries:
                st.warning(f"⏳ Request timed out, retrying ({attempt}/{retries})...")
                time.sleep(2)
            else:
                st.error(
                    f"Connection error after {retries} attempts: {e}\n\n"
                    "💡 The ECS task may be cold-starting. Wait ~30s and try again."
                )
                return None
        except Exception as e:
            st.error(f"Unexpected error: {e}")
            return None
    return None


def api_get(path: str, params: dict = None):
    """GET request to the API with retry."""
    r = _request_with_retry("GET", f"{API}{path}", params=params)
    return r.json() if r else None


def api_post(path: str, json_body: dict = None, files=None, params=None):
    """POST request to the API with retry."""
    r = _request_with_retry("POST", f"{API}{path}", json=json_body, files=files, params=params)
    return r.json() if r else None


@st.fragment
def speak_text(text: str, language: str = "en", key: str = "tts"):
    """
    Render a 🔊 Listen button that fetches TTS audio from Polly and plays it.
    Uses Kajal (neural) for English, Aditi (bilingual) for Hindi.
    Wrapped in @st.fragment to avoid full page reruns.
    """
    if not text or not text.strip():
        return
    btn_label = "🔊 Listen" if language == "en" else "🔊 सुनें"
    if st.button(btn_label, key=f"tts_{key}", width="content"):
        with st.spinner("🔊 Generating audio..."):
            r = _request_with_retry(
                "POST",
                f"{API}/tts/synthesize",
                json={"text": text, "language": language},
            )
            if r:
                st.audio(r.content, format="audio/mpeg", autoplay=True)
            else:
                st.error("Could not generate audio.")


def display_quality(q: dict):
    """Render a quality assessment result with Bedrock AI recommendations."""
    grade = q.get("overall_grade", "N/A")
    grade_colors = {
        "excellent": "🟢", "good": "🔵", "average": "🟡", "poor": "🔴"
    }
    icon = grade_colors.get(grade, "⚪")

    col1, col2, col3 = st.columns(3)
    col1.metric("Quality Grade", f"{icon} {grade.title()}")
    col2.metric("Quality Score", f"{q.get('quality_score', 'N/A')}/100")
    col3.metric(
        "Freshness",
        q.get("freshness_status", q.get("freshness_label", "N/A")),
    )

    if "confidence" in q:
        st.progress(min(q["confidence"], 1.0), text=f"Confidence: {q['confidence']:.0%}")

    # ── Bedrock AI Recommendations (English + Hindi) ──
    recs = q.get("recommendations", {})
    bedrock_recs = q.get("bedrock_recommendations", {})

    if isinstance(recs, dict) and (recs.get("english") or recs.get("hindi")):
        # Urgency badge
        urgency = recs.get("urgency", "medium")
        urgency_map = {
            "low": ("🟢", "No rush"),
            "medium": ("🟡", "Sell soon"),
            "high": ("🟠", "Act quickly"),
            "critical": ("🔴", "Urgent!"),
        }
        urg_icon, urg_text = urgency_map.get(urgency, ("⚪", urgency))
        action = recs.get("action", "")
        source = recs.get("source", bedrock_recs.get("source", ""))

        st.markdown("---")
        hdr_col1, hdr_col2, hdr_col3 = st.columns([2, 1, 1])
        hdr_col1.markdown(f"### 🤖 AI Farmer Recommendations")
        hdr_col2.markdown(f"**Urgency:** {urg_icon} {urg_text}")
        if source == "bedrock":
            hdr_col3.caption("Powered by Amazon Bedrock")

        # English tab and Hindi tab
        tab_en, tab_hi = st.tabs(["🇬🇧 English", "🇮🇳 हिंदी"])

        with tab_en:
            rec_en = recs.get("english", "")
            if rec_en:
                st.info(f"📋 **Recommendation:** {rec_en}")
            storage_en = recs.get("storage_tips_en", "")
            if storage_en:
                st.success(f"🏪 **Storage Tips:** {storage_en}")
            sell_en = recs.get("selling_strategy_en", "")
            if sell_en:
                st.warning(f"💰 **Selling Strategy:** {sell_en}")
            # 🔊 Read aloud all English recommendations
            full_en = ". ".join(filter(None, [rec_en, storage_en, sell_en]))
            speak_text(full_en, language="en", key="quality_rec_en")

        with tab_hi:
            rec_hi = recs.get("hindi", "")
            if rec_hi:
                st.info(f"📋 **सिफारिश:** {rec_hi}")
            storage_hi = recs.get("storage_tips_hi", "")
            if storage_hi:
                st.success(f"🏪 **भंडारण सुझाव:** {storage_hi}")
            sell_hi = recs.get("selling_strategy_hi", "")
            if sell_hi:
                st.warning(f"💰 **बिक्री रणनीति:** {sell_hi}")
            # 🔊 Read aloud all Hindi recommendations
            full_hi = ". ".join(filter(None, [rec_hi, storage_hi, sell_hi]))
            speak_text(full_hi, language="hi", key="quality_rec_hi")

    elif isinstance(recs, list) and recs:
        # Legacy list-style recommendations
        st.markdown("**📋 Recommendations:**")
        for rec in recs:
            if isinstance(rec, dict):
                st.markdown(f"- {rec.get('text', rec.get('en', str(rec)))}")
            else:
                st.markdown(f"- {rec}")


def display_pricing(p: dict):
    """Render a price recommendation result."""
    # ── Price headline ──
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("💰 Ideal Price", f"₹{p.get('ideal_price', 0):.2f}/kg")
    col2.metric("📉 Min (Floor)", f"₹{p.get('recommended_min_price', 0):.2f}/kg")
    col3.metric("📈 Max Price", f"₹{p.get('recommended_max_price', 0):.2f}/kg")
    col4.metric("🏪 Market Price", f"₹{p.get('predicted_market_price', 0):.2f}/kg")

    # ── Confidence (0-1 scale) ──
    confidence = p.get("confidence_score", 0)
    if confidence:
        st.progress(min(float(confidence), 1.0), text=f"Model Confidence: {confidence * 100:.0f}%")

    # ── Model & source badges ──
    badge_cols = st.columns(4)
    model_type = p.get("model_type", "unknown")
    badge_cols[0].caption(f"🤖 Model: **{model_type}**")
    source = p.get("price_source", "unknown")
    if source == "data.gov.in":
        badge_cols[1].caption("📡 **Live mandi data**")
    else:
        badge_cols[1].caption(f"📊 Source: {source}")
    trend = p.get("trend", "stable")
    trend_icon = {"rising": "📈", "falling": "📉", "stable": "➡️"}.get(trend, "➡️")
    badge_cols[2].caption(f"{trend_icon} Trend: **{trend}**")
    demand = p.get("demand_index")
    if demand is not None:
        badge_cols[3].caption(f"🔥 Demand: **{demand * 100:.0f}%**")

    # ── Action recommendation ──
    action = p.get("action", "")
    action_text = p.get("action_text", "")
    if action == "sell_now":
        st.success(f"🎯 **Sell Now** — {action_text}")
    elif action == "wait":
        st.info(f"⏳ **Wait** — {action_text}")
    elif action == "store":
        st.warning(f"🏪 **Store** — {action_text}")

    # ── Recommendation text ──
    rec_text = p.get("recommendation_text")
    if rec_text:
        st.info(f"📝 {rec_text}")

    # 🔊 Read aloud pricing recommendation
    price_speech = ". ".join(filter(None, [action_text, rec_text or ""]))
    speak_text(price_speech, language="en", key="price_rec")

    # ── MSP note ──
    msp_note = p.get("msp_note")
    if msp_note:
        st.caption(msp_note)

    # ── Price range visualization ──
    lower = p.get("price_range_lower", 0)
    upper = p.get("price_range_upper", 0)
    ideal = p.get("ideal_price", 0)
    avg_7d = p.get("avg_7d", 0)
    if lower and upper and ideal:
        import plotly.graph_objects as go
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=["Price Range"], y=[upper - lower], base=[lower],
            marker_color="rgba(76, 175, 80, 0.3)", name="Range",
            width=0.4, showlegend=True,
        ))
        fig.add_hline(y=ideal, line_dash="solid", line_color="green",
                      annotation_text=f"Ideal ₹{ideal:.1f}")
        if avg_7d:
            fig.add_hline(y=avg_7d, line_dash="dot", line_color="blue",
                          annotation_text=f"7d Avg ₹{avg_7d:.1f}")
        market = p.get("predicted_market_price", 0)
        if market:
            fig.add_hline(y=market, line_dash="dash", line_color="orange",
                          annotation_text=f"Market ₹{market:.1f}")
        fig.update_layout(
            title="Price Range Visualization",
            yaxis_title="₹/kg", height=300,
            margin=dict(l=40, r=40, t=40, b=40),
        )
        st.plotly_chart(fig, width="stretch")

    # ── Factors ──
    factors = p.get("factors", [])
    if factors:
        with st.expander("📊 Price Factors", expanded=True):
            for f in factors:
                if isinstance(f, dict):
                    name = f.get("name", "")
                    value = f.get("value", "")
                    impact = f.get("impact", "")
                    weight = f.get("weight")
                    impact_icon = {
                        "positive": "🟢", "negative": "🔴",
                        "neutral": "⚪", "baseline": "🔵", "reference": "📌",
                        "protection": "🛡️",
                    }.get(impact, "⚪")
                    weight_str = f" (weight: {weight:.0%})" if weight else ""
                    st.markdown(f"- {impact_icon} **{name}**: {value}{weight_str}")

    # ── 3-Day Forecast ──
    forecast = p.get("price_forecast_3d", [])
    if forecast:
        with st.expander("📈 3-Day Price Forecast"):
            for day in forecast:
                if isinstance(day, dict):
                    trend_icon = {"rising": "📈", "falling": "📉", "stable": "➡️"}.get(
                        day.get("trend", ""), "➡️")
                    conf = day.get("confidence", 0)
                    st.markdown(
                        f"- **{day.get('date', '?')}**: "
                        f"₹{day.get('predicted_price', '?')}/kg "
                        f"{trend_icon} (confidence: {conf * 100:.0f}%)"
                    )

    # ── What-If Scenarios ──
    scenarios = p.get("what_if_scenarios", [])
    if scenarios:
        with st.expander("🔮 What-If Scenarios"):
            for s in scenarios:
                if isinstance(s, dict):
                    change = s.get("price_change", "")
                    new_price = s.get("new_ideal_price", 0)
                    st.markdown(
                        f"**{s.get('scenario', '')}**\n\n"
                        f"Price change: {change} → New ideal: ₹{new_price:.2f}/kg\n\n"
                        f"💡 _{s.get('recommendation', '')}_"
                    )
                    st.divider()


def display_mandi(data: dict):
    """Render mandi price data as a table."""
    records = data.get("records", [])
    if not records:
        st.warning("No mandi records found.")
        return

    st.caption(
        f"Source: {data.get('source', 'N/A')} | "
        f"Total mandis: {data.get('total', len(records))}"
    )

    # Summary stats
    prices = [r.get("modal_price_per_kg", 0) for r in records if r.get("modal_price_per_kg")]
    if prices:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Avg ₹/kg", f"₹{sum(prices)/len(prices):.2f}")
        c2.metric("Min ₹/kg", f"₹{min(prices):.2f}")
        c3.metric("Max ₹/kg", f"₹{max(prices):.2f}")
        c4.metric("Mandis", len(records))

    # Table
    table_data = []
    for r in records[:20]:
        table_data.append({
            "State": r.get("state", ""),
            "District": r.get("district", ""),
            "Market": r.get("market", ""),
            "Modal ₹/kg": r.get("modal_price_per_kg", ""),
            "Min ₹/kg": r.get("min_price_per_kg", ""),
            "Max ₹/kg": r.get("max_price_per_kg", ""),
            "Date": r.get("arrival_date", ""),
        })
    st.dataframe(table_data, width="stretch")


# ═════════════════════════════════════════════════════════
#  Authentication UI (shown when not logged in)
# ═════════════════════════════════════════════════════════

def _show_auth_ui():
    """Render login / register / OTP verification forms."""
    st.markdown("## 🌾 Welcome to SwadeshAI")
    st.markdown("Sign in or create an account to access the dashboard.")
    st.divider()

    auth_mode = st.session_state.auth_page

    # ── Registration ──────────────────────────────────────
    if auth_mode == "register":
        st.subheader("📝 Create Account")
        with st.form("register_form"):
            reg_name = st.text_input("Full Name *")
            reg_mobile = st.text_input("Mobile Number *", placeholder="+919876543210")
            reg_type = st.selectbox("I am a", ["seller", "buyer", "logistic"],
                                    format_func=lambda x: {"seller": "🧑‍🌾 Seller / Farmer",
                                                           "buyer": "🛒 Buyer",
                                                           "logistic": "🚚 Logistics Provider"}.get(x, x))
            reg_business = st.text_input("Business Name (optional)")
            col_city, col_state, col_pin = st.columns(3)
            with col_city:
                reg_city = st.text_input("City")
            with col_state:
                reg_state = st.selectbox("State", [""] + STATES)
            with col_pin:
                reg_pincode = st.text_input("Pincode", max_chars=6)

            submitted = st.form_submit_button("Register", type="primary")
            if submitted:
                if not reg_name or not reg_mobile:
                    st.error("Name and Mobile Number are required.")
                else:
                    payload = {
                        "mobile_number": reg_mobile,
                        "user_type": reg_type,
                        "name": reg_name,
                    }
                    if reg_business:
                        payload["business_name"] = reg_business
                    if reg_city:
                        payload["city"] = reg_city
                    if reg_state:
                        payload["state"] = reg_state
                    if reg_pincode:
                        payload["pincode"] = reg_pincode

                    try:
                        r = requests.post(f"{AUTH_API}/register", json=payload, timeout=15)
                        if r.status_code == 200:
                            data = r.json()
                            st.success(f"✅ {data.get('message', 'Registered!')} — please log in.")
                            st.session_state.auth_page = "login"
                            time.sleep(1)
                            st.rerun()
                        else:
                            try:
                                detail = r.json().get("detail", r.text[:200])
                            except Exception:
                                detail = r.text[:200] or f"HTTP {r.status_code}"
                            st.error(f"Registration failed: {detail}")
                    except requests.exceptions.ConnectionError:
                        st.error(f"Cannot reach backend at `{api_url}`. Is the server running?")
                    except Exception as e:
                        st.error(f"Registration error: {e}")

        st.markdown("---")
        if st.button("Already have an account? **Log in**"):
            st.session_state.auth_page = "login"
            st.rerun()

    # ── OTP Verification ──────────────────────────────────
    elif auth_mode == "otp":
        ctx = st.session_state.otp_context
        st.subheader("🔑 Enter OTP")
        st.info(f"OTP sent to **{ctx.get('mobile_number', '')}**")
        if ctx.get("demo_otp"):
            st.warning(f"🧪 **Demo mode** — your OTP is: `{ctx['demo_otp']}`")

        with st.form("otp_form"):
            otp_input = st.text_input("Enter 6-digit OTP", max_chars=6)
            verify_btn = st.form_submit_button("Verify & Login", type="primary")
            if verify_btn:
                if not otp_input or len(otp_input) < 4:
                    st.error("Please enter a valid OTP.")
                else:
                    try:
                        r = requests.post(f"{AUTH_API}/login/verify-otp", json={
                            "mobile_number": ctx["mobile_number"],
                            "user_type": ctx["user_type"],
                            "otp": otp_input,
                        }, timeout=15)
                        if r.status_code == 200:
                            data = r.json()
                            st.session_state.auth_token = data["access_token"]
                            st.session_state.auth_user = {
                                "user_id": data.get("user_id"),
                                "user_type": data.get("user_type"),
                                "name": data.get("name"),
                                "mobile_number": data.get("mobile_number"),
                            }
                            st.session_state.otp_context = {}
                            st.success(f"✅ Welcome, {data.get('name', 'User')}!")
                            time.sleep(1)
                            st.rerun()
                        else:
                            try:
                                detail = r.json().get("detail", r.text[:200])
                            except Exception:
                                detail = r.text[:200] or f"HTTP {r.status_code}"
                            st.error(f"Verification failed: {detail}")
                    except requests.exceptions.ConnectionError:
                        st.error(f"Cannot reach backend at `{api_url}`. Is the server running?")
                    except Exception as e:
                        st.error(f"OTP verification error: {e}")

        if st.button("⬅️ Back to Login"):
            st.session_state.auth_page = "login"
            st.session_state.otp_context = {}
            st.rerun()

    # ── Login (default) ───────────────────────────────────
    else:
        st.subheader("🔐 Login")
        with st.form("login_form"):
            login_mobile = st.text_input("Mobile Number", placeholder="+919876543210")
            login_type = st.selectbox("I am a", ["seller", "buyer", "logistic"],
                                      format_func=lambda x: {"seller": "🧑‍🌾 Seller / Farmer",
                                                              "buyer": "🛒 Buyer",
                                                              "logistic": "🚚 Logistics Provider"}.get(x, x))
            login_btn = st.form_submit_button("Request OTP", type="primary")
            if login_btn:
                if not login_mobile:
                    st.error("Please enter your mobile number.")
                else:
                    try:
                        r = requests.post(f"{AUTH_API}/login/request-otp", json={
                            "mobile_number": login_mobile,
                            "user_type": login_type,
                        }, timeout=15)
                        if r.status_code == 200:
                            data = r.json()
                            st.session_state.otp_context = {
                                "mobile_number": login_mobile,
                                "user_type": login_type,
                                "demo_otp": data.get("demo_otp"),
                            }
                            st.session_state.auth_page = "otp"
                            st.rerun()
                        else:
                            try:
                                detail = r.json().get("detail", r.text[:200])
                            except Exception:
                                detail = r.text[:200] or f"HTTP {r.status_code}"
                            st.error(f"Login failed: {detail}")
                    except requests.exceptions.ConnectionError:
                        st.error(f"Cannot reach backend at `{api_url}`. Is the server running?")
                    except Exception as e:
                        st.error(f"Login error: {e}")

        st.markdown("---")
        if st.button("New user? **Create account**"):
            st.session_state.auth_page = "register"
            st.rerun()


# ── Show auth UI or main app ─────────────────────────────
if not st.session_state.auth_token:
    _show_auth_ui()
    st.stop()


# ═════════════════════════════════════════════════════════
#  Pages  (only reachable when authenticated)
# ═════════════════════════════════════════════════════════

# ── Page 0: Freshness + Pricing (Simulated) ──────────────
if page == "🔬 Freshness + Pricing":
    st.header("🔬 Freshness Detection + Price Recommendation")
    st.markdown(
        "Simulated quality assessment → ML-powered pricing with live mandi data.  \n"
        "No image required — great for demo."
    )

    col1, col2 = st.columns(2)
    with col1:
        crop = st.selectbox("Select Crop", CROPS, index=0)
        quantity = st.number_input("Quantity (kg)", min_value=1, value=100, step=10)
    with col2:
        storage = st.selectbox("Storage Type", STORAGE_TYPES, index=0)
        state = st.selectbox("State (for mandi lookup)", ["Any"] + STATES, index=0)

    if st.button("🚀 Run Freshness + Pricing Pipeline", type="primary", width="stretch"):
        with st.spinner("Running AI pipeline..."):
            params = {"quantity_kg": quantity, "storage_type": storage}
            if state != "Any":
                params["state"] = state

            data = api_get(f"/quality/simulate-and-price/{crop}", params=params)

        if data:
            st.divider()

            # Quality Assessment
            st.subheader("🔍 Quality Assessment")
            quality = data.get("quality_assessment", {})
            display_quality(quality)

            # 🔊 Read aloud recommendations
            recs = quality.get("recommendations", {})
            if isinstance(recs, dict):
                rec_en = recs.get("english", "")
                if rec_en:
                    speak_text(rec_en, language="en", key="freshness_rec_en")

            st.divider()

            # Price Recommendation
            st.subheader("💰 Price Recommendation")
            pricing = data.get("price_recommendation", {})
            display_pricing(pricing)

            # 🔊 Read aloud pricing
            action_text = pricing.get("action_text", "")
            rec_text = pricing.get("recommendation_text", "")
            if action_text:
                speak_text(f"{action_text}. {rec_text or ''}", language="en", key="freshness_price")

            st.divider()

            # Mandi Prices
            mandi = data.get("mandi_prices", {})
            if mandi.get("records"):
                st.subheader("🏪 Nearby Mandi Prices")
                display_mandi(mandi)

            # Raw JSON
            with st.expander("🔧 Raw API Response"):
                st.json(data)


# ── Page 1: Image Assessment ─────────────────────────────
elif page == "📸 Image Assessment":
    st.header("📸 Upload Produce Image for Assessment")
    st.markdown(
        "Upload a photo of your produce for AI-powered freshness detection.  \n"
        "The image is sent to the AWS backend for analysis via SageMaker/Rekognition."
    )

    col1, col2 = st.columns(2)
    with col1:
        crop = st.selectbox("Crop Name", CROPS, index=0)
        quantity = st.number_input("Quantity (kg)", min_value=1, value=100, step=10)
    with col2:
        storage = st.selectbox("Storage Type", STORAGE_TYPES, index=0)
        uploaded_file = st.file_uploader(
            "Upload produce image",
            type=["jpg", "jpeg", "png", "webp"],
            help="Max 10MB",
        )

    if uploaded_file:
        st.image(uploaded_file, caption=f"{crop.title()} — uploaded image", width=300)

    if st.button("🔬 Analyze & Get Price", type="primary", width="stretch", disabled=not uploaded_file):
        with st.spinner("Analyzing image with AI..."):
            files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
            params = {
                "crop_name": crop,
                "quantity_kg": quantity,
                "storage_type": storage,
            }
            data = api_post("/quality/assess-and-price", files=files, params=params)

        if data:
            st.divider()

            st.subheader("🔍 Quality Assessment")
            display_quality(data.get("quality_assessment", {}))

            st.divider()

            st.subheader("💰 Price Recommendation")
            display_pricing(data.get("price_recommendation", {}))

            mandi = data.get("mandi_prices", {})
            if mandi.get("records"):
                st.divider()
                st.subheader("🏪 Mandi Prices")
                display_mandi(mandi)

            with st.expander("🔧 Raw API Response"):
                st.json(data)


# ── Page 3: Direct Price Recommendation ──────────────────
elif page == "💰 Price Recommendation":
    st.header("💰 AI Price Recommendation")
    st.markdown("Get ML-powered price recommendations using XGBoost + live mandi data.")

    col1, col2 = st.columns(2)
    with col1:
        crop = st.selectbox("Crop", CROPS, index=0)
        quantity = st.number_input("Quantity (kg)", min_value=1, value=100, step=10)
        quality_grade = st.selectbox("Quality Grade", QUALITY_GRADES, index=1)
    with col2:
        spoilage_risk = st.selectbox("Spoilage Risk", SPOILAGE_RISKS, index=0)
        storage = st.selectbox("Storage Type", STORAGE_TYPES, index=0)
        shelf_life = st.number_input("Remaining Shelf Life (days)", min_value=0, value=5, step=1)

    if st.button("💰 Get Price Recommendation", type="primary", width="stretch"):
        with st.spinner("Running ML pricing model..."):
            body = {
                "crop_name": crop,
                "quantity_kg": quantity,
                "quality_grade": quality_grade,
                "spoilage_risk": spoilage_risk,
                "storage_type": storage,
                "remaining_shelf_life_days": shelf_life if shelf_life > 0 else None,
            }
            data = api_post("/pricing/recommend", json_body=body)

        if data:
            st.divider()
            display_pricing(data)

            with st.expander("🔧 Raw API Response"):
                st.json(data)


# ── Page 4: Mandi Prices ─────────────────────────────────
elif page == "📊 Mandi Prices":
    st.header("📊 Live Mandi Prices")
    st.markdown("Real-time commodity prices from **data.gov.in** mandis across India.")

    col1, col2, col3 = st.columns(3)
    with col1:
        commodity = st.selectbox("Commodity", CROPS, index=0)
    with col2:
        state = st.selectbox("State", ["All States"] + STATES, index=0)
    with col3:
        limit = st.number_input("Max Records", min_value=5, max_value=100, value=30, step=5)

    if st.button("📡 Fetch Mandi Prices", type="primary", width="stretch"):
        with st.spinner("Fetching live mandi data..."):
            params = {"limit": limit}
            if state != "All States":
                params["state"] = state
            data = api_get(f"/pricing/mandi/prices/{commodity}", params=params)

        if data:
            display_mandi(data)

            with st.expander("🔧 Raw API Response"):
                st.json(data)

    st.divider()

    # Mandi comparison
    st.subheader("🔄 Compare Prices Across States")
    compare_crop = st.selectbox("Commodity to compare", CROPS, index=0, key="compare_crop")
    selected_states = st.multiselect("Select states to compare", STATES, default=["Maharashtra", "Karnataka"])

    if st.button("🔄 Compare", width="stretch", disabled=len(selected_states) < 2):
        with st.spinner("Comparing prices..."):
            params = {"states": ",".join(selected_states)}
            data = api_get(f"/pricing/mandi/compare/{compare_crop}", params=params)

        if data:
            best = data.get("best_market")
            if best:
                st.success(
                    f"🏆 Best market: **{best['market']}** ({best['state']}) — "
                    f"₹{best['modal_price_per_kg']}/kg"
                )

            for summary in data.get("state_summaries", []):
                with st.expander(
                    f"📍 {summary['state']} — Avg ₹{summary['avg_price_per_kg']}/kg "
                    f"({summary['num_mandis']} mandis)"
                ):
                    for m in summary.get("markets", []):
                        st.markdown(f"- **{m['market']}**: ₹{m['modal_price_per_kg']}/kg")


# ── Page 5: Weather Forecast & Crop Health ───────────────
elif page == "📈 Trends & Forecast":
    st.header("🌦️ Weather-Based Crop Health & Price Forecast")
    st.markdown(
        "Uses **OpenWeatherMap 5-day forecast** to predict how upcoming weather "
        "affects your crop's shelf life, spoilage risk, and market prices."
    )

    col1, col2, col3 = st.columns(3)
    with col1:
        crop = st.selectbox("Crop", CROPS, index=0)
        quality_grade = st.selectbox("Quality Grade", QUALITY_GRADES, index=1)
    with col2:
        city = st.text_input("City (for weather)", value="Delhi")
        storage = st.selectbox("Storage Type", STORAGE_TYPES, index=0, key="forecast_storage")
    with col3:
        forecast_days = st.slider("Forecast Days", 1, 5, 5)
        harvest_days_ago = st.number_input("Harvested (days ago)", min_value=0, value=1, step=1)

    if st.button("🌦️ Generate Weather Forecast", type="primary", width="stretch"):
        with st.spinner("Fetching weather forecast and analyzing crop impact..."):
            params = {
                "days_ahead": forecast_days,
                "city": city,
                "quality_grade": quality_grade,
                "storage_type": storage,
                "harvest_days_ago": harvest_days_ago,
            }
            data = api_get(f"/pricing/weather-forecast/{crop}", params=params)

        if data:
            st.divider()

            # ── Overview metrics ──
            overview_cols = st.columns(5)
            overview_cols[0].metric("📍 Location", data.get("location", "N/A"))
            overview_cols[1].metric("🏪 Market Price", f"₹{data.get('current_market_price', 0):.2f}/kg")
            overview_cols[2].metric("📦 Shelf Life Left", f"{data.get('remaining_shelf_life_days', 0)} days")
            best_price = data.get("best_projected_price", 0)
            market = data.get("current_market_price", 0)
            price_diff = best_price - market if market else 0
            overview_cols[3].metric("💰 Best Price", f"₹{best_price:.2f}/kg", f"{price_diff:+.2f}")
            overview_cols[4].metric("📡 Source", data.get("price_source", "N/A"))

            # ── Overall recommendation ──
            action = data.get("overall_action", "")
            reason = data.get("overall_reason", "")
            best_day = data.get("best_selling_day", "")
            if action == "sell_now":
                st.error(f"🎯 **SELL NOW** — {reason}")
            elif action == "wait":
                st.success(f"⏳ **WAIT** (best day: {best_day}) — {reason}")
            elif action == "store":
                st.info(f"🏪 **STORE** — {reason}")

            health_trend = data.get("health_trend", "unknown")
            st.caption(f"Health trend: **{health_trend}** | Weather source: {data.get('weather_source', 'N/A')}")

            st.divider()

            # ── Daily forecast cards ──
            daily = data.get("daily_forecast", [])
            if daily:
                try:
                    import plotly.graph_objects as go
                    from plotly.subplots import make_subplots

                    dates = [d["date"] for d in daily]
                    health_scores = [d["crop_health"]["health_score"] for d in daily]
                    prices = [d["price_impact"]["projected_price"] for d in daily]
                    temps = [d["weather"]["temp_avg"] for d in daily]
                    rainfall = [d["weather"]["rainfall_mm"] for d in daily]

                    fig = make_subplots(
                        rows=2, cols=2,
                        subplot_titles=(
                            "Crop Health Score", "Projected Price ₹/kg",
                            "Temperature °C", "Rainfall mm",
                        ),
                        vertical_spacing=0.15,
                    )

                    # Health score
                    health_colors = ["#2ecc71" if h > 70 else "#f39c12" if h > 40 else "#e74c3c" for h in health_scores]
                    fig.add_trace(go.Bar(x=dates, y=health_scores, marker_color=health_colors, name="Health"), row=1, col=1)
                    fig.add_hline(y=50, line_dash="dash", line_color="red", row=1, col=1, annotation_text="Risk threshold")

                    # Price
                    fig.add_trace(go.Scatter(x=dates, y=prices, mode="lines+markers", name="Price ₹/kg", line=dict(color="#3498db")), row=1, col=2)
                    fig.add_hline(y=market, line_dash="dot", line_color="orange", row=1, col=2, annotation_text=f"Current ₹{market:.1f}")

                    # Temperature
                    temp_colors = ["#e74c3c" if t > 35 else "#f39c12" if t > 28 else "#2ecc71" for t in temps]
                    fig.add_trace(go.Bar(x=dates, y=temps, marker_color=temp_colors, name="Temp °C"), row=2, col=1)

                    # Rainfall
                    fig.add_trace(go.Bar(x=dates, y=rainfall, marker_color="#3498db", name="Rain mm"), row=2, col=2)

                    fig.update_layout(height=500, showlegend=False, margin=dict(t=40))
                    st.plotly_chart(fig, width="stretch")

                except ImportError:
                    pass

                # ── Detail cards per day ──
                for day in daily:
                    w = day["weather"]
                    ch = day["crop_health"]
                    pi = day["price_impact"]

                    risk_icon = {"low": "🟢", "medium": "🟡", "high": "🔴"}.get(ch["weather_risk"], "⚪")
                    condition_icon = {
                        "Clear": "☀️", "Clouds": "☁️", "Rain": "🌧️",
                        "Drizzle": "🌦️", "Thunderstorm": "⛈️", "Mist": "🌫️",
                    }.get(w["condition"], "🌤️")

                    with st.expander(
                        f"{condition_icon} **{day['date']}** — Health: {ch['health_score']:.0f}/100 {risk_icon} | "
                        f"₹{pi['projected_price']}/kg ({pi['net_impact_pct']:+.1f}%)"
                    ):
                        wc1, wc2, wc3, wc4 = st.columns(4)
                        wc1.metric("🌡️ Temp", f"{w['temp_avg']}°C", f"Max {w['temp_max']}°C")
                        wc2.metric("💧 Humidity", f"{w['humidity']}%")
                        wc3.metric("🌧️ Rain", f"{w['rainfall_mm']} mm")
                        wc4.metric("💨 Wind", f"{w['wind_speed']} m/s")

                        hc1, hc2, hc3 = st.columns(3)
                        hc1.metric("❤️ Health", f"{ch['health_score']:.0f}/100")
                        hc2.metric("📦 Shelf Life", f"{ch['effective_shelf_life_days']:.1f} days")
                        hc3.metric("⚡ Degradation", f"{ch['daily_degradation_rate']:.2f}x")

                        sf = ch["spoilage_factors"]
                        st.caption(
                            f"Spoilage factors — Temp: {sf['temperature']:.2f}x | "
                            f"Humidity: {sf['humidity']:.2f}x | Rain: {sf['rainfall']:.2f}x"
                        )

                        st.info(f"📝 {day['advisory']}")

            with st.expander("🔧 Raw API Response"):
                st.json(data)


# ── Page 6: Causal AI Analysis ───────────────────────────
elif page == "🔬 Causal AI":
    st.header("🔬 Causal AI — Why Things Happen")
    st.markdown(
        "Uses **DoWhy causal inference** to answer *why* — not just *what* — happens.  \n"
        "Rigorous backdoor-adjustment and propensity-score matching to uncover real causal effects."
    )

    analysis_type = st.selectbox(
        "Select Causal Analysis",
        [
            "🧊 Cold Storage → Spoilage Reduction",
            "🌡️ Weather → Market Prices",
            "⭐ Quality → Price Premium",
        ],
    )

    col1, col2 = st.columns(2)
    with col1:
        causal_crop = st.selectbox("Crop", CROPS, index=0, key="causal_crop")
    with col2:
        if "Weather" in analysis_type:
            causal_location = st.text_input("Location", value="Delhi", key="causal_loc")

    if st.button("🔬 Run Causal Analysis", type="primary", width="stretch"):
        with st.spinner("Running causal inference with DoWhy..."):
            if "Storage" in analysis_type:
                data = api_get("/causal/storage-spoilage", params={
                    "crop_name": causal_crop,
                })
            elif "Weather" in analysis_type:
                data = api_get("/causal/weather-prices", params={
                    "crop_name": causal_crop,
                    "location": causal_location,
                })
            else:
                data = api_get("/causal/quality-premium", params={
                    "crop_name": causal_crop,
                })

        if data and data.get("success"):
            analysis = data.get("analysis", {})
            st.divider()

            # Show demo badge if using pre-computed results
            method = analysis.get("method", "")
            if "pre-computed" in method.lower() or "demo" in method.lower():
                st.info("🧪 **Demo Mode** — showing pre-computed causal analysis results. "
                        "Deploy with DoWhy for live inference.")

            # ── Question & answer ──
            st.subheader(f"❓ {analysis.get('question', '')}")
            st.info(f"**Treatment:** {analysis.get('treatment', '')}")
            st.caption(f"**Outcome:** {analysis.get('outcome', '')}")

            # ── Key metrics ──
            met1, met2, met3 = st.columns(3)
            ate = analysis.get("average_treatment_effect", 0)
            met1.metric("📊 Causal Effect (ATE)", f"{ate:+.2f}")
            met2.metric("🎯 Confidence", analysis.get("confidence", "N/A"))
            robust = analysis.get("sensitivity_robust", False)
            met3.metric("🛡️ Robust", "✅ Yes" if robust else "⚠️ Needs review")

            # ── Interpretation ──
            st.success(f"📝 **Interpretation:** {analysis.get('interpretation', '')}")
            st.warning(f"💡 **Recommendation:** {analysis.get('recommendation', '')}")
            speak_text(
                f"{analysis.get('interpretation', '')}. {analysis.get('recommendation', '')}",
                language="en", key="causal_rec",
            )

            # ── Data summary ──
            summary = analysis.get("data_summary", {})
            if summary:
                with st.expander("📊 Data Summary", expanded=True):
                    summary_cols = st.columns(len(summary))
                    for i, (k, v) in enumerate(summary.items()):
                        label = k.replace("_", " ").title()
                        summary_cols[i % len(summary_cols)].metric(label, f"{v}")

            # ── Mechanism / Insight ──
            mechanism = analysis.get("mechanism")
            if mechanism:
                st.info(f"⚙️ **Causal Mechanism:** {mechanism}")
            insight = analysis.get("actionable_insight")
            if insight:
                st.success(f"🎯 **Actionable Insight:** {insight}")

            st.caption(f"Method: {analysis.get('method', '')} | Sample: {analysis.get('sample_size', '')}")

            with st.expander("🔧 Raw API Response"):
                st.json(data)
        elif data:
            st.error(f"Analysis failed: {data.get('error', 'Unknown error')}")


# ── Page 7: Weather Dashboard ────────────────────────────
elif page == "🌤️ Weather":
    st.header("🌤️ Weather Dashboard")
    st.markdown(
        "Real-time weather data and 5-day agricultural forecast via **OpenWeatherMap**.  \n"
        "Includes spoilage risk assessment based on temperature, humidity, and rainfall."
    )

    weather_city = st.text_input("Enter City Name", value="Delhi", key="weather_city")

    wcol1, wcol2 = st.columns(2)
    with wcol1:
        get_current = st.button("☀️ Current Weather", type="primary", width="stretch")
    with wcol2:
        get_forecast = st.button("📅 5-Day Forecast", type="primary", width="stretch")

    if get_current:
        with st.spinner("Fetching weather..."):
            data = api_get(f"/weather/city/{weather_city}")

        if data:
            st.divider()
            st.subheader(f"☀️ Current Weather — {data.get('city', weather_city)}")

            wc1, wc2, wc3, wc4, wc5 = st.columns(5)
            temp = data.get("temperature", 0)
            temp_color = "🔴" if temp > 35 else "🟡" if temp > 28 else "🟢"
            wc1.metric(f"{temp_color} Temperature", f"{temp}°C")
            wc2.metric("💧 Humidity", f"{data.get('humidity', 0)}%")
            wc3.metric("🌬️ Pressure", f"{data.get('pressure', 0)} hPa")
            wc4.metric("💨 Wind", f"{data.get('wind_speed', 0)} m/s")
            wc5.metric("🌧️ Rain (1h)", f"{data.get('rainfall_1h', 0)} mm")

            st.info(f"🌤️ Condition: **{data.get('description', 'N/A').title()}**")
            st.caption(f"Source: {data.get('source', 'N/A')}")

            # Temperature advisory
            if temp > 35:
                st.error("🔴 **Extreme heat!** Move perishable produce to cold storage immediately.")
            elif temp > 28:
                st.warning("🟡 **Above optimal** for most produce storage. Keep in shade with ventilation.")
            else:
                st.success("🟢 Temperature is manageable for produce storage.")

            with st.expander("🔧 Raw API Response"):
                st.json(data)

    if get_forecast:
        with st.spinner("Fetching 5-day forecast..."):
            data = api_get(f"/weather/forecast/city/{weather_city}")

        if data:
            st.divider()
            st.subheader(f"📅 5-Day Forecast — {weather_city}")

            # ── Forecast chart ──
            if isinstance(data, list) and data:
                try:
                    import plotly.graph_objects as go
                    from plotly.subplots import make_subplots

                    dates = [d["date"] for d in data]
                    temps = [d["temp_avg"] for d in data]
                    humidity = [d["humidity_avg"] for d in data]
                    rain = [d["rainfall_mm"] for d in data]

                    fig = make_subplots(
                        rows=1, cols=3,
                        subplot_titles=("Temperature °C", "Humidity %", "Rainfall mm"),
                    )
                    temp_colors = ["#e74c3c" if t > 35 else "#f39c12" if t > 28 else "#2ecc71" for t in temps]
                    fig.add_trace(go.Bar(x=dates, y=temps, marker_color=temp_colors, name="Temp"), row=1, col=1)
                    fig.add_trace(go.Bar(x=dates, y=humidity, marker_color="#3498db", name="Humidity"), row=1, col=2)
                    fig.add_trace(go.Bar(x=dates, y=rain, marker_color="#2980b9", name="Rain"), row=1, col=3)
                    fig.update_layout(height=350, showlegend=False, margin=dict(t=40))
                    st.plotly_chart(fig, width="stretch")
                except ImportError:
                    pass

                # ── Daily cards ──
                for day in data:
                    condition = day.get("condition", "Clear")
                    condition_icon = {
                        "Clear": "☀️", "Clouds": "☁️", "Rain": "🌧️",
                        "Drizzle": "🌦️", "Thunderstorm": "⛈️", "Mist": "🌫️",
                    }.get(condition, "🌤️")

                    with st.expander(
                        f"{condition_icon} **{day['date']}** — "
                        f"{day['temp_avg']}°C | 💧 {day['humidity_avg']}% | "
                        f"🌧️ {day['rainfall_mm']}mm"
                    ):
                        dc1, dc2, dc3, dc4, dc5 = st.columns(5)
                        dc1.metric("🌡️ Avg", f"{day['temp_avg']}°C")
                        dc2.metric("📉 Min", f"{day['temp_min']}°C")
                        dc3.metric("📈 Max", f"{day['temp_max']}°C")
                        dc4.metric("💧 Humidity", f"{day['humidity_avg']}%")
                        dc5.metric("💨 Wind", f"{day['wind_speed_avg']} m/s")
                        st.caption(f"Condition: {day.get('description', 'N/A')}")

                with st.expander("🔧 Raw API Response"):
                    st.json(data)
            elif isinstance(data, dict) and "detail" in data:
                st.error(f"Error: {data['detail']}")


# ── Page 8: Logistics ────────────────────────────────────
elif page == "🚚 Logistics":
    st.header("🚚 Transport & Logistics Planner")
    st.markdown(
        "Get AI-powered vehicle recommendations and logistics provider matching.  \n"
        "Factors in distance, quantity, crop perishability, and urgency."
    )

    URGENCY_LEVELS = ["low", "medium", "high"]

    st.subheader("📦 Shipment Details")
    col1, col2 = st.columns(2)
    with col1:
        log_crop = st.selectbox("Crop", CROPS, index=0, key="log_crop")
        log_quantity = st.number_input("Quantity (kg)", min_value=1, value=500, step=50, key="log_qty")
        log_urgency = st.selectbox("Urgency", URGENCY_LEVELS, index=1, key="log_urgency")
    with col2:
        log_source = st.text_input("Source Location", value="Pune, Maharashtra", key="log_src")
        log_dest = st.text_input("Destination", value="Mumbai, Maharashtra", key="log_dest")
        log_distance = st.number_input("Distance (km)", min_value=1.0, value=150.0, step=10.0, key="log_dist")

    if st.button("🚚 Get Logistics Recommendation", type="primary", width="stretch"):
        with st.spinner("Computing optimal transport..."):
            data = api_get("/logistics/complete", params={
                "seller_location": log_source,
                "buyer_location": log_dest,
                "distance_km": log_distance,
                "quantity_kg": log_quantity,
                "crop_name": log_crop,
                "urgency": log_urgency,
            })

        if data and data.get("success"):
            st.divider()

            # ── Vehicle recommendation ──
            vr = data.get("vehicle_recommendation", {})
            primary = vr.get("primary_recommendation", {})

            st.subheader(f"🚛 Recommended: {primary.get('vehicle_name', 'N/A')}")

            vc1, vc2, vc3, vc4 = st.columns(4)
            vc1.metric("💰 Transport Cost", f"₹{primary.get('estimated_cost', 0):,.0f}")
            vc2.metric("⏱️ Travel Time", f"{primary.get('estimated_time_hours', 0):.1f} hrs")
            vc3.metric("📦 Capacity Used", f"{primary.get('capacity_utilization', 0):.0f}%")
            vc4.metric("🎯 Match Score", f"{primary.get('score', 0):.0f}/100")

            # Reasons
            reasons = primary.get("reasons", [])
            if reasons:
                for reason in reasons:
                    st.caption(f"✅ {reason}")

            # ── Alternatives ──
            alternatives = vr.get("alternatives", [])
            if alternatives:
                with st.expander("🔄 Alternative Vehicles"):
                    for alt in alternatives:
                        ac1, ac2, ac3 = st.columns(3)
                        ac1.markdown(f"**{alt['vehicle_name']}**")
                        ac2.metric("Cost", f"₹{alt['estimated_cost']:,.0f}")
                        ac3.metric("Time", f"{alt['estimated_time_hours']:.1f} hrs")
                        st.divider()

            # ── Route & delivery info ──
            route = data.get("route_info", {})
            if route:
                st.divider()
                st.subheader("📍 Route & Delivery")
                rc1, rc2, rc3 = st.columns(3)
                rc1.metric("📍 Route", f"{route.get('source', '')} → {route.get('destination', '')}")
                rc2.metric("📏 Distance", f"{route.get('distance_km', 0)} km")
                rc3.metric("📅 Est. Delivery", route.get("estimated_delivery", "N/A"))

            # ── Cost breakdown ──
            cost = data.get("cost_breakdown", {})
            if cost:
                with st.expander("💰 Cost Breakdown", expanded=True):
                    cc1, cc2, cc3, cc4 = st.columns(4)
                    cc1.metric("Transport", f"₹{cost.get('transport_cost', 0):,.0f}")
                    cc2.metric("Loading", f"₹{cost.get('loading_charges', 0):,.0f}")
                    cc3.metric("Tolls", f"₹{cost.get('toll_estimated', 0):,.0f}")
                    cc4.metric("**Total**", f"₹{cost.get('total_estimated', 0):,.0f}")

            # ── Logistics providers ──
            providers = data.get("logistics_providers", [])
            if providers:
                st.divider()
                st.subheader("🏢 Logistics Providers")
                for p in providers:
                    with st.expander(f"⭐ {p['rating']}/5 — **{p['name']}** ({p['type']})"):
                        st.markdown(f"📞 **Phone:** {p.get('phone', 'N/A')}")
                        st.markdown(f"📍 **Coverage:** {', '.join(p.get('coverage', []))}")
                        features = p.get("features", [])
                        if features:
                            st.markdown("**Features:** " + " · ".join(features))

            # TTS
            speech = (
                f"Recommended vehicle: {primary.get('vehicle_name', '')}. "
                f"Estimated cost: {primary.get('estimated_cost', 0)} rupees. "
                f"Travel time: {primary.get('estimated_time_hours', 0)} hours."
            )
            speak_text(speech, language="en", key="logistics_rec")

            with st.expander("🔧 Raw API Response"):
                st.json(data)
        elif data:
            st.error(f"Error: {data.get('error', 'Unknown error')}")


# ── Page 9: AI Chatbot ───────────────────────────────────
elif page == "🤖 AI Chatbot":
    st.header("🤖 AI Agricultural Assistant")
    st.markdown(
        "Chat with our AI assistant powered by **Amazon Bedrock Nova Lite**.  \n"
        "Ask about farming, pricing, storage, or market tips in English or Hindi.  \n"
        "🎙️ **Voice input supported** — record your question using the microphone!"
    )

    lang = st.radio("Language", ["en", "hi"], format_func=lambda x: "English" if x == "en" else "हिंदी", horizontal=True)

    # Chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display chat history
    for idx, msg in enumerate(st.session_state.messages):
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg.get("transcript"):
                st.caption(f"🎙️ Transcribed: \"{msg['transcript']}\"")
            if msg["role"] == "assistant":
                speak_text(msg["content"], language=lang, key=f"hist_{idx}")
            if msg.get("sources"):
                st.caption(f"Sources: {', '.join(msg['sources'])}")
            if msg.get("actions"):
                for action in msg["actions"]:
                    if isinstance(action, dict):
                        label = action.get("label", action.get("text", str(action)))
                        st.button(label, key=f"action_{hash(label)}_{id(action)}", disabled=True)

    # ── Voice Input ──
    st.divider()
    voice_col, text_col = st.columns([1, 3])
    with voice_col:
        audio_data = st.audio_input("🎙️ Record voice", key="voice_input")

    # Process voice only once — guard with session state
    if audio_data is not None:
        audio_id = hash(audio_data.getvalue())
        if st.session_state.get("_last_voice_id") != audio_id:
            st.session_state["_last_voice_id"] = audio_id
            with st.chat_message("user"):
                st.audio(audio_data, format="audio/webm")
                st.caption("🎙️ Processing voice message...")

            with st.chat_message("assistant"):
                with st.spinner("Transcribing & thinking..."):
                    r = _request_with_retry(
                        "POST",
                        f"{API}/chatbot/voice",
                        files={"audio": ("recording.webm", audio_data.getvalue(), "audio/webm")},
                        data={"language": lang},
                    )
                    data = r.json() if r else None

                if data:
                    transcript = data.get("transcript", "")
                    confidence = data.get("transcript_confidence", 0)
                    reply = data.get("reply", "Sorry, I couldn't process that.")
                    sources = data.get("sources", [])
                    actions = data.get("suggested_actions", [])

                    if transcript:
                        st.info(f"🎙️ **You said:** \"{transcript}\"  \n_(confidence: {confidence:.0%})_")
                    st.markdown(reply)
                    speak_text(reply, language=lang, key=f"voice_reply_{audio_id}")
                    if sources:
                        st.caption(f"Sources: {', '.join(sources)}")
                    for action in actions:
                        if isinstance(action, dict):
                            st.button(
                                action.get("label", action.get("text", str(action))),
                                key=f"va_{audio_id}_{hash(str(action))}",
                                disabled=True,
                            )

                    # Save to chat history
                    st.session_state.messages.append({
                        "role": "user",
                        "content": f"🎙️ _{transcript}_" if transcript else "🎙️ (voice message)",
                        "transcript": transcript,
                    })
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": reply,
                        "sources": sources,
                        "actions": actions,
                    })
                else:
                    st.error("Failed to process voice message.")

    # Chat input (text)
    if prompt := st.chat_input("Ask a question about farming, pricing, storage..."):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Get AI response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                data = api_post("/chatbot/message", json_body={
                    "message": prompt,
                    "language": lang,
                })

            if data:
                reply = data.get("reply", "Sorry, I couldn't process that.")
                sources = data.get("sources", [])
                actions = data.get("suggested_actions", [])

                st.markdown(reply)
                speak_text(reply, language=lang, key=f"chat_reply_{time.time()}")
                if sources:
                    st.caption(f"Sources: {', '.join(sources)}")
                for action in actions:
                    if isinstance(action, dict):
                        st.button(
                            action.get("label", action.get("text", str(action))),
                            key=f"a_{time.time()}_{hash(str(action))}",
                            disabled=True,
                        )

                st.session_state.messages.append({
                    "role": "assistant",
                    "content": reply,
                    "sources": sources,
                    "actions": actions,
                })
            else:
                st.error("Failed to get response from chatbot.")

    # Suggested prompts
    if not st.session_state.messages:
        st.divider()
        st.markdown("**💡 Try asking:**")
        suggestions = [
            "What is the best time to sell tomatoes?",
            "How should I store onions to reduce spoilage?",
            "टमाटर की कीमत कब बढ़ेगी?",
            "What are the current mandi prices for potato?",
            "How to detect if mangoes are ripe?",
        ]
        cols = st.columns(len(suggestions))
        for i, s in enumerate(suggestions):
            with cols[i]:
                if st.button(s, key=f"suggest_{i}", width="stretch"):
                    st.session_state.messages.append({"role": "user", "content": s})
                    # Fetch AI response immediately
                    data = api_post("/chatbot/message", json_body={
                        "message": s,
                        "language": lang,
                    })
                    if data:
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": data.get("reply", "Sorry, I couldn't process that."),
                            "sources": data.get("sources", []),
                            "actions": data.get("suggested_actions", []),
                        })
                    st.rerun()


# ── Footer ───────────────────────────────────────────────
st.divider()
st.caption(
    "SwadeshAI — AI for Bharat Hackathon | "
    f"Backend: {api_url} | "
    f"{datetime.now().strftime('%Y-%m-%d %H:%M')}"
)

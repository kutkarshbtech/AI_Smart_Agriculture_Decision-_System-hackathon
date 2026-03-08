"""
Streamlit Authentication Module with Mobile Number + OTP Login.
Supports Buyer, Seller, and Logistic Provider registration/login.
"""
import streamlit as st
import sys
import os
import re

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.services.auth_service import AuthService


class StreamlitAuth:
    """Streamlit authentication handler"""
    
    def __init__(self):
        self.auth_service = AuthService(storage_path="data/auth")
        
        # Initialize session state
        if 'authenticated' not in st.session_state:
            st.session_state.authenticated = False
        if 'user_data' not in st.session_state:
            st.session_state.user_data = None
        if 'auth_token' not in st.session_state:
            st.session_state.auth_token = None
        if 'otp_sent' not in st.session_state:
            st.session_state.otp_sent = False
        if 'pending_mobile' not in st.session_state:
            st.session_state.pending_mobile = None
        if 'pending_user_type' not in st.session_state:
            st.session_state.pending_user_type = None
        if 'demo_otp' not in st.session_state:
            st.session_state.demo_otp = None
    
    def is_authenticated(self) -> bool:
        """Check if user is authenticated"""
        return st.session_state.authenticated
    
    def get_user_data(self) -> dict:
        """Get authenticated user data"""
        return st.session_state.user_data
    
    def validate_mobile(self, mobile: str) -> tuple[bool, str]:
        """Validate mobile number format"""
        cleaned = re.sub(r'[^0-9+]', '', mobile)
        if not re.match(r'^\+?[1-9]\d{9,14}$', cleaned):
            return False, "Invalid mobile number format. Use +919876543210"
        return True, cleaned
    
    def registration_page(self):
        """Display registration form"""
        st.title("🔐 SwadeshAI Registration")
        st.markdown("Register as Buyer, Seller, or Logistic Provider")
        
        with st.form("registration_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                user_type = st.selectbox(
                    "I am a *",
                    ["", "buyer", "seller", "logistic"],
                    format_func=lambda x: {
                        "": "-- Select Type --",
                        "buyer": "🛒 Buyer (Wholesaler/Retailer)",
                        "seller": "🌾 Seller (Farmer/Supplier)",
                        "logistic": "🚚 Logistic Provider"
                    }[x]
                )
                
                name = st.text_input("Full Name *", placeholder="Rajesh Kumar")
                mobile = st.text_input(
                    "Mobile Number *", 
                    placeholder="+919876543210",
                    help="Include country code (e.g., +91 for India)"
                )
            
            with col2:
                business_name = st.text_input(
                    "Business Name", 
                    placeholder="Optional for buyers/logistics"
                )
                
                city = st.text_input("City", placeholder="Delhi")
                state = st.text_input("State", placeholder="Delhi")
                pincode = st.text_input("Pincode", placeholder="110001", max_chars=6)
            
            # Additional fields for logistics
            if user_type == "logistic":
                st.markdown("---")
                st.subheader("Logistics Details")
                
                vehicle_options = [
                    "Two Wheeler", "Auto Rickshaw", "Pickup Van", 
                    "Mini Truck", "6-Wheeler", "10-Wheeler", "Refrigerated Truck"
                ]
                vehicle_types = st.multiselect(
                    "Vehicle Types Available",
                    vehicle_options
                )
                
                state_options = [
                    "Delhi", "Uttar Pradesh", "Punjab", "Haryana", "Rajasthan",
                    "Maharashtra", "Gujarat", "Karnataka", "Tamil Nadu", "West Bengal"
                ]
                operating_states = st.multiselect(
                    "Operating States",
                    state_options
                )
            else:
                vehicle_types = None
                operating_states = None
            
            submitted = st.form_submit_button("📝 Register", use_container_width=True)
            
            if submitted:
                # Validate required fields
                if not user_type or user_type == "":
                    st.error("❌ Please select user type")
                    return
                
                if not name or len(name) < 2:
                    st.error("❌ Please enter your full name")
                    return
                
                if not mobile:
                    st.error("❌ Please enter mobile number")
                    return
                
                # Validate mobile number
                valid, cleaned_mobile = self.validate_mobile(mobile)
                if not valid:
                    st.error(f"❌ {cleaned_mobile}")
                    return
                
                # Validate pincode if provided
                if pincode and not re.match(r'^\d{6}$', pincode):
                    st.error("❌ Invalid pincode format (must be 6 digits)")
                    return
                
                # Prepare additional fields
                additional_fields = {}
                if business_name:
                    additional_fields['business_name'] = business_name
                if city:
                    additional_fields['city'] = city
                if state:
                    additional_fields['state'] = state
                if pincode:
                    additional_fields['pincode'] = pincode
                if vehicle_types:
                    additional_fields['vehicle_types'] = vehicle_types
                if operating_states:
                    additional_fields['operating_states'] = operating_states
                
                # Register user
                success, message, user_data = self.auth_service.register_user(
                    mobile_number=cleaned_mobile,
                    user_type=user_type,
                    name=name,
                    **additional_fields
                )
                
                if success:
                    st.success(f"✅ {message}")
                    st.info("👉 Please proceed to login with your mobile number")
                    st.balloons()
                else:
                    st.error(f"❌ {message}")
    
    def login_page(self):
        """Display login form with OTP"""
        st.title("🔑 SwadeshAI Login")
        st.markdown("Login with Mobile Number + OTP")
        
        # Step 1: Request OTP
        if not st.session_state.otp_sent:
            with st.form("login_form"):
                user_type = st.selectbox(
                    "Login as",
                    ["", "buyer", "seller", "logistic"],
                    format_func=lambda x: {
                        "": "-- Select Type --",
                        "buyer": "🛒 Buyer",
                        "seller": "🌾 Seller",
                        "logistic": "🚚 Logistic Provider"
                    }[x]
                )
                
                mobile = st.text_input(
                    "Mobile Number", 
                    placeholder="+919876543210",
                    help="Enter registered mobile number"
                )
                
                submitted = st.form_submit_button("📱 Send OTP", use_container_width=True)
                
                if submitted:
                    if not user_type or user_type == "":
                        st.error("❌ Please select user type")
                        return
                    
                    if not mobile:
                        st.error("❌ Please enter mobile number")
                        return
                    
                    valid, cleaned_mobile = self.validate_mobile(mobile)
                    if not valid:
                        st.error(f"❌ {cleaned_mobile}")
                        return
                    
                    # Request OTP
                    success, message, otp = self.auth_service.send_otp(
                        mobile_number=cleaned_mobile,
                        user_type=user_type
                    )
                    
                    if success:
                        st.session_state.otp_sent = True
                        st.session_state.pending_mobile = cleaned_mobile
                        st.session_state.pending_user_type = user_type
                        st.session_state.demo_otp = otp  # For demo purposes
                        st.rerun()
                    else:
                        st.error(f"❌ {message}")
        
        # Step 2: Verify OTP
        else:
            st.info(f"📱 OTP sent to {st.session_state.pending_mobile}")
            
            # Show OTP in demo mode (remove in production!)
            if st.session_state.demo_otp:
                st.success(f"🔑 Demo OTP: **{st.session_state.demo_otp}**")
                st.caption("(OTP shown only for demo purposes)")
            
            with st.form("otp_form"):
                otp = st.text_input(
                    "Enter 6-digit OTP", 
                    placeholder="123456",
                    max_chars=6
                )
                
                col1, col2 = st.columns(2)
                
                with col1:
                    verify_btn = st.form_submit_button("✅ Verify & Login", use_container_width=True)
                with col2:
                    cancel_btn = st.form_submit_button("❌ Cancel", use_container_width=True)
                
                if verify_btn:
                    if not otp or len(otp) != 6:
                        st.error("❌ Please enter 6-digit OTP")
                        return
                    
                    # Verify OTP
                    success, message, token = self.auth_service.verify_otp(
                        mobile_number=st.session_state.pending_mobile,
                        user_type=st.session_state.pending_user_type,
                        otp=otp
                    )
                    
                    if success:
                        # Get user data
                        user_data = self.auth_service.get_user(
                            st.session_state.pending_mobile,
                            st.session_state.pending_user_type
                        )
                        
                        # Set session state
                        st.session_state.authenticated = True
                        st.session_state.user_data = user_data
                        st.session_state.auth_token = token
                        st.session_state.otp_sent = False
                        st.session_state.demo_otp = None
                        
                        st.success(f"✅ Welcome {user_data['name']}!")
                        st.balloons()
                        st.rerun()
                    else:
                        st.error(f"❌ {message}")
                
                if cancel_btn:
                    st.session_state.otp_sent = False
                    st.session_state.pending_mobile = None
                    st.session_state.pending_user_type = None
                    st.session_state.demo_otp = None
                    st.rerun()
    
    def logout(self):
        """Logout user"""
        if st.session_state.auth_token:
            self.auth_service.logout(st.session_state.auth_token)
        
        st.session_state.authenticated = False
        st.session_state.user_data = None
        st.session_state.auth_token = None
        st.session_state.otp_sent = False
        st.session_state.pending_mobile = None
        st.session_state.pending_user_type = None
        st.session_state.demo_otp = None
    
    def render_user_info(self):
        """Render user info in sidebar"""
        if self.is_authenticated():
            user = self.get_user_data()
            
            with st.sidebar:
                st.markdown("---")
                
                # User type icon
                icon = {
                    "buyer": "🛒",
                    "seller": "🌾",
                    "logistic": "🚚"
                }.get(user['user_type'], "👤")
                
                st.markdown(f"### {icon} {user['name']}")
                st.caption(f"{user['user_type'].title()} • {user['mobile_number']}")
                
                if user.get('business_name'):
                    st.caption(f"🏢 {user['business_name']}")
                
                if user.get('city') and user.get('state'):
                    st.caption(f"📍 {user['city']}, {user['state']}")
                
                if st.button("🚪 Logout", use_container_width=True):
                    self.logout()
                    st.rerun()
                
                st.markdown("---")


# Standalone auth app (can be used separately)
def main():
    """Standalone authentication app"""
    st.set_page_config(
        page_title="SwadeshAI Auth",
        page_icon="🔐",
        layout="centered"
    )
    
    auth = StreamlitAuth()
    
    if auth.is_authenticated():
        st.success("✅ You are logged in!")
        auth.render_user_info()
        
        user = auth.get_user_data()
        st.json(user)
        
    else:
        tab1, tab2 = st.tabs(["🔑 Login", "📝 Register"])
        
        with tab1:
            auth.login_page()
        
        with tab2:
            auth.registration_page()


if __name__ == "__main__":
    main()

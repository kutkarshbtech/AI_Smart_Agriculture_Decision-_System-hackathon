package com.swadesh.ai.data.model

import com.google.gson.annotations.SerializedName

/**
 * Authentication data models matching backend API
 * Supports three user types: Buyer, Seller, Logistic
 */

enum class UserType {
    @SerializedName("buyer")
    BUYER,
    
    @SerializedName("seller")
    SELLER,
    
    @SerializedName("logistic")
    LOGISTIC;
    
    fun displayName(): String = when (this) {
        BUYER -> "Buyer"
        SELLER -> "Seller"
        LOGISTIC -> "Logistic Provider"
    }
}

// ─── Request Models ───────────────────────────────────────

data class RegisterRequest(
    @SerializedName("mobile_number")
    val mobileNumber: String,
    
    @SerializedName("user_type")
    val userType: String,
    
    @SerializedName("name")
    val name: String,
    
    // Optional fields
    @SerializedName("business_name")
    val businessName: String? = null,
    
    @SerializedName("vehicle_types")
    val vehicleTypes: List<String>? = null,
    
    @SerializedName("operating_states")
    val operatingStates: List<String>? = null,
    
    @SerializedName("city")
    val city: String? = null,
    
    @SerializedName("state")
    val state: String? = null,
    
    @SerializedName("pincode")
    val pincode: String? = null,
    
    @SerializedName("village")
    val village: String? = null,
    
    @SerializedName("district")
    val district: String? = null
)

data class LoginRequest(
    @SerializedName("mobile_number")
    val mobileNumber: String,
    
    @SerializedName("user_type")
    val userType: String
)

data class VerifyOTPRequest(
    @SerializedName("mobile_number")
    val mobileNumber: String,
    
    @SerializedName("user_type")
    val userType: String,
    
    @SerializedName("otp")
    val otp: String
)

// ─── Response Models ───────────────────────────────────────

data class RegisterResponse(
    @SerializedName("success")
    val success: Boolean,
    
    @SerializedName("message")
    val message: String,
    
    @SerializedName("user")
    val user: UserBasic?
)

data class UserBasic(
    @SerializedName("id")
    val id: Int,
    
    @SerializedName("mobile_number")
    val mobileNumber: String,
    
    @SerializedName("user_type")
    val userType: String,
    
    @SerializedName("name")
    val name: String
)

data class OTPResponse(
    @SerializedName("success")
    val success: Boolean,
    
    @SerializedName("message")
    val message: String,
    
    @SerializedName("otp_sent")
    val otpSent: Boolean,
    
    @SerializedName("demo_otp")
    val demoOtp: String?  // Only for demo mode
)

data class AuthToken(
    @SerializedName("access_token")
    val accessToken: String,
    
    @SerializedName("token_type")
    val tokenType: String = "bearer",
    
    @SerializedName("user_id")
    val userId: Int,
    
    @SerializedName("user_type")
    val userType: String,
    
    @SerializedName("name")
    val name: String,
    
    @SerializedName("mobile_number")
    val mobileNumber: String,
    
    @SerializedName("expires_in")
    val expiresIn: Int = 86400  // 24 hours
)

data class UserProfile(
    @SerializedName("id")
    val id: Int,
    
    @SerializedName("mobile_number")
    val mobileNumber: String,
    
    @SerializedName("user_type")
    val userType: String,
    
    @SerializedName("name")
    val name: String,
    
    @SerializedName("business_name")
    val businessName: String? = null,
    
    @SerializedName("vehicle_types")
    val vehicleTypes: List<String>? = null,
    
    @SerializedName("operating_states")
    val operatingStates: List<String>? = null,
    
    @SerializedName("city")
    val city: String? = null,
    
    @SerializedName("state")
    val state: String? = null,
    
    @SerializedName("pincode")
    val pincode: String? = null,
    
    @SerializedName("village")
    val village: String? = null,
    
    @SerializedName("district")
    val district: String? = null,
    
    @SerializedName("is_active")
    val isActive: Boolean,
    
    @SerializedName("is_verified")
    val isVerified: Boolean,
    
    @SerializedName("created_at")
    val createdAt: String,
    
    @SerializedName("last_login")
    val lastLogin: String? = null
)

data class ApiResponse(
    @SerializedName("success")
    val success: Boolean,
    
    @SerializedName("message")
    val message: String
)

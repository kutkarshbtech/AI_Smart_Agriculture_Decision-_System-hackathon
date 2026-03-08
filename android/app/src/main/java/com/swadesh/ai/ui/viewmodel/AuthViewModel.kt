package com.swadesh.ai.ui.viewmodel

import android.content.Context
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.swadesh.ai.data.api.RetrofitClient
import com.swadesh.ai.data.model.*
import com.swadesh.ai.data.repository.AuthRepository
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.launch

/**
 * ViewModel for authentication (Login, Register, OTP)
 * Manages auth state for three user types: Buyer, Seller, Logistic
 */
class AuthViewModel(context: Context) : ViewModel() {
    
    private val authRepository = AuthRepository(context)
    private val authApi = RetrofitClient.authApi
    
    // Auth state
    private val _authState = MutableStateFlow<AuthState>(AuthState.Initial)
    val authState: StateFlow<AuthState> = _authState.asStateFlow()
    
    // User data
    private val _userProfile = MutableStateFlow<UserProfile?>(null)
    val userProfile: StateFlow<UserProfile?> = _userProfile.asStateFlow()
    
    // Is logged in
    val isLoggedIn = authRepository.isLoggedIn.stateIn(
        scope = viewModelScope,
        started = SharingStarted.WhileSubscribed(5000),
        initialValue = false
    )
    
    // User type
    val userType = authRepository.userType.stateIn(
        scope = viewModelScope,
        started = SharingStarted.WhileSubscribed(5000),
        initialValue = null
    )
    
    // User name
    val userName = authRepository.userName.stateIn(
        scope = viewModelScope,
        started = SharingStarted.WhileSubscribed(5000),
        initialValue = null
    )
    
    // ─── Registration ───────────────────────────────────────
    
    fun register(
        mobileNumber: String,
        userType: UserType,
        name: String,
        businessName: String? = null,
        vehicleTypes: List<String>? = null,
        operatingStates: List<String>? = null,
        city: String? = null,
        state: String? = null,
        pincode: String? = null,
        village: String? = null,
        district: String? = null
    ) {
        viewModelScope.launch {
            _authState.value = AuthState.Loading
            
            try {
                val request = RegisterRequest(
                    mobileNumber = mobileNumber,
                    userType = userType.name.lowercase(),
                    name = name,
                    businessName = businessName,
                    vehicleTypes = vehicleTypes,
                    operatingStates = operatingStates,
                    city = city,
                    state = state,
                    pincode = pincode,
                    village = village,
                    district = district
                )
                
                val response = authApi.register(request)
                
                if (response.isSuccessful && response.body()?.success == true) {
                    _authState.value = AuthState.RegistrationSuccess(response.body()!!.message)
                } else {
                    val errorMsg = response.body()?.message ?: response.errorBody()?.string() ?: "Registration failed"
                    _authState.value = AuthState.Error(errorMsg)
                }
            } catch (e: Exception) {
                _authState.value = AuthState.Error(e.message ?: "Network error")
            }
        }
    }
    
    // ─── Login (Request OTP) ───────────────────────────────
    
    fun requestOTP(mobileNumber: String, userType: UserType) {
        viewModelScope.launch {
            _authState.value = AuthState.Loading
            
            try {
                val request = LoginRequest(
                    mobileNumber = mobileNumber,
                    userType = userType.name.lowercase()
                )
                
                val response = authApi.requestOTP(request)
                
                if (response.isSuccessful && response.body()?.success == true) {
                    val otpResponse = response.body()!!
                    _authState.value = AuthState.OTPSent(
                        message = otpResponse.message,
                        demoOtp = otpResponse.demoOtp  // For testing only
                    )
                } else {
                    val errorMsg = response.body()?.message ?: "Failed to send OTP"
                    _authState.value = AuthState.Error(errorMsg)
                }
            } catch (e: Exception) {
                _authState.value = AuthState.Error(e.message ?: "Network error")
            }
        }
    }
    
    // ─── Verify OTP ───────────────────────────────────────
    
    fun verifyOTP(mobileNumber: String, userType: UserType, otp: String) {
        viewModelScope.launch {
            _authState.value = AuthState.Loading
            
            try {
                val request = VerifyOTPRequest(
                    mobileNumber = mobileNumber,
                    userType = userType.name.lowercase(),
                    otp = otp
                )
                
                val response = authApi.verifyOTP(request)
                
                if (response.isSuccessful && response.body() != null) {
                    val authToken = response.body()!!
                    
                    // Save auth data
                    authRepository.saveAuthData(
                        token = authToken.accessToken,
                        userId = authToken.userId,
                        userType = authToken.userType,
                        name = authToken.name,
                        mobileNumber = authToken.mobileNumber
                    )
                    
                    _authState.value = AuthState.LoginSuccess(authToken)
                } else {
                    _authState.value = AuthState.Error("Invalid OTP")
                }
            } catch (e: Exception) {
                _authState.value = AuthState.Error(e.message ?: "Network error")
            }
        }
    }
    
    // ─── Get Profile ───────────────────────────────────────
    
    fun loadProfile() {
        viewModelScope.launch {
            try {
                val token = authRepository.getBearerToken()
                if (token != null) {
                    val response = authApi.getProfile(token)
                    if (response.isSuccessful && response.body() != null) {
                        _userProfile.value = response.body()
                    }
                }
            } catch (e: Exception) {
                // Handle error silently or log
            }
        }
    }
    
    // ─── Logout ───────────────────────────────────────────
    
    fun logout() {
        viewModelScope.launch {
            try {
                val token = authRepository.getBearerToken()
                if (token != null) {
                    authApi.logout(token)
                }
            } catch (e: Exception) {
                // Handle error
            } finally {
                authRepository.clearAuthData()
                _authState.value = AuthState.LoggedOut
                _userProfile.value = null
            }
        }
    }
    
    // Reset auth state
    fun resetAuthState() {
        _authState.value = AuthState.Initial
    }
}

// ─── Auth States ───────────────────────────────────────

sealed class AuthState {
    data object Initial : AuthState()
    data object Loading : AuthState()
    data class RegistrationSuccess(val message: String) : AuthState()
    data class OTPSent(val message: String, val demoOtp: String?) : AuthState()
    data class LoginSuccess(val authToken: AuthToken) : AuthState()
    data class Error(val message: String) : AuthState()
    data object LoggedOut : AuthState()
}

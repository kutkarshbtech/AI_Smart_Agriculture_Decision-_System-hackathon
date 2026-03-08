package com.swadesh.ai.data.api

import com.swadesh.ai.data.model.*
import retrofit2.Response
import retrofit2.http.*

/**
 * Authentication API service interface
 * Endpoints: /api/auth/*
 */
interface AuthApiService {
    
    @POST("api/auth/register")
    suspend fun register(
        @Body request: RegisterRequest
    ): Response<RegisterResponse>
    
    @POST("api/auth/login/request-otp")
    suspend fun requestOTP(
        @Body request: LoginRequest
    ): Response<OTPResponse>
    
    @POST("api/auth/login/verify-otp")
    suspend fun verifyOTP(
        @Body request: VerifyOTPRequest
    ): Response<AuthToken>
    
    @GET("api/auth/profile")
    suspend fun getProfile(
        @Header("Authorization") token: String
    ): Response<UserProfile>
    
    @POST("api/auth/logout")
    suspend fun logout(
        @Header("Authorization") token: String
    ): Response<ApiResponse>
}

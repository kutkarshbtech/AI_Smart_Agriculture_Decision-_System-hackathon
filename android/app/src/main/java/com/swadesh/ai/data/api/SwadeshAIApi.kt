package com.swadesh.ai.data.api

import com.swadesh.ai.data.models.*
import okhttp3.MultipartBody
import retrofit2.Response
import retrofit2.http.*

/**
 * SwadeshAI API service interface.
 * Connects Android app to FastAPI backend.
 */
interface SwadeshAIApi {

    // ─── Produce Management ────────────────────────────

    @GET("produce/crop-types")
    suspend fun getCropTypes(
        @Query("category") category: String? = null
    ): Response<List<CropType>>

    @POST("produce/batches")
    suspend fun createBatch(
        @Body request: CreateBatchRequest
    ): Response<ProduceBatch>

    @GET("produce/batches")
    suspend fun getBatches(
        @Query("farmer_id") farmerId: Int = 1,
        @Query("include_sold") includeSold: Boolean = false
    ): Response<List<ProduceBatch>>

    @GET("produce/batches/{batchId}")
    suspend fun getBatch(
        @Path("batchId") batchId: Int
    ): Response<ProduceBatch>

    @Multipart
    @POST("produce/batches/{batchId}/images")
    suspend fun uploadProduceImage(
        @Path("batchId") batchId: Int,
        @Part file: MultipartBody.Part
    ): Response<QualityAssessment>

    // ─── Spoilage Assessment ───────────────────────────

    @POST("spoilage/assess")
    suspend fun assessSpoilage(
        @Body request: SpoilageRequest
    ): Response<SpoilageAssessment>

    @GET("spoilage/batch/{batchId}")
    suspend fun getBatchSpoilage(
        @Path("batchId") batchId: Int
    ): Response<SpoilageAssessment>

    // ─── Pricing Intelligence ──────────────────────────

    @GET("pricing/market/{cropName}")
    suspend fun getMarketPrices(
        @Path("cropName") cropName: String,
        @Query("days") days: Int = 7
    ): Response<MarketPricesResponse>

    @GET("pricing/recommend/{batchId}")
    suspend fun getPriceRecommendation(
        @Path("batchId") batchId: Int
    ): Response<PriceRecommendation>

    // ─── Quality Assessment ────────────────────────────

    @Multipart
    @POST("quality/assess/{batchId}")
    suspend fun assessQuality(
        @Path("batchId") batchId: Int,
        @Part file: MultipartBody.Part
    ): Response<QualityAssessment>

    @Multipart
    @POST("quality/assess-standalone")
    suspend fun assessFreshnessStandalone(
        @Query("crop_name") cropName: String,
        @Part file: MultipartBody.Part
    ): Response<FreshnessAssessmentResponse>

    @GET("quality/model-status")
    suspend fun getModelStatus(): Response<ModelStatusResponse>

    @GET("quality/simulate/{cropName}")
    suspend fun simulateQuality(
        @Path("cropName") cropName: String
    ): Response<QualityAssessment>

    // ─── Buyer Matching ────────────────────────────────

    @POST("buyers/match")
    suspend fun findMatchingBuyers(
        @Body request: BuyerMatchRequest
    ): Response<BuyerMatchResponse>

    @GET("buyers/nearby")
    suspend fun findNearbyBuyers(
        @Query("crop_name") cropName: String,
        @Query("lat") lat: Float,
        @Query("lng") lng: Float,
        @Query("quantity_kg") quantityKg: Float = 100f,
        @Query("max_distance_km") maxDistanceKm: Float = 100f
    ): Response<BuyerMatchResponse>

    // ─── Dashboard ─────────────────────────────────────

    @GET("dashboard/summary/{farmerId}")
    suspend fun getDashboardSummary(
        @Path("farmerId") farmerId: Int = 1
    ): Response<DashboardSummary>

    // ─── Alerts ────────────────────────────────────────

    @GET("alerts/user/{userId}")
    suspend fun getUserAlerts(
        @Path("userId") userId: Int = 1,
        @Query("unread_only") unreadOnly: Boolean = false
    ): Response<AlertsResponse>

    @POST("alerts/{alertId}/read")
    suspend fun markAlertRead(
        @Path("alertId") alertId: Int
    ): Response<Map<String, String>>

    // ─── Chatbot ───────────────────────────────────────

    @POST("chatbot/message")
    suspend fun sendChatMessage(
        @Body request: ChatMessageRequest
    ): Response<ChatMessageResponse>

    @GET("chatbot/welcome")
    suspend fun getWelcomeMessage(
        @Query("language") language: String = "hi"
    ): Response<ChatMessageResponse>
}

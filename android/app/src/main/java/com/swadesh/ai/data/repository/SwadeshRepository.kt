package com.swadesh.ai.data.repository

import com.swadesh.ai.data.api.RetrofitClient
import com.swadesh.ai.data.models.*

/**
 * Main repository — single source of truth for all data operations.
 */
class SwadeshRepository {
    private val api = RetrofitClient.api

    // ─── Produce ───────────────────────────────────────

    suspend fun getCropTypes(category: String? = null): Result<List<CropType>> = apiCall {
        api.getCropTypes(category)
    }

    suspend fun createBatch(request: CreateBatchRequest): Result<ProduceBatch> = apiCall {
        api.createBatch(request)
    }

    suspend fun getBatches(farmerId: Int = 1): Result<List<ProduceBatch>> = apiCall {
        api.getBatches(farmerId)
    }

    suspend fun getBatch(batchId: Int): Result<ProduceBatch> = apiCall {
        api.getBatch(batchId)
    }

    // ─── Spoilage ──────────────────────────────────────

    suspend fun assessSpoilage(request: SpoilageRequest): Result<SpoilageAssessment> = apiCall {
        api.assessSpoilage(request)
    }

    suspend fun getBatchSpoilage(batchId: Int): Result<SpoilageAssessment> = apiCall {
        api.getBatchSpoilage(batchId)
    }

    // ─── Pricing ───────────────────────────────────────

    suspend fun getMarketPrices(cropName: String, days: Int = 7): Result<MarketPricesResponse> = apiCall {
        api.getMarketPrices(cropName, days)
    }

    suspend fun getPriceRecommendation(batchId: Int): Result<PriceRecommendation> = apiCall {
        api.getPriceRecommendation(batchId)
    }

    // ─── Quality ───────────────────────────────────────

    suspend fun simulateQuality(cropName: String): Result<QualityAssessment> = apiCall {
        api.simulateQuality(cropName)
    }

    // ─── Buyers ────────────────────────────────────────

    suspend fun findBuyers(request: BuyerMatchRequest): Result<BuyerMatchResponse> = apiCall {
        api.findMatchingBuyers(request)
    }

    suspend fun findNearbyBuyers(
        cropName: String, lat: Float, lng: Float,
        quantityKg: Float = 100f, maxDistanceKm: Float = 100f
    ): Result<BuyerMatchResponse> = apiCall {
        api.findNearbyBuyers(cropName, lat, lng, quantityKg, maxDistanceKm)
    }

    // ─── Dashboard ─────────────────────────────────────

    suspend fun getDashboardSummary(farmerId: Int = 1): Result<DashboardSummary> = apiCall {
        api.getDashboardSummary(farmerId)
    }

    // ─── Alerts ────────────────────────────────────────

    suspend fun getAlerts(userId: Int = 1, unreadOnly: Boolean = false): Result<AlertsResponse> = apiCall {
        api.getUserAlerts(userId, unreadOnly)
    }

    suspend fun markAlertRead(alertId: Int): Result<Map<String, String>> = apiCall {
        api.markAlertRead(alertId)
    }

    // ─── Chatbot ───────────────────────────────────────

    suspend fun sendChatMessage(request: ChatMessageRequest): Result<ChatMessageResponse> = apiCall {
        api.sendChatMessage(request)
    }

    suspend fun getWelcomeMessage(language: String = "hi"): Result<ChatMessageResponse> = apiCall {
        api.getWelcomeMessage(language)
    }

    // ─── Helper ────────────────────────────────────────

    private suspend fun <T> apiCall(call: suspend () -> retrofit2.Response<T>): Result<T> {
        return try {
            val response = call()
            if (response.isSuccessful) {
                response.body()?.let { Result.success(it) }
                    ?: Result.failure(Exception("Empty response body"))
            } else {
                Result.failure(Exception("API error: ${response.code()} ${response.message()}"))
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }
}

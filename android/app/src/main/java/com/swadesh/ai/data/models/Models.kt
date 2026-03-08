package com.swadesh.ai.data.models

import com.google.gson.annotations.SerializedName

// ─── Crop Types ────────────────────────────────────────

data class CropType(
    val id: Int,
    @SerializedName("name_en") val nameEn: String,
    @SerializedName("name_hi") val nameHi: String?,
    val category: String,
    @SerializedName("avg_shelf_life_days") val avgShelfLifeDays: Int?,
    @SerializedName("optimal_temp_min") val optimalTempMin: Float?,
    @SerializedName("optimal_temp_max") val optimalTempMax: Float?,
    @SerializedName("image_url") val imageUrl: String?
)

// ─── Produce Batch ─────────────────────────────────────

data class ProduceBatch(
    val id: Int,
    @SerializedName("farmer_id") val farmerId: Int,
    @SerializedName("crop_type_id") val cropTypeId: Int,
    @SerializedName("crop_name") val cropName: String?,
    @SerializedName("quantity_kg") val quantityKg: Float,
    @SerializedName("harvest_date") val harvestDate: String,
    @SerializedName("storage_type") val storageType: String,
    @SerializedName("storage_temp") val storageTemp: Float?,
    @SerializedName("storage_humidity") val storageHumidity: Float?,
    @SerializedName("quality_grade") val qualityGrade: String?,
    @SerializedName("quality_score") val qualityScore: Float?,
    @SerializedName("spoilage_risk") val spoilageRisk: String?,
    @SerializedName("spoilage_probability") val spoilageProbability: Float?,
    @SerializedName("estimated_shelf_life_days") val estimatedShelfLifeDays: Int?,
    @SerializedName("image_urls") val imageUrls: List<String>,
    @SerializedName("is_sold") val isSold: Boolean,
    @SerializedName("created_at") val createdAt: String
)

data class CreateBatchRequest(
    @SerializedName("crop_type_id") val cropTypeId: Int,
    @SerializedName("quantity_kg") val quantityKg: Float,
    @SerializedName("harvest_date") val harvestDate: String,
    @SerializedName("storage_type") val storageType: String = "ambient",
    @SerializedName("storage_temp") val storageTemp: Float? = null,
    @SerializedName("storage_humidity") val storageHumidity: Float? = null,
    @SerializedName("location_lat") val locationLat: Float? = null,
    @SerializedName("location_lng") val locationLng: Float? = null,
    val notes: String? = null
)

// ─── Spoilage ──────────────────────────────────────────

data class SpoilageAssessment(
    @SerializedName("batch_id") val batchId: Int,
    @SerializedName("crop_name") val cropName: String,
    @SerializedName("spoilage_risk") val spoilageRisk: String,
    @SerializedName("spoilage_probability") val spoilageProbability: Float,
    @SerializedName("estimated_shelf_life_days") val estimatedShelfLifeDays: Int,
    @SerializedName("remaining_shelf_life_days") val remainingShelfLifeDays: Int,
    @SerializedName("risk_factors") val riskFactors: List<RiskFactor>,
    val recommendations: List<String>,
    val explanation: String
)

data class RiskFactor(
    val factor: String,
    val impact: String,
    val severity: String,
    val current: Any? = null,
    @SerializedName("optimal_range") val optimalRange: String? = null
)

data class SpoilageRequest(
    @SerializedName("batch_id") val batchId: Int,
    @SerializedName("current_temp") val currentTemp: Float? = null,
    @SerializedName("current_humidity") val currentHumidity: Float? = null,
    @SerializedName("transport_hours") val transportHours: Float? = null,
    @SerializedName("has_cold_storage") val hasColdStorage: Boolean = false
)

// ─── Pricing ───────────────────────────────────────────

data class PriceRecommendation(
    @SerializedName("batch_id") val batchId: Int,
    @SerializedName("crop_name") val cropName: String,
    @SerializedName("quantity_kg") val quantityKg: Float,
    @SerializedName("recommended_min_price") val recommendedMinPrice: Float,
    @SerializedName("recommended_max_price") val recommendedMaxPrice: Float,
    @SerializedName("predicted_market_price") val predictedMarketPrice: Float?,
    @SerializedName("confidence_score") val confidenceScore: Float,
    val factors: List<PriceFactor>,
    @SerializedName("recommendation_text") val recommendationText: String,
    val action: String,
    val trend: String?,
    @SerializedName("avg_7d") val avg7d: Float?
)

data class PriceFactor(
    val name: String,
    val value: String,
    val impact: String
)

data class MarketPriceData(
    @SerializedName("crop_name") val cropName: String,
    @SerializedName("mandi_name") val mandiName: String,
    @SerializedName("min_price") val minPrice: Float,
    @SerializedName("max_price") val maxPrice: Float,
    @SerializedName("modal_price") val modalPrice: Float,
    val date: String,
    val source: String
)

data class MarketPricesResponse(
    @SerializedName("crop_name") val cropName: String,
    val prices: List<MarketPriceData>,
    val trend: String,
    @SerializedName("avg_price_7d") val avgPrice7d: Float?
)

// ─── Quality ───────────────────────────────────────────

data class QualityAssessment(
    @SerializedName("crop_name") val cropName: String,
    @SerializedName("overall_grade") val overallGrade: String,
    @SerializedName("quality_score") val qualityScore: Float,
    @SerializedName("freshness_score") val freshnessScore: Float,
    @SerializedName("damage_score") val damageScore: Float,
    @SerializedName("ripeness_level") val ripenessLevel: String,
    @SerializedName("defects_detected") val defectsDetected: List<String>,
    @SerializedName("analysis_summary") val analysisSummary: String
)

// ─── Buyer Matching ────────────────────────────────────

data class BuyerMatch(
    val id: Int,
    @SerializedName("shop_name") val shopName: String?,
    @SerializedName("contact_name") val contactName: String,
    @SerializedName("contact_phone") val contactPhone: String,
    val district: String?,
    val state: String?,
    @SerializedName("distance_km") val distanceKm: Float?,
    @SerializedName("is_verified") val isVerified: Boolean
)

data class BuyerMatchRequest(
    @SerializedName("batch_id") val batchId: Int,
    @SerializedName("farmer_lat") val farmerLat: Float,
    @SerializedName("farmer_lng") val farmerLng: Float,
    @SerializedName("max_distance_km") val maxDistanceKm: Float = 50f
)

data class BuyerMatchResponse(
    @SerializedName("batch_id") val batchId: Int,
    @SerializedName("crop_name") val cropName: String,
    @SerializedName("matched_buyers") val matchedBuyers: List<BuyerMatch>,
    @SerializedName("total_matches") val totalMatches: Int
)

// ─── Dashboard ─────────────────────────────────────────

data class DashboardSummary(
    @SerializedName("total_batches") val totalBatches: Int,
    @SerializedName("active_batches") val activeBatches: Int,
    @SerializedName("sold_batches") val soldBatches: Int,
    @SerializedName("total_quantity_kg") val totalQuantityKg: Float,
    @SerializedName("avg_quality_score") val avgQualityScore: Float?,
    @SerializedName("high_risk_batches") val highRiskBatches: Int,
    @SerializedName("pending_alerts") val pendingAlerts: Int,
    @SerializedName("top_recommendation") val topRecommendation: String?
)

// ─── Alerts ────────────────────────────────────────────

data class Alert(
    val id: Int,
    @SerializedName("alert_type") val alertType: String,
    val title: String,
    val message: String,
    val severity: String,
    @SerializedName("is_read") val isRead: Boolean,
    @SerializedName("created_at") val createdAt: String
)

data class AlertsResponse(
    val alerts: List<Alert>,
    @SerializedName("unread_count") val unreadCount: Int,
    val total: Int
)

// ─── Chatbot ───────────────────────────────────────────

data class ChatMessageRequest(
    val message: String,
    val language: String = "hi",
    val context: Map<String, Any>? = null
)

data class ChatMessageResponse(
    val reply: String,
    val language: String,
    @SerializedName("suggested_actions") val suggestedActions: List<SuggestedAction>,
    val sources: List<String>
)

data class SuggestedAction(
    val type: String,
    val label: String,
    val target: String
)

// ─── Freshness Assessment ──────────────────────────────

data class FreshnessAssessmentResponse(
    @SerializedName("crop_name") val cropName: String,
    @SerializedName("overall_grade") val overallGrade: String,
    @SerializedName("quality_score") val qualityScore: Float,
    @SerializedName("freshness_score") val freshnessScore: Float,
    @SerializedName("damage_score") val damageScore: Float,
    @SerializedName("ripeness_level") val ripenessLevel: String,
    @SerializedName("defects_detected") val defectsDetected: List<String>,
    @SerializedName("analysis_summary") val analysisSummary: String,
    @SerializedName("freshness_status") val freshnessStatus: String? = null,
    val confidence: Float? = null,
    @SerializedName("hindi_label") val hindiLabel: String? = null,
    @SerializedName("model_type") val modelType: String? = null,
    @SerializedName("inference_time_ms") val inferenceTimeMs: Float? = null,
    @SerializedName("recommendation_en") val recommendationEn: String? = null,
    @SerializedName("recommendation_hi") val recommendationHi: String? = null,
    val urgency: String? = null,
    @SerializedName("top_predictions") val topPredictions: List<FreshnessPrediction>? = null
)

data class FreshnessPrediction(
    @SerializedName("class_name") val className: String,
    val probability: Float,
    @SerializedName("hindi_name") val hindiName: String? = null
)

data class ModelStatusResponse(
    @SerializedName("model_loaded") val modelLoaded: Boolean,
    @SerializedName("model_type") val modelType: String,
    @SerializedName("supported_crops") val supportedCrops: List<String>,
    @SerializedName("num_classes") val numClasses: Int
)

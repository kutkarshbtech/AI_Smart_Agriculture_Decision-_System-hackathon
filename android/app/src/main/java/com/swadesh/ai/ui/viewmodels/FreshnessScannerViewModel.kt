package com.swadesh.ai.ui.viewmodels

import android.graphics.Bitmap
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.swadesh.ai.data.api.RetrofitClient
import com.swadesh.ai.data.models.FreshnessAssessmentResponse
import com.swadesh.ai.data.models.ModelStatusResponse
import com.swadesh.ai.ui.screens.FreshnessResult
import com.swadesh.ai.ui.screens.Prediction
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import okhttp3.MediaType.Companion.toMediaTypeOrNull
import okhttp3.MultipartBody
import okhttp3.RequestBody.Companion.toRequestBody
import java.io.ByteArrayOutputStream

data class ScannerUiState(
    val isAnalyzing: Boolean = false,
    val result: FreshnessResult? = null,
    val error: String? = null,
    val modelStatus: ModelStatusResponse? = null,
    val useFallback: Boolean = false
)

class FreshnessScannerViewModel : ViewModel() {

    private val api = RetrofitClient.api

    private val _uiState = MutableStateFlow(ScannerUiState())
    val uiState: StateFlow<ScannerUiState> = _uiState.asStateFlow()

    private val hindiMap = mapOf(
        "apple" to "सेब", "banana" to "केला", "bell_pepper" to "शिमला मिर्च",
        "bitter_gourd" to "करेला", "capsicum" to "शिमला मिर्च", "carrot" to "गाजर",
        "cucumber" to "खीरा", "mango" to "आम", "okra" to "भिंडी",
        "orange" to "संतरा", "potato" to "आलू", "strawberry" to "स्ट्रॉबेरी",
        "tomato" to "टमाटर"
    )

    init {
        checkModelStatus()
    }

    private fun checkModelStatus() {
        viewModelScope.launch {
            try {
                val response = api.getModelStatus()
                if (response.isSuccessful) {
                    _uiState.value = _uiState.value.copy(modelStatus = response.body())
                }
            } catch (_: Exception) {
                // Backend not reachable — will use simulation
                _uiState.value = _uiState.value.copy(useFallback = true)
            }
        }
    }

    fun analyzeFreshness(bitmap: Bitmap, cropName: String) {
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isAnalyzing = true, error = null, result = null)

            try {
                val result = callFreshnessApi(bitmap, cropName)
                _uiState.value = _uiState.value.copy(
                    isAnalyzing = false,
                    result = result
                )
            } catch (e: Exception) {
                // If API fails, use simulation fallback
                val simulated = simulateFreshnessResult(cropName)
                _uiState.value = _uiState.value.copy(
                    isAnalyzing = false,
                    result = simulated,
                    error = "Using offline mode: ${e.message}"
                )
            }
        }
    }

    private suspend fun callFreshnessApi(bitmap: Bitmap, cropName: String): FreshnessResult {
        // Convert bitmap to JPEG bytes
        val stream = ByteArrayOutputStream()
        bitmap.compress(Bitmap.CompressFormat.JPEG, 90, stream)
        val imageBytes = stream.toByteArray()

        val requestBody = imageBytes.toRequestBody("image/jpeg".toMediaTypeOrNull())
        val filePart = MultipartBody.Part.createFormData("file", "capture.jpg", requestBody)

        val response = api.assessFreshnessStandalone(cropName, filePart)

        if (!response.isSuccessful) {
            throw Exception("Server error: ${response.code()}")
        }

        val body = response.body() ?: throw Exception("Empty response")
        return mapApiResponseToResult(body, cropName)
    }

    private fun mapApiResponseToResult(
        response: FreshnessAssessmentResponse,
        cropName: String
    ): FreshnessResult {
        return FreshnessResult(
            freshnessStatus = response.freshnessStatus ?: if (response.freshnessScore >= 50) "fresh" else "rotten",
            confidence = response.confidence ?: (response.qualityScore / 100f),
            qualityGrade = response.overallGrade,
            freshnessScore = response.freshnessScore.toInt(),
            damageScore = response.damageScore.toInt(),
            cropType = response.cropName,
            hindiLabel = response.hindiLabel ?: hindiMap[cropName] ?: cropName,
            ripeness = response.ripenessLevel,
            defects = response.defectsDetected,
            summary = response.analysisSummary,
            recommendationEn = response.recommendationEn
                ?: "Quality grade: ${response.overallGrade}. Score: ${response.qualityScore.toInt()}/100.",
            recommendationHi = response.recommendationHi
                ?: "गुणवत्ता ग्रेड: ${response.overallGrade}। स्कोर: ${response.qualityScore.toInt()}/100।",
            urgency = response.urgency ?: if (response.freshnessScore < 30) "critical" else if (response.freshnessScore < 60) "high" else "low",
            modelType = response.modelType ?: "backend",
            inferenceTimeMs = response.inferenceTimeMs ?: 0f,
            topPredictions = response.topPredictions?.map { pred ->
                Prediction(
                    className = pred.className,
                    confidence = pred.probability,
                    hindi = pred.hindiName ?: ""
                )
            } ?: emptyList()
        )
    }

    fun clearResult() {
        _uiState.value = _uiState.value.copy(result = null, error = null)
    }

    /**
     * Offline simulation fallback — used when backend is unreachable.
     */
    private fun simulateFreshnessResult(cropName: String): FreshnessResult {
        val isFresh = (0..10).random() > 3

        return if (isFresh) {
            FreshnessResult(
                freshnessStatus = "fresh",
                confidence = (75..98).random() / 100f,
                qualityGrade = listOf("excellent", "good").random(),
                freshnessScore = (72..98).random(),
                damageScore = (0..15).random(),
                cropType = cropName,
                hindiLabel = hindiMap[cropName] ?: cropName,
                ripeness = "ripe",
                defects = emptyList(),
                summary = "Your $cropName is in excellent fresh condition.",
                recommendationEn = "Your $cropName is fresh! Sell within 2-3 days for best returns at premium prices.",
                recommendationHi = "आपका ${hindiMap[cropName] ?: cropName} ताज़ा है! 2-3 दिन में बेचने पर अच्छे दाम मिलेंगे।",
                urgency = "low",
                modelType = "offline-simulation",
                inferenceTimeMs = (15..85).random().toFloat(),
                topPredictions = listOf(
                    Prediction("fresh_$cropName", (75..98).random() / 100f, "ताज़ा ${hindiMap[cropName] ?: ""}"),
                    Prediction("rotten_$cropName", (2..25).random() / 100f, "सड़ा ${hindiMap[cropName] ?: ""}")
                )
            )
        } else {
            FreshnessResult(
                freshnessStatus = "rotten",
                confidence = (60..95).random() / 100f,
                qualityGrade = listOf("poor", "average").random(),
                freshnessScore = (8..35).random(),
                damageScore = (55..90).random(),
                cropType = cropName,
                hindiLabel = hindiMap[cropName] ?: cropName,
                ripeness = "overripe",
                defects = listOf("visible spoilage", "discoloration"),
                summary = "Your $cropName shows signs of spoilage.",
                recommendationEn = "Your $cropName shows spoilage. Sell immediately at reduced price or to processing units.",
                recommendationHi = "आपके ${hindiMap[cropName] ?: cropName} में खराबी है। तुरंत कम दाम पर या प्रोसेसिंग यूनिट को बेचें।",
                urgency = "critical",
                modelType = "offline-simulation",
                inferenceTimeMs = (15..85).random().toFloat(),
                topPredictions = listOf(
                    Prediction("rotten_$cropName", (60..95).random() / 100f, "सड़ा ${hindiMap[cropName] ?: ""}"),
                    Prediction("fresh_$cropName", (5..40).random() / 100f, "ताज़ा ${hindiMap[cropName] ?: ""}")
                )
            )
        }
    }
}

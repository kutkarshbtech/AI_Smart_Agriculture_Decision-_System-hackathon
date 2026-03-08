package com.swadesh.ai.ui.viewmodel

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.swadesh.ai.data.models.*
import com.swadesh.ai.data.repository.SwadeshRepository
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

/**
 * ViewModel for ProduceScreen — manages produce batch CRUD and spoilage checks.
 */

data class ProduceUiState(
    val isLoading: Boolean = false,
    val batches: List<ProduceBatch> = emptyList(),
    val spoilageAssessment: SpoilageAssessment? = null,
    val qualityAssessment: QualityAssessment? = null,
    val error: String? = null
)

class ProduceViewModel : ViewModel() {

    private val repository = SwadeshRepository()

    private val _uiState = MutableStateFlow(ProduceUiState())
    val uiState: StateFlow<ProduceUiState> = _uiState.asStateFlow()

    init {
        loadBatches()
    }

    fun loadBatches() {
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isLoading = true, error = null)

            repository.getProduceBatches("demo_farmer")
                .onSuccess { batches ->
                    _uiState.value = _uiState.value.copy(
                        isLoading = false,
                        batches = batches
                    )
                }
                .onFailure { e ->
                    _uiState.value = _uiState.value.copy(
                        isLoading = false,
                        error = e.message
                    )
                }
        }
    }

    fun addBatch(request: CreateProduceBatchRequest) {
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isLoading = true)

            repository.createProduceBatch(request)
                .onSuccess {
                    loadBatches() // Refresh list
                }
                .onFailure { e ->
                    _uiState.value = _uiState.value.copy(
                        isLoading = false,
                        error = e.message
                    )
                }
        }
    }

    fun assessSpoilage(batchId: String) {
        viewModelScope.launch {
            repository.assessSpoilage(batchId)
                .onSuccess { assessment ->
                    _uiState.value = _uiState.value.copy(
                        spoilageAssessment = assessment
                    )
                }
                .onFailure { e ->
                    _uiState.value = _uiState.value.copy(error = e.message)
                }
        }
    }

    fun assessQuality(batchId: String) {
        viewModelScope.launch {
            repository.getSimulatedQuality(batchId)
                .onSuccess { assessment ->
                    _uiState.value = _uiState.value.copy(
                        qualityAssessment = assessment
                    )
                }
                .onFailure { e ->
                    _uiState.value = _uiState.value.copy(error = e.message)
                }
        }
    }

    fun clearAssessments() {
        _uiState.value = _uiState.value.copy(
            spoilageAssessment = null,
            qualityAssessment = null
        )
    }

    fun refresh() = loadBatches()
}

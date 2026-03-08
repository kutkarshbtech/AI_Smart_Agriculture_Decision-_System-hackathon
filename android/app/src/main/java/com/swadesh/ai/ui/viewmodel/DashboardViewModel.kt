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
 * ViewModel for DashboardScreen — loads summary data and recommendations.
 */

data class DashboardUiState(
    val isLoading: Boolean = false,
    val summary: DashboardSummary? = null,
    val recommendations: List<ActionRecommendation> = emptyList(),
    val error: String? = null
)

class DashboardViewModel : ViewModel() {

    private val repository = SwadeshRepository()

    private val _uiState = MutableStateFlow(DashboardUiState())
    val uiState: StateFlow<DashboardUiState> = _uiState.asStateFlow()

    init {
        loadDashboard()
    }

    fun loadDashboard() {
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isLoading = true, error = null)

            // Load summary and recommendations in parallel
            val summaryResult = repository.getDashboardSummary("demo_farmer")
            val recsResult = repository.getDashboardRecommendations("demo_farmer")

            summaryResult.onSuccess { summary ->
                _uiState.value = _uiState.value.copy(summary = summary)
            }.onFailure { e ->
                _uiState.value = _uiState.value.copy(error = e.message)
            }

            recsResult.onSuccess { recs ->
                _uiState.value = _uiState.value.copy(recommendations = recs)
            }

            _uiState.value = _uiState.value.copy(isLoading = false)
        }
    }

    fun refresh() = loadDashboard()
}

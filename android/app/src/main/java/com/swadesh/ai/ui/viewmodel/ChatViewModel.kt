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
 * ViewModel for ChatScreen — manages chat messages with AI backend.
 */

data class ChatUiState(
    val isLoading: Boolean = false,
    val messages: List<ChatMessage> = emptyList(),
    val error: String? = null
)

class ChatViewModel : ViewModel() {

    private val repository = SwadeshRepository()

    private val _uiState = MutableStateFlow(ChatUiState())
    val uiState: StateFlow<ChatUiState> = _uiState.asStateFlow()

    init {
        loadWelcome()
    }

    private fun loadWelcome() {
        viewModelScope.launch {
            repository.getChatWelcome()
                .onSuccess { welcome ->
                    _uiState.value = _uiState.value.copy(
                        messages = listOf(welcome)
                    )
                }
        }
    }

    fun sendMessage(text: String) {
        viewModelScope.launch {
            // Add user message
            val userMsg = ChatMessage(
                message = text,
                isUser = true,
                language = if (text.any { it.code > 255 }) "hi" else "en"
            )
            val updatedMessages = _uiState.value.messages + userMsg
            _uiState.value = _uiState.value.copy(
                messages = updatedMessages,
                isLoading = true,
                error = null
            )

            // Send to backend
            val request = ChatRequest(
                message = text,
                userId = "demo_farmer",
                language = userMsg.language
            )
            repository.sendChatMessage(request)
                .onSuccess { response ->
                    _uiState.value = _uiState.value.copy(
                        messages = _uiState.value.messages + response,
                        isLoading = false
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
}

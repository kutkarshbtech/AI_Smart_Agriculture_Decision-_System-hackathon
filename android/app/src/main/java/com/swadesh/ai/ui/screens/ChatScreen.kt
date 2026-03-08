package com.swadesh.ai.ui.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.lazy.rememberLazyListState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import kotlinx.coroutines.launch

/**
 * AI Chat screen — multilingual chatbot (Hindi + English) for farmer queries.
 * Powered by Amazon Bedrock Claude via SwadeshAI backend.
 */

data class ChatMsg(
    val text: String,
    val isUser: Boolean,
    val timestamp: String = "",
    val suggestedActions: List<String> = emptyList()
)

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ChatScreen() {
    var message by remember { mutableStateOf("") }
    var isLoading by remember { mutableStateOf(false) }
    val listState = rememberLazyListState()
    val scope = rememberCoroutineScope()

    val messages = remember {
        mutableStateListOf(
            ChatMsg(
                text = "नमस्ते! मैं SwadeshAI हूँ 🌾\n\nHello! I'm SwadeshAI, your farming assistant.\n\nYou can ask me about:\n• Market prices / मंडी भाव\n• Spoilage prevention / खराबी रोकथाम\n• Weather impact / मौसम का प्रभाव\n• Best buyers / सबसे अच्छे खरीदार\n• Storage tips / भंडारण सुझाव\n\nकिसी भी भाषा में पूछें - हिंदी या English!",
                isUser = false,
                suggestedActions = listOf(
                    "टमाटर का भाव क्या है?",
                    "How to store potatoes?",
                    "मेरी फसल कब बेचूं?",
                    "Weather forecast"
                )
            )
        )
    }

    // Simulated responses for demo
    fun getAIResponse(userMsg: String): ChatMsg {
        val lowerMsg = userMsg.lowercase()
        return when {
            lowerMsg.contains("भाव") || lowerMsg.contains("price") || lowerMsg.contains("rate") -> ChatMsg(
                text = "📊 Current market prices / आज के मंडी भाव:\n\n" +
                        "🍅 Tomato / टमाटर: ₹35/kg (↑17%)\n" +
                        "🥔 Potato / आलू: ₹18/kg (↓10%)\n" +
                        "🧅 Onion / प्याज: ₹28/kg (↑12%)\n" +
                        "🥭 Mango / आम: ₹65/kg (↑8%)\n\n" +
                        "💡 Tip: Tomato prices are high right now — good time to sell!\n" +
                        "सुझाव: टमाटर के भाव अभी ऊंचे हैं — बेचने का अच्छा समय!",
                isUser = false,
                suggestedActions = listOf("Find buyers for tomato", "Price trend for potato", "When to sell mango?")
            )

            lowerMsg.contains("store") || lowerMsg.contains("भंडार") || lowerMsg.contains("रख") -> ChatMsg(
                text = "🏪 Storage Tips / भंडारण सुझाव:\n\n" +
                        "🥔 Potato / आलू:\n" +
                        "• Cool, dark place (10-15°C)\n" +
                        "• Good ventilation / हवा का बहाव\n" +
                        "• Lasts 2-3 months if stored properly\n\n" +
                        "🍅 Tomato / टमाटर:\n" +
                        "• Room temperature until ripe\n" +
                        "• Refrigerate when fully ripe\n" +
                        "• कमरे के तापमान पर पकने दें\n\n" +
                        "🧅 Onion / प्याज:\n" +
                        "• Dry, well-ventilated area\n" +
                        "• Spread on racks, don't pile\n" +
                        "• सूखी, हवादार जगह पर रखें",
                isUser = false,
                suggestedActions = listOf("Cold storage nearby?", "How long can I store wheat?")
            )

            lowerMsg.contains("बेच") || lowerMsg.contains("sell") || lowerMsg.contains("when") -> ChatMsg(
                text = "📈 Selling Recommendation / बिक्री सुझाव:\n\n" +
                        "Based on current market analysis:\n\n" +
                        "✅ SELL NOW / अभी बेचें:\n" +
                        "• Tomato — prices are 17% above average\n" +
                        "• Mango — peak season, perishable\n\n" +
                        "⏳ WAIT / रुकें:\n" +
                        "• Potato — prices expected to rise in 2 weeks\n" +
                        "• Wheat — stable, can store safely\n\n" +
                        "⚠️ Spoilage Risk / खराबी का खतरा:\n" +
                        "If temperature > 35°C, sell perishables within 2 days!\n" +
                        "अगर तापमान 35°C से ज्यादा है, जल्दी बेचें!",
                isUser = false,
                suggestedActions = listOf("Find buyers near me", "Check spoilage risk", "Price forecast next week")
            )

            lowerMsg.contains("weather") || lowerMsg.contains("मौसम") -> ChatMsg(
                text = "🌤️ Weather Impact / मौसम का प्रभाव:\n\n" +
                        "Current: 34°C, Humidity 65%\n\n" +
                        "⚠️ Impact on your produce:\n\n" +
                        "🍅 Tomato: HIGH RISK\n" +
                        "Heat + humidity = rapid spoilage\n" +
                        "Sell within 2 days or cold store\n" +
                        "गर्मी + नमी = जल्दी खराब\n\n" +
                        "🥔 Potato: LOW RISK\n" +
                        "Store in cool, dark place\n" +
                        "ठंडी, अँधेरी जगह पर रखें\n\n" +
                        "🥭 Mango: MEDIUM RISK\n" +
                        "Will ripen fast, sell soon\n" +
                        "जल्दी पकेगा, जल्दी बेचें",
                isUser = false,
                suggestedActions = listOf("3-day weather forecast", "How to protect from heat?")
            )

            lowerMsg.contains("buyer") || lowerMsg.contains("खरीद") -> ChatMsg(
                text = "🤝 Buyer Matches / खरीदार मिलान:\n\n" +
                        "I found these matches for your produce:\n\n" +
                        "1. Sharma Trading Co. (5.2 km)\n" +
                        "   Rating: ⭐⭐⭐⭐½\n" +
                        "   Match: 92% | Buys: Tomato, Potato\n\n" +
                        "2. Fresh Direct India (82 km)\n" +
                        "   Rating: ⭐⭐⭐⭐\n" +
                        "   Match: 85% | Buys: Mango, Banana\n\n" +
                        "Go to Buyers tab for more details and to contact them!\n" +
                        "और जानकारी के लिए Buyers टैब पर जाएं!",
                isUser = false,
                suggestedActions = listOf("Call Sharma Trading", "Send price offer")
            )

            else -> ChatMsg(
                text = "I understand your question. Let me help! / मैं आपकी मदद करता हूँ!\n\n" +
                        "Here's what I can assist with:\n\n" +
                        "📊 Market prices & selling advice\n" +
                        "🔬 Spoilage risk assessment\n" +
                        "🌤️ Weather-based guidance\n" +
                        "🤝 Buyer matching\n" +
                        "🏪 Storage recommendations\n\n" +
                        "Try asking: \"What's the price of tomato?\" or \"टमाटर कब बेचूं?\"\n\n" +
                        "आप हिंदी में भी पूछ सकते हैं!",
                isUser = false,
                suggestedActions = listOf("Check market prices", "मंडी भाव बताओ", "Storage tips", "Find buyers nearby")
            )
        }
    }

    Column(modifier = Modifier.fillMaxSize()) {
        // Chat header
        Surface(
            color = MaterialTheme.colorScheme.primaryContainer,
            modifier = Modifier.fillMaxWidth()
        ) {
            Row(
                modifier = Modifier.padding(16.dp),
                verticalAlignment = Alignment.CenterVertically
            ) {
                Surface(
                    modifier = Modifier
                        .size(40.dp)
                        .clip(CircleShape),
                    color = MaterialTheme.colorScheme.primary
                ) {
                    Box(contentAlignment = Alignment.Center) {
                        Text("🌾", style = MaterialTheme.typography.titleMedium)
                    }
                }
                Spacer(modifier = Modifier.width(12.dp))
                Column {
                    Text(
                        "SwadeshAI Assistant",
                        style = MaterialTheme.typography.titleSmall,
                        fontWeight = FontWeight.Bold
                    )
                    Text(
                        "Online • Hindi & English",
                        style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.onPrimaryContainer.copy(alpha = 0.7f)
                    )
                }
            }
        }

        // Messages
        LazyColumn(
            modifier = Modifier
                .weight(1f)
                .padding(horizontal = 12.dp),
            state = listState,
            contentPadding = PaddingValues(vertical = 8.dp),
            verticalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            items(messages) { msg ->
                ChatBubble(msg) { action ->
                    // Handle suggested action taps
                    messages.add(ChatMsg(text = action, isUser = true))
                    val response = getAIResponse(action)
                    messages.add(response)
                    scope.launch {
                        listState.animateScrollToItem(messages.size - 1)
                    }
                }
            }

            if (isLoading) {
                item {
                    Row(
                        modifier = Modifier.padding(8.dp),
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        CircularProgressIndicator(
                            modifier = Modifier.size(16.dp),
                            strokeWidth = 2.dp
                        )
                        Spacer(modifier = Modifier.width(8.dp))
                        Text(
                            "Thinking... / सोच रहा हूँ...",
                            style = MaterialTheme.typography.bodySmall,
                            color = MaterialTheme.colorScheme.onSurfaceVariant
                        )
                    }
                }
            }
        }

        // Input bar
        Surface(
            modifier = Modifier.fillMaxWidth(),
            shadowElevation = 8.dp
        ) {
            Row(
                modifier = Modifier
                    .padding(12.dp)
                    .fillMaxWidth(),
                verticalAlignment = Alignment.CenterVertically
            ) {
                OutlinedTextField(
                    value = message,
                    onValueChange = { message = it },
                    placeholder = {
                        Text(
                            "Type message / संदेश लिखें...",
                            style = MaterialTheme.typography.bodyMedium
                        )
                    },
                    modifier = Modifier.weight(1f),
                    shape = RoundedCornerShape(24.dp),
                    maxLines = 3
                )
                Spacer(modifier = Modifier.width(8.dp))
                FilledIconButton(
                    onClick = {
                        if (message.isNotBlank()) {
                            val userMsg = message.trim()
                            messages.add(ChatMsg(text = userMsg, isUser = true))
                            message = ""

                            // Simulate AI response
                            isLoading = true
                            val response = getAIResponse(userMsg)
                            isLoading = false
                            messages.add(response)

                            scope.launch {
                                listState.animateScrollToItem(messages.size - 1)
                            }
                        }
                    },
                    enabled = message.isNotBlank()
                ) {
                    Icon(Icons.Filled.Send, contentDescription = "Send")
                }
            }
        }
    }
}

@Composable
fun ChatBubble(
    msg: ChatMsg,
    onActionClick: (String) -> Unit
) {
    Column(
        modifier = Modifier.fillMaxWidth(),
        horizontalAlignment = if (msg.isUser) Alignment.End else Alignment.Start
    ) {
        Surface(
            shape = RoundedCornerShape(
                topStart = 16.dp,
                topEnd = 16.dp,
                bottomStart = if (msg.isUser) 16.dp else 4.dp,
                bottomEnd = if (msg.isUser) 4.dp else 16.dp
            ),
            color = if (msg.isUser)
                MaterialTheme.colorScheme.primary
            else
                MaterialTheme.colorScheme.surfaceVariant,
            modifier = Modifier.widthIn(max = 300.dp)
        ) {
            Text(
                text = msg.text,
                modifier = Modifier.padding(12.dp),
                style = MaterialTheme.typography.bodyMedium,
                color = if (msg.isUser)
                    MaterialTheme.colorScheme.onPrimary
                else
                    MaterialTheme.colorScheme.onSurfaceVariant
            )
        }

        // Suggested quick actions
        if (msg.suggestedActions.isNotEmpty() && !msg.isUser) {
            Spacer(modifier = Modifier.height(8.dp))
            Column(
                verticalArrangement = Arrangement.spacedBy(4.dp)
            ) {
                msg.suggestedActions.forEach { action ->
                    SuggestionChip(
                        onClick = { onActionClick(action) },
                        label = {
                            Text(action, style = MaterialTheme.typography.labelSmall)
                        },
                        icon = {
                            Icon(
                                Icons.Filled.TouchApp,
                                contentDescription = null,
                                modifier = Modifier.size(14.dp)
                            )
                        }
                    )
                }
            }
        }
    }
}

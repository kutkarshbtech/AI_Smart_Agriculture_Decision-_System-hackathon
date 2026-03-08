package com.swadesh.ai.ui.screens

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp

/**
 * Market Prices screen — shows mandi prices, trends, and AI price recommendations.
 */

data class MarketPriceItem(
    val cropName: String,
    val cropNameHindi: String,
    val currentPrice: Double,
    val previousPrice: Double,
    val unit: String = "₹/kg",
    val mandi: String,
    val trend: String // "up", "down", "stable"
)

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun PricesScreen() {
    var selectedTab by remember { mutableIntStateOf(0) }

    val marketPrices = remember {
        listOf(
            MarketPriceItem("Tomato", "टमाटर", 35.0, 30.0, mandi = "Lucknow Mandi", trend = "up"),
            MarketPriceItem("Potato", "आलू", 18.0, 20.0, mandi = "Kanpur Mandi", trend = "down"),
            MarketPriceItem("Onion", "प्याज", 28.0, 25.0, mandi = "Nashik Mandi", trend = "up"),
            MarketPriceItem("Rice", "चावल", 42.0, 42.0, mandi = "Lucknow Mandi", trend = "stable"),
            MarketPriceItem("Mango", "आम", 65.0, 60.0, mandi = "Malihabad Mandi", trend = "up"),
            MarketPriceItem("Wheat", "गेहूं", 25.0, 26.0, mandi = "Kanpur Mandi", trend = "down"),
            MarketPriceItem("Banana", "केला", 30.0, 28.0, mandi = "Varanasi Mandi", trend = "up"),
            MarketPriceItem("Cauliflower", "फूलगोभी", 22.0, 24.0, mandi = "Patna Mandi", trend = "down"),
        )
    }

    Column(modifier = Modifier.fillMaxSize()) {
        // Tab row
        TabRow(selectedTabIndex = selectedTab) {
            Tab(
                selected = selectedTab == 0,
                onClick = { selectedTab = 0 },
                text = { Text("Live Prices\nमंडी भाव") },
                icon = { Icon(Icons.Filled.TrendingUp, contentDescription = null) }
            )
            Tab(
                selected = selectedTab == 1,
                onClick = { selectedTab = 1 },
                text = { Text("AI Advice\nAI सुझाव") },
                icon = { Icon(Icons.Filled.Lightbulb, contentDescription = null) }
            )
        }

        when (selectedTab) {
            0 -> LivePricesTab(marketPrices)
            1 -> AIAdviceTab()
        }
    }
}

@Composable
fun LivePricesTab(prices: List<MarketPriceItem>) {
    LazyColumn(
        modifier = Modifier.padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp)
    ) {
        item {
            Text(
                "Today's Market Prices / आज के मंडी भाव",
                style = MaterialTheme.typography.titleMedium,
                fontWeight = FontWeight.Bold
            )
            Spacer(modifier = Modifier.height(4.dp))
            Text(
                "Updated hourly from major mandis",
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant
            )
        }

        items(prices) { price ->
            PriceCard(price)
        }
    }
}

@Composable
fun PriceCard(price: MarketPriceItem) {
    val changePercent = ((price.currentPrice - price.previousPrice) / price.previousPrice * 100)
    val trendIcon = when (price.trend) {
        "up" -> Icons.Filled.TrendingUp
        "down" -> Icons.Filled.TrendingDown
        else -> Icons.Filled.TrendingFlat
    }
    val trendColor = when (price.trend) {
        "up" -> MaterialTheme.colorScheme.primary
        "down" -> MaterialTheme.colorScheme.error
        else -> MaterialTheme.colorScheme.onSurfaceVariant
    }

    Card(
        modifier = Modifier.fillMaxWidth(),
        shape = RoundedCornerShape(12.dp)
    ) {
        Row(
            modifier = Modifier
                .padding(16.dp)
                .fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Column(modifier = Modifier.weight(1f)) {
                Text(
                    "${price.cropName} / ${price.cropNameHindi}",
                    style = MaterialTheme.typography.titleSmall,
                    fontWeight = FontWeight.Bold
                )
                Spacer(modifier = Modifier.height(4.dp))
                Text(
                    price.mandi,
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
            }

            Column(horizontalAlignment = Alignment.End) {
                Text(
                    "₹${price.currentPrice.toInt()}/kg",
                    style = MaterialTheme.typography.titleMedium,
                    fontWeight = FontWeight.Bold
                )
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Icon(
                        trendIcon,
                        contentDescription = null,
                        modifier = Modifier.size(16.dp),
                        tint = trendColor
                    )
                    Spacer(modifier = Modifier.width(4.dp))
                    Text(
                        "${if (changePercent >= 0) "+" else ""}${"%.1f".format(changePercent)}%",
                        style = MaterialTheme.typography.labelSmall,
                        color = trendColor
                    )
                }
            }
        }
    }
}

@Composable
fun AIAdviceTab() {
    LazyColumn(
        modifier = Modifier.padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp)
    ) {
        item {
            Text(
                "AI Price Recommendations / AI मूल्य सुझाव",
                style = MaterialTheme.typography.titleMedium,
                fontWeight = FontWeight.Bold
            )
            Spacer(modifier = Modifier.height(4.dp))
            Text(
                "Based on market trends, weather, and your produce quality",
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant
            )
        }

        item {
            AdviceCard(
                crop = "Tomato / टमाटर",
                advice = "SELL NOW / अभी बेचें",
                reason = "Prices are 17% above average. High temperatures this week may increase spoilage risk. Consider selling at Lucknow Mandi.\n\nकीमतें औसत से 17% ऊपर हैं। इस सप्ताह उच्च तापमान से खराब होने का खतरा बढ़ सकता है।",
                suggestedPrice = "₹32-35/kg",
                isUrgent = true
            )
        }

        item {
            AdviceCard(
                crop = "Potato / आलू",
                advice = "WAIT & STORE / रुकें और स्टोर करें",
                reason = "Prices are declining but expected to recover in 2 weeks. Store in cool, dry place.\n\nकीमतें कम हो रही हैं लेकिन 2 हफ्तों में ठीक होने की उम्मीद है। ठंडी, सूखी जगह पर रखें।",
                suggestedPrice = "₹20-22/kg (in 2 weeks)",
                isUrgent = false
            )
        }

        item {
            AdviceCard(
                crop = "Mango / आम",
                advice = "SELL SOON / जल्दी बेचें",
                reason = "Peak season prices. Mangoes are highly perishable — sell within 2 days for best returns.\n\nसीजन के सबसे अच्छे भाव। आम जल्दी खराब होते हैं — 2 दिन में सबसे अच्छा मुनाफा।",
                suggestedPrice = "₹60-65/kg",
                isUrgent = true
            )
        }
    }
}

@Composable
fun AdviceCard(
    crop: String,
    advice: String,
    reason: String,
    suggestedPrice: String,
    isUrgent: Boolean
) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        colors = CardDefaults.cardColors(
            containerColor = if (isUrgent)
                MaterialTheme.colorScheme.tertiaryContainer
            else
                MaterialTheme.colorScheme.surfaceVariant
        ),
        shape = RoundedCornerShape(16.dp)
    ) {
        Column(modifier = Modifier.padding(16.dp)) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(
                    crop,
                    style = MaterialTheme.typography.titleSmall,
                    fontWeight = FontWeight.Bold
                )
                AssistChip(
                    onClick = {},
                    label = {
                        Text(
                            advice,
                            style = MaterialTheme.typography.labelSmall,
                            fontWeight = FontWeight.Bold
                        )
                    },
                    colors = AssistChipDefaults.assistChipColors(
                        containerColor = if (isUrgent)
                            MaterialTheme.colorScheme.error.copy(alpha = 0.1f)
                        else
                            MaterialTheme.colorScheme.primary.copy(alpha = 0.1f)
                    )
                )
            }

            Spacer(modifier = Modifier.height(8.dp))

            Text(
                reason,
                style = MaterialTheme.typography.bodySmall
            )

            Spacer(modifier = Modifier.height(12.dp))

            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(
                    "Suggested: $suggestedPrice",
                    style = MaterialTheme.typography.labelMedium,
                    fontWeight = FontWeight.Bold,
                    color = MaterialTheme.colorScheme.primary
                )
                Button(
                    onClick = { /* Find buyers */ },
                    contentPadding = PaddingValues(horizontal = 16.dp, vertical = 4.dp)
                ) {
                    Text("Find Buyers", style = MaterialTheme.typography.labelSmall)
                }
            }
        }
    }
}

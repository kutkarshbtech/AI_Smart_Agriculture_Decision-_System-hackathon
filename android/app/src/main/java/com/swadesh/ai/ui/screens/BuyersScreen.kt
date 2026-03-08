package com.swadesh.ai.ui.screens

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
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

/**
 * Buyers screen — shows matched buyers, nearby aggregators, and logistics options.
 */

data class BuyerItem(
    val id: String,
    val name: String,
    val businessType: String,
    val location: String,
    val distance: Double, // km
    val preferredCrops: List<String>,
    val rating: Float,
    val phone: String,
    val matchScore: Int // 0-100
)

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun BuyersScreen() {
    var selectedTab by remember { mutableIntStateOf(0) }

    val buyers = remember {
        listOf(
            BuyerItem("1", "Sharma Trading Co.", "Wholesaler", "Lucknow", 5.2,
                listOf("Tomato", "Potato", "Onion"), 4.5f, "+91 98765 43210", 92),
            BuyerItem("2", "Fresh Direct India", "Retailer", "Kanpur", 82.0,
                listOf("Mango", "Banana", "Apple"), 4.2f, "+91 87654 32109", 85),
            BuyerItem("3", "Agarwal Vegetables", "Wholesaler", "Varanasi", 15.3,
                listOf("Cauliflower", "Spinach", "Okra"), 4.0f, "+91 76543 21098", 78),
            BuyerItem("4", "Patel Exports", "Exporter", "Ahmedabad", 950.0,
                listOf("Mango", "Grapes", "Pomegranate"), 4.8f, "+91 65432 10987", 70),
            BuyerItem("5", "Gupta Cold Storage", "Cold Storage", "Patna", 120.0,
                listOf("Potato", "Onion", "Apple"), 3.9f, "+91 54321 09876", 65),
            BuyerItem("6", "Singh Retail Chain", "Retailer", "Jaipur", 600.0,
                listOf("Tomato", "Mango", "Banana"), 4.3f, "+91 43210 98765", 60),
        )
    }

    Column(modifier = Modifier.fillMaxSize()) {
        TabRow(selectedTabIndex = selectedTab) {
            Tab(
                selected = selectedTab == 0,
                onClick = { selectedTab = 0 },
                text = { Text("AI Matched\nAI मिलान") },
                icon = { Icon(Icons.Filled.AutoAwesome, contentDescription = null) }
            )
            Tab(
                selected = selectedTab == 1,
                onClick = { selectedTab = 1 },
                text = { Text("Nearby\nआस-पास") },
                icon = { Icon(Icons.Filled.NearMe, contentDescription = null) }
            )
        }

        when (selectedTab) {
            0 -> MatchedBuyersTab(buyers.sortedByDescending { it.matchScore })
            1 -> NearbyBuyersTab(buyers.sortedBy { it.distance })
        }
    }
}

@Composable
fun MatchedBuyersTab(buyers: List<BuyerItem>) {
    LazyColumn(
        modifier = Modifier.padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp)
    ) {
        item {
            Text(
                "Best Matches / सबसे अच्छे खरीदार",
                style = MaterialTheme.typography.titleMedium,
                fontWeight = FontWeight.Bold
            )
            Spacer(modifier = Modifier.height(4.dp))
            Text(
                "Ranked by crop match, distance, and reliability",
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant
            )
        }

        items(buyers) { buyer ->
            BuyerCard(buyer, showMatchScore = true)
        }
    }
}

@Composable
fun NearbyBuyersTab(buyers: List<BuyerItem>) {
    LazyColumn(
        modifier = Modifier.padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp)
    ) {
        item {
            Text(
                "Nearby Buyers / आस-पास के खरीदार",
                style = MaterialTheme.typography.titleMedium,
                fontWeight = FontWeight.Bold
            )
            Spacer(modifier = Modifier.height(4.dp))
            Text(
                "Sorted by distance from your location",
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant
            )
        }

        items(buyers) { buyer ->
            BuyerCard(buyer, showMatchScore = false)
        }
    }
}

@Composable
fun BuyerCard(buyer: BuyerItem, showMatchScore: Boolean) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        shape = RoundedCornerShape(16.dp)
    ) {
        Column(modifier = Modifier.padding(16.dp)) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                verticalAlignment = Alignment.CenterVertically
            ) {
                // Avatar
                Surface(
                    modifier = Modifier
                        .size(48.dp)
                        .clip(CircleShape),
                    color = MaterialTheme.colorScheme.primaryContainer
                ) {
                    Box(contentAlignment = Alignment.Center) {
                        Text(
                            buyer.name.first().toString(),
                            style = MaterialTheme.typography.titleLarge,
                            fontWeight = FontWeight.Bold,
                            color = MaterialTheme.colorScheme.primary
                        )
                    }
                }

                Spacer(modifier = Modifier.width(12.dp))

                Column(modifier = Modifier.weight(1f)) {
                    Text(
                        buyer.name,
                        style = MaterialTheme.typography.titleSmall,
                        fontWeight = FontWeight.Bold
                    )
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Text(
                            buyer.businessType,
                            style = MaterialTheme.typography.bodySmall,
                            color = MaterialTheme.colorScheme.primary
                        )
                        Text(
                            " • ",
                            color = MaterialTheme.colorScheme.onSurfaceVariant
                        )
                        Icon(
                            Icons.Filled.LocationOn,
                            contentDescription = null,
                            modifier = Modifier.size(12.dp),
                            tint = MaterialTheme.colorScheme.onSurfaceVariant
                        )
                        Text(
                            "${buyer.location} (${formatDistance(buyer.distance)})",
                            style = MaterialTheme.typography.bodySmall,
                            color = MaterialTheme.colorScheme.onSurfaceVariant
                        )
                    }
                }

                if (showMatchScore) {
                    Column(horizontalAlignment = Alignment.CenterHorizontally) {
                        Text(
                            "${buyer.matchScore}%",
                            style = MaterialTheme.typography.titleMedium,
                            fontWeight = FontWeight.Bold,
                            color = MaterialTheme.colorScheme.primary
                        )
                        Text(
                            "match",
                            style = MaterialTheme.typography.labelSmall,
                            color = MaterialTheme.colorScheme.onSurfaceVariant
                        )
                    }
                }
            }

            Spacer(modifier = Modifier.height(12.dp))

            // Preferred crops
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(6.dp)
            ) {
                buyer.preferredCrops.take(4).forEach { crop ->
                    SuggestionChip(
                        onClick = {},
                        label = {
                            Text(crop, style = MaterialTheme.typography.labelSmall)
                        }
                    )
                }
            }

            Spacer(modifier = Modifier.height(8.dp))

            // Rating
            Row(
                verticalAlignment = Alignment.CenterVertically
            ) {
                repeat(5) { i ->
                    Icon(
                        if (i < buyer.rating.toInt()) Icons.Filled.Star else Icons.Filled.StarBorder,
                        contentDescription = null,
                        modifier = Modifier.size(14.dp),
                        tint = MaterialTheme.colorScheme.tertiary
                    )
                }
                Spacer(modifier = Modifier.width(4.dp))
                Text(
                    "${buyer.rating}",
                    style = MaterialTheme.typography.labelSmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
            }

            Spacer(modifier = Modifier.height(12.dp))

            // Action buttons
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                OutlinedButton(
                    onClick = { /* Call buyer */ },
                    modifier = Modifier.weight(1f)
                ) {
                    Icon(Icons.Filled.Phone, contentDescription = null, modifier = Modifier.size(16.dp))
                    Spacer(modifier = Modifier.width(4.dp))
                    Text("Call / कॉल", style = MaterialTheme.typography.labelMedium)
                }
                Button(
                    onClick = { /* Send offer */ },
                    modifier = Modifier.weight(1f)
                ) {
                    Icon(Icons.Filled.Send, contentDescription = null, modifier = Modifier.size(16.dp))
                    Spacer(modifier = Modifier.width(4.dp))
                    Text("Send Offer", style = MaterialTheme.typography.labelMedium)
                }
            }
        }
    }
}

fun formatDistance(km: Double): String {
    return if (km < 1) {
        "${(km * 1000).toInt()} m"
    } else if (km < 100) {
        "${"%.1f".format(km)} km"
    } else {
        "${km.toInt()} km"
    }
}

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
 * Produce inventory screen — shows list of farmer's produce batches
 * with spoilage risk indicators and quality info.
 */

// Simplified local model for display
data class ProduceItem(
    val id: String,
    val cropName: String,
    val cropNameHindi: String,
    val quantity: Double,
    val unit: String = "kg",
    val qualityGrade: String = "Good",
    val spoilageRisk: String = "low",
    val daysRemaining: Int = 5,
    val location: String = ""
)

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ProduceScreen() {
    var showAddDialog by remember { mutableStateOf(false) }
    var produceList by remember {
        mutableStateOf(
            listOf(
                ProduceItem("1", "Tomato", "टमाटर", 50.0, spoilageRisk = "medium", daysRemaining = 3, location = "Lucknow"),
                ProduceItem("2", "Potato", "आलू", 200.0, spoilageRisk = "low", daysRemaining = 14, location = "Kanpur"),
                ProduceItem("3", "Mango", "आम", 30.0, spoilageRisk = "high", daysRemaining = 1, location = "Varanasi")
            )
        )
    }

    Scaffold(
        floatingActionButton = {
            ExtendedFloatingActionButton(
                onClick = { showAddDialog = true },
                icon = { Icon(Icons.Filled.Add, contentDescription = null) },
                text = { Text("Add / जोड़ें") },
                containerColor = MaterialTheme.colorScheme.primary
            )
        }
    ) { paddingValues ->
        LazyColumn(
            modifier = Modifier
                .fillMaxSize()
                .padding(paddingValues)
                .padding(horizontal = 16.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp),
            contentPadding = PaddingValues(vertical = 16.dp)
        ) {
            item {
                Text(
                    "My Produce / मेरी फसल",
                    style = MaterialTheme.typography.headlineSmall,
                    fontWeight = FontWeight.Bold
                )
                Spacer(modifier = Modifier.height(4.dp))
                Text(
                    "${produceList.size} batches • ${produceList.sumOf { it.quantity }.toInt()} kg total",
                    style = MaterialTheme.typography.bodyMedium,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
            }

            items(produceList) { item ->
                ProduceCard(item)
            }

            if (produceList.isEmpty()) {
                item {
                    EmptyProduceState()
                }
            }
        }
    }

    if (showAddDialog) {
        AddProduceDialog(
            onDismiss = { showAddDialog = false },
            onAdd = { newItem ->
                produceList = produceList + newItem
                showAddDialog = false
            }
        )
    }
}

@Composable
fun ProduceCard(item: ProduceItem) {
    val riskColor = when (item.spoilageRisk) {
        "critical" -> MaterialTheme.colorScheme.error
        "high" -> MaterialTheme.colorScheme.error.copy(alpha = 0.8f)
        "medium" -> MaterialTheme.colorScheme.tertiary
        else -> MaterialTheme.colorScheme.primary
    }
    val riskLabel = when (item.spoilageRisk) {
        "critical" -> "🔴 Critical / गंभीर"
        "high" -> "🟠 High / उच्च"
        "medium" -> "🟡 Medium / मध्यम"
        else -> "🟢 Low / कम"
    }

    Card(
        modifier = Modifier.fillMaxWidth(),
        shape = RoundedCornerShape(16.dp)
    ) {
        Column(modifier = Modifier.padding(16.dp)) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Column {
                    Text(
                        "${item.cropName} / ${item.cropNameHindi}",
                        style = MaterialTheme.typography.titleMedium,
                        fontWeight = FontWeight.Bold
                    )
                    Text(
                        "${item.quantity.toInt()} ${item.unit}",
                        style = MaterialTheme.typography.bodyLarge,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                }
                SuggestionChip(
                    onClick = {},
                    label = {
                        Text(
                            riskLabel,
                            style = MaterialTheme.typography.labelSmall
                        )
                    }
                )
            }

            Spacer(modifier = Modifier.height(12.dp))
            HorizontalDivider()
            Spacer(modifier = Modifier.height(12.dp))

            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween
            ) {
                InfoChip(
                    icon = Icons.Filled.Timer,
                    label = "${item.daysRemaining} days left"
                )
                InfoChip(
                    icon = Icons.Filled.Star,
                    label = item.qualityGrade
                )
                if (item.location.isNotBlank()) {
                    InfoChip(
                        icon = Icons.Filled.LocationOn,
                        label = item.location
                    )
                }
            }

            Spacer(modifier = Modifier.height(12.dp))

            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                OutlinedButton(
                    onClick = { /* Check spoilage */ },
                    modifier = Modifier.weight(1f)
                ) {
                    Icon(Icons.Filled.Science, contentDescription = null, modifier = Modifier.size(16.dp))
                    Spacer(modifier = Modifier.width(4.dp))
                    Text("Assess", style = MaterialTheme.typography.labelMedium)
                }
                Button(
                    onClick = { /* Get pricing */ },
                    modifier = Modifier.weight(1f)
                ) {
                    Icon(Icons.Filled.TrendingUp, contentDescription = null, modifier = Modifier.size(16.dp))
                    Spacer(modifier = Modifier.width(4.dp))
                    Text("Price", style = MaterialTheme.typography.labelMedium)
                }
            }
        }
    }
}

@Composable
fun InfoChip(
    icon: androidx.compose.ui.graphics.vector.ImageVector,
    label: String
) {
    Row(verticalAlignment = Alignment.CenterVertically) {
        Icon(
            icon,
            contentDescription = null,
            modifier = Modifier.size(14.dp),
            tint = MaterialTheme.colorScheme.onSurfaceVariant
        )
        Spacer(modifier = Modifier.width(4.dp))
        Text(
            label,
            style = MaterialTheme.typography.labelSmall,
            color = MaterialTheme.colorScheme.onSurfaceVariant
        )
    }
}

@Composable
fun EmptyProduceState() {
    Card(
        modifier = Modifier
            .fillMaxWidth()
            .padding(32.dp),
        colors = CardDefaults.cardColors(
            containerColor = MaterialTheme.colorScheme.surfaceVariant
        )
    ) {
        Column(
            modifier = Modifier
                .padding(32.dp)
                .fillMaxWidth(),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            Icon(
                Icons.Filled.Inventory,
                contentDescription = null,
                modifier = Modifier.size(64.dp),
                tint = MaterialTheme.colorScheme.onSurfaceVariant.copy(alpha = 0.5f)
            )
            Spacer(modifier = Modifier.height(16.dp))
            Text(
                "No produce added yet",
                style = MaterialTheme.typography.titleMedium
            )
            Text(
                "कोई फसल नहीं जोड़ी गई",
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.onSurfaceVariant
            )
            Spacer(modifier = Modifier.height(8.dp))
            Text(
                "Tap + to add your first produce batch",
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant
            )
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun AddProduceDialog(
    onDismiss: () -> Unit,
    onAdd: (ProduceItem) -> Unit
) {
    val crops = listOf(
        "Tomato" to "टमाटर", "Potato" to "आलू", "Onion" to "प्याज",
        "Rice" to "चावल", "Wheat" to "गेहूं", "Mango" to "आम",
        "Banana" to "केला", "Apple" to "सेब", "Cauliflower" to "फूलगोभी",
        "Spinach" to "पालक", "Okra" to "भिंडी", "Brinjal" to "बैंगन",
        "Green Chili" to "हरी मिर्च", "Grapes" to "अंगूर",
        "Pomegranate" to "अनार", "Guava" to "अमरूद"
    )

    var selectedCrop by remember { mutableStateOf(crops[0]) }
    var quantity by remember { mutableStateOf("") }
    var location by remember { mutableStateOf("") }
    var expanded by remember { mutableStateOf(false) }

    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text("Add Produce / फसल जोड़ें") },
        text = {
            Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
                // Crop selector
                ExposedDropdownMenuBox(
                    expanded = expanded,
                    onExpandedChange = { expanded = !expanded }
                ) {
                    OutlinedTextField(
                        value = "${selectedCrop.first} / ${selectedCrop.second}",
                        onValueChange = {},
                        readOnly = true,
                        label = { Text("Crop / फसल") },
                        trailingIcon = { ExposedDropdownMenuDefaults.TrailingIcon(expanded) },
                        modifier = Modifier
                            .fillMaxWidth()
                            .menuAnchor()
                    )
                    ExposedDropdownMenu(
                        expanded = expanded,
                        onDismissRequest = { expanded = false }
                    ) {
                        crops.forEach { crop ->
                            DropdownMenuItem(
                                text = { Text("${crop.first} / ${crop.second}") },
                                onClick = {
                                    selectedCrop = crop
                                    expanded = false
                                }
                            )
                        }
                    }
                }

                OutlinedTextField(
                    value = quantity,
                    onValueChange = { quantity = it },
                    label = { Text("Quantity (kg) / मात्रा") },
                    modifier = Modifier.fillMaxWidth()
                )

                OutlinedTextField(
                    value = location,
                    onValueChange = { location = it },
                    label = { Text("Location / स्थान") },
                    modifier = Modifier.fillMaxWidth()
                )
            }
        },
        confirmButton = {
            Button(
                onClick = {
                    val qty = quantity.toDoubleOrNull() ?: 0.0
                    if (qty > 0) {
                        onAdd(
                            ProduceItem(
                                id = System.currentTimeMillis().toString(),
                                cropName = selectedCrop.first,
                                cropNameHindi = selectedCrop.second,
                                quantity = qty,
                                location = location
                            )
                        )
                    }
                }
            ) {
                Text("Add / जोड़ें")
            }
        },
        dismissButton = {
            TextButton(onClick = onDismiss) {
                Text("Cancel / रद्द")
            }
        }
    )
}

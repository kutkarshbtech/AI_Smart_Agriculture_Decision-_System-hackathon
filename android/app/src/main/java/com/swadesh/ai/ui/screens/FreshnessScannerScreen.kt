package com.swadesh.ai.ui.screens

import android.Manifest
import android.content.pm.PackageManager
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.net.Uri
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.Image
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.asImageBitmap
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.core.content.ContextCompat
import androidx.lifecycle.viewmodel.compose.viewModel
import com.swadesh.ai.ui.viewmodels.FreshnessScannerViewModel

/**
 * Freshness Scanner screen — capture or pick a fruit photo and get
 * real-time freshness/quality assessment from the MobileNetV2 model.
 */

// Result data class for display
data class FreshnessResult(
    val freshnessStatus: String = "",       // "fresh" or "rotten"
    val confidence: Float = 0f,
    val qualityGrade: String = "",          // excellent/good/average/poor
    val freshnessScore: Int = 0,
    val damageScore: Int = 0,
    val cropType: String = "",
    val hindiLabel: String = "",
    val ripeness: String = "",
    val defects: List<String> = emptyList(),
    val summary: String = "",
    val recommendationEn: String = "",
    val recommendationHi: String = "",
    val urgency: String = "",
    val modelType: String = "",
    val inferenceTimeMs: Float = 0f,
    val topPredictions: List<Prediction> = emptyList()
)

data class Prediction(
    val className: String,
    val confidence: Float,
    val hindi: String
)

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun FreshnessScannerScreen(
    viewModel: FreshnessScannerViewModel = viewModel()
) {
    val context = LocalContext.current
    var capturedImageBitmap by remember { mutableStateOf<Bitmap?>(null) }
    var selectedCrop by remember { mutableStateOf("tomato") }
    var showCropSelector by remember { mutableStateOf(false) }

    val uiState by viewModel.uiState.collectAsState()

    // Supported crops (matches ULNN Food Freshness Dataset — 13 categories)
    val crops = listOf(
        "apple" to "सेब",
        "banana" to "केला",
        "bell_pepper" to "शिमला मिर्च",
        "bitter_gourd" to "करेला",
        "capsicum" to "शिमला मिर्च",
        "carrot" to "गाजर",
        "cucumber" to "खीरा",
        "mango" to "आम",
        "okra" to "भिंडी",
        "orange" to "संतरा",
        "potato" to "आलू",
        "strawberry" to "स्ट्रॉबेरी",
        "tomato" to "टमाटर"
    )

    // Camera permission
    var hasCameraPermission by remember {
        mutableStateOf(
            ContextCompat.checkSelfPermission(context, Manifest.permission.CAMERA) ==
                    PackageManager.PERMISSION_GRANTED
        )
    }

    val permissionLauncher = rememberLauncherForActivityResult(
        ActivityResultContracts.RequestPermission()
    ) { isGranted ->
        hasCameraPermission = isGranted
    }

    // Camera launcher
    val cameraLauncher = rememberLauncherForActivityResult(
        ActivityResultContracts.TakePicturePreview()
    ) { bitmap ->
        if (bitmap != null) {
            capturedImageBitmap = bitmap
            viewModel.clearResult()
        }
    }

    // Gallery launcher
    val galleryLauncher = rememberLauncherForActivityResult(
        ActivityResultContracts.GetContent()
    ) { uri ->
        uri?.let {
            try {
                val inputStream = context.contentResolver.openInputStream(it)
                val bitmap = BitmapFactory.decodeStream(inputStream)
                capturedImageBitmap = bitmap
                viewModel.clearResult()
                inputStream?.close()
            } catch (e: Exception) {
                // Handle error
            }
        }
    }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
            .padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp)
    ) {
        // Header
        Text(
            "🔬 Freshness Scanner / ताज़गी स्कैनर",
            style = MaterialTheme.typography.headlineSmall,
            fontWeight = FontWeight.Bold
        )
        Text(
            "Take a photo of your fruit to check its freshness\n" +
                    "अपनी फसल की ताज़गी जांचने के लिए फोटो लें",
            style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant
        )

        // Crop selector
        Card(
            modifier = Modifier.fillMaxWidth(),
            colors = CardDefaults.cardColors(
                containerColor = MaterialTheme.colorScheme.surfaceVariant
            )
        ) {
            Row(
                modifier = Modifier
                    .padding(16.dp)
                    .fillMaxWidth(),
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.SpaceBetween
            ) {
                Text("Select crop / फसल चुनें:", style = MaterialTheme.typography.bodyMedium)
                AssistChip(
                    onClick = { showCropSelector = !showCropSelector },
                    label = {
                        val display = crops.find { it.first == selectedCrop }
                        Text("${display?.first ?: selectedCrop} / ${display?.second ?: ""}")
                    },
                    leadingIcon = {
                        Icon(Icons.Filled.ArrowDropDown, contentDescription = null)
                    }
                )
            }
            if (showCropSelector) {
                Column(modifier = Modifier.padding(horizontal = 16.dp, vertical = 4.dp)) {
                    crops.forEach { (name, hindi) ->
                        TextButton(
                            onClick = {
                                selectedCrop = name
                                showCropSelector = false
                            },
                            modifier = Modifier.fillMaxWidth()
                        ) {
                            Text(
                                "$name / $hindi",
                                style = MaterialTheme.typography.bodyMedium,
                                modifier = Modifier.fillMaxWidth()
                            )
                        }
                    }
                }
            }
        }

        // Image capture area
        Card(
            modifier = Modifier
                .fillMaxWidth()
                .heightIn(min = 250.dp),
            shape = RoundedCornerShape(16.dp)
        ) {
            if (capturedImageBitmap != null) {
                Box(modifier = Modifier.fillMaxWidth()) {
                    Image(
                        bitmap = capturedImageBitmap!!.asImageBitmap(),
                        contentDescription = "Captured produce",
                        modifier = Modifier
                            .fillMaxWidth()
                            .heightIn(min = 250.dp, max = 350.dp)
                            .clip(RoundedCornerShape(16.dp)),
                        contentScale = ContentScale.Crop
                    )
                    // Re-capture button
                    IconButton(
                        onClick = {
                            capturedImageBitmap = null
                            viewModel.clearResult()
                        },
                        modifier = Modifier
                            .align(Alignment.TopEnd)
                            .padding(8.dp)
                    ) {
                        Icon(
                            Icons.Filled.Close,
                            contentDescription = "Remove",
                            tint = MaterialTheme.colorScheme.onSurface
                        )
                    }
                }
            } else {
                // Empty state — prompt to capture
                Column(
                    modifier = Modifier
                        .fillMaxWidth()
                        .heightIn(min = 250.dp)
                        .padding(32.dp),
                    horizontalAlignment = Alignment.CenterHorizontally,
                    verticalArrangement = Arrangement.Center
                ) {
                    Icon(
                        Icons.Filled.CameraAlt,
                        contentDescription = null,
                        modifier = Modifier.size(64.dp),
                        tint = MaterialTheme.colorScheme.onSurfaceVariant.copy(alpha = 0.4f)
                    )
                    Spacer(modifier = Modifier.height(16.dp))
                    Text(
                        "Take a photo or select from gallery\n" +
                                "फोटो लें या गैलरी से चुनें",
                        style = MaterialTheme.typography.bodyMedium,
                        textAlign = TextAlign.Center,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                }
            }
        }

        // Capture buttons
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            OutlinedButton(
                onClick = {
                    if (hasCameraPermission) {
                        cameraLauncher.launch(null)
                    } else {
                        permissionLauncher.launch(Manifest.permission.CAMERA)
                    }
                },
                modifier = Modifier.weight(1f)
            ) {
                Icon(Icons.Filled.CameraAlt, contentDescription = null)
                Spacer(modifier = Modifier.width(8.dp))
                Text("Camera\nकैमरा", textAlign = TextAlign.Center)
            }
            OutlinedButton(
                onClick = { galleryLauncher.launch("image/*") },
                modifier = Modifier.weight(1f)
            ) {
                Icon(Icons.Filled.PhotoLibrary, contentDescription = null)
                Spacer(modifier = Modifier.width(8.dp))
                Text("Gallery\nगैलरी", textAlign = TextAlign.Center)
            }
        }

        // Analyze button
        Button(
            onClick = {
                capturedImageBitmap?.let { bitmap ->
                    viewModel.analyzeFreshness(bitmap, selectedCrop)
                }
            },
            enabled = capturedImageBitmap != null && !uiState.isAnalyzing,
            modifier = Modifier
                .fillMaxWidth()
                .height(56.dp),
            shape = RoundedCornerShape(16.dp)
        ) {
            if (uiState.isAnalyzing) {
                CircularProgressIndicator(
                    modifier = Modifier.size(24.dp),
                    color = MaterialTheme.colorScheme.onPrimary,
                    strokeWidth = 2.dp
                )
                Spacer(modifier = Modifier.width(12.dp))
                Text("Analyzing... / विश्लेषण हो रहा है...")
            } else {
                Icon(Icons.Filled.Science, contentDescription = null)
                Spacer(modifier = Modifier.width(12.dp))
                Text(
                    "Analyze Freshness / ताज़गी जांचें",
                    style = MaterialTheme.typography.titleMedium
                )
            }
        }

        // Error message (offline mode notice)
        uiState.error?.let { errorMsg ->
            Card(
                modifier = Modifier.fillMaxWidth(),
                colors = CardDefaults.cardColors(
                    containerColor = MaterialTheme.colorScheme.tertiaryContainer
                )
            ) {
                Row(
                    modifier = Modifier.padding(12.dp),
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Icon(
                        Icons.Filled.WifiOff,
                        contentDescription = null,
                        modifier = Modifier.size(20.dp),
                        tint = MaterialTheme.colorScheme.onTertiaryContainer
                    )
                    Spacer(modifier = Modifier.width(8.dp))
                    Text(
                        errorMsg,
                        style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.onTertiaryContainer
                    )
                }
            }
        }

        // Model status indicator
        uiState.modelStatus?.let { status ->
            Text(
                "Model: ${status.modelType} • ${status.numClasses} classes",
                style = MaterialTheme.typography.labelSmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant.copy(alpha = 0.6f)
            )
        }

        // Results section
        uiState.result?.let { res ->
            FreshnessResultCard(res)
        }
    }
}


@Composable
fun FreshnessResultCard(result: FreshnessResult) {
    val isFresh = result.freshnessStatus == "fresh"
    val statusColor = if (isFresh)
        MaterialTheme.colorScheme.primary
    else
        MaterialTheme.colorScheme.error

    Card(
        modifier = Modifier.fillMaxWidth(),
        colors = CardDefaults.cardColors(
            containerColor = if (isFresh)
                MaterialTheme.colorScheme.primaryContainer
            else
                MaterialTheme.colorScheme.errorContainer
        ),
        shape = RoundedCornerShape(16.dp)
    ) {
        Column(modifier = Modifier.padding(20.dp)) {
            // Status header
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Column {
                    Text(
                        if (isFresh) "🟢 FRESH / ताज़ा" else "🔴 NOT FRESH / ताज़ा नहीं",
                        style = MaterialTheme.typography.titleLarge,
                        fontWeight = FontWeight.Bold,
                        color = statusColor
                    )
                    Text(
                        "${result.cropType} / ${result.hindiLabel}",
                        style = MaterialTheme.typography.bodyMedium
                    )
                }
                Text(
                    "${(result.confidence * 100).toInt()}%",
                    style = MaterialTheme.typography.headlineMedium,
                    fontWeight = FontWeight.Bold,
                    color = statusColor
                )
            }

            Spacer(modifier = Modifier.height(16.dp))
            HorizontalDivider()
            Spacer(modifier = Modifier.height(16.dp))

            // Metrics row
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceEvenly
            ) {
                MetricItem("Grade", result.qualityGrade.uppercase())
                MetricItem("Score", "${result.freshnessScore}/100")
                MetricItem("Ripeness", result.ripeness)
                MetricItem("Damage", "${result.damageScore}%")
            }

            // Defects
            if (result.defects.isNotEmpty()) {
                Spacer(modifier = Modifier.height(12.dp))
                Text(
                    "⚠️ Issues: ${result.defects.joinToString(", ")}",
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.error
                )
            }

            // Recommendations
            Spacer(modifier = Modifier.height(16.dp))
            Card(
                colors = CardDefaults.cardColors(
                    containerColor = MaterialTheme.colorScheme.surface.copy(alpha = 0.7f)
                )
            ) {
                Column(modifier = Modifier.padding(12.dp)) {
                    Text(
                        "💡 Recommendation / सुझाव",
                        style = MaterialTheme.typography.titleSmall,
                        fontWeight = FontWeight.Bold
                    )
                    Spacer(modifier = Modifier.height(8.dp))
                    Text(
                        result.recommendationEn,
                        style = MaterialTheme.typography.bodySmall
                    )
                    Spacer(modifier = Modifier.height(4.dp))
                    Text(
                        result.recommendationHi,
                        style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                    Spacer(modifier = Modifier.height(8.dp))
                    AssistChip(
                        onClick = {},
                        label = {
                            Text(
                                "Urgency: ${result.urgency.uppercase()}",
                                style = MaterialTheme.typography.labelSmall
                            )
                        },
                        colors = AssistChipDefaults.assistChipColors(
                            containerColor = when (result.urgency) {
                                "critical" -> MaterialTheme.colorScheme.error.copy(alpha = 0.15f)
                                "high" -> MaterialTheme.colorScheme.tertiary.copy(alpha = 0.15f)
                                else -> MaterialTheme.colorScheme.primary.copy(alpha = 0.15f)
                            }
                        )
                    )
                }
            }

            // Model info
            Spacer(modifier = Modifier.height(8.dp))
            Text(
                "Model: ${result.modelType} • ${result.inferenceTimeMs}ms",
                style = MaterialTheme.typography.labelSmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant.copy(alpha = 0.5f)
            )

            // Top predictions
            if (result.topPredictions.isNotEmpty()) {
                Spacer(modifier = Modifier.height(8.dp))
                Text(
                    "All predictions:",
                    style = MaterialTheme.typography.labelSmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
                result.topPredictions.take(3).forEach { pred ->
                    Text(
                        "  ${pred.className}: ${(pred.confidence * 100).toInt()}% — ${pred.hindi}",
                        style = MaterialTheme.typography.labelSmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant.copy(alpha = 0.7f)
                    )
                }
            }
        }
    }
}


@Composable
fun MetricItem(label: String, value: String) {
    Column(horizontalAlignment = Alignment.CenterHorizontally) {
        Text(
            value,
            style = MaterialTheme.typography.titleSmall,
            fontWeight = FontWeight.Bold
        )
        Text(
            label,
            style = MaterialTheme.typography.labelSmall,
            color = MaterialTheme.colorScheme.onSurfaceVariant
        )
    }
}


// Simulation moved to FreshnessScannerViewModel

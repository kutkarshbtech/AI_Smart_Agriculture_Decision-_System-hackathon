package com.swadesh.ai.ui.screens

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.*
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.swadesh.ai.data.model.UserType
import com.swadesh.ai.ui.viewmodel.AuthViewModel
import com.swadesh.ai.ui.viewmodel.AuthState

/**
 * Registration Screen for new users
 * Different fields for Buyer, Seller, and Logistic user types
 */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun RegisterScreen(
    viewModel: AuthViewModel,
    onBack: () -> Unit,
    onRegisterSuccess: () -> Unit
) {
    var mobileNumber by remember { mutableStateOf("") }
    var name by remember { mutableStateOf("") }
    var selectedUserType by remember { mutableStateOf(UserType.SELLER) }
    var showUserTypeDialog by remember { mutableStateOf(false) }
    
    // Common fields
    var city by remember { mutableStateOf("") }
    var state by remember { mutableStateOf("") }
    var pincode by remember { mutableStateOf("") }
    
    // Buyer/Logistic fields
    var businessName by remember { mutableStateOf("") }
    
    // Seller fields
    var village by remember { mutableStateOf("") }
    var district by remember { mutableStateOf("") }
    
    // Logistic fields
    var vehicleTypes by remember { mutableStateOf("") }  // Comma-separated
    var operatingStates by remember { mutableStateOf("") }  // Comma-separated
    
    val authState by viewModel.authState.collectAsState()
    
    // Handle successful registration
    LaunchedEffect(authState) {
        if (authState is AuthState.RegistrationSuccess) {
            onRegisterSuccess()
            viewModel.resetAuthState()
        }
    }
    
    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Register") },
                navigationIcon = {
                    IconButton(onClick = onBack) {
                        Icon(Icons.Default.ArrowBack, "Back")
                    }
                }
            )
        }
    ) { padding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
                .padding(24.dp)
                .verticalScroll(rememberScrollState()),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            // Title
            Text(
                text = "Create Account",
                style = MaterialTheme.typography.headlineMedium,
                fontWeight = FontWeight.Bold
            )
            
            Spacer(modifier = Modifier.height(8.dp))
            
            Text(
                text = "Fill in your details to get started",
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.onSurfaceVariant
            )
            
            Spacer(modifier = Modifier.height(32.dp))
            
            // User Type Selection
            OutlinedCard(
                modifier = Modifier.fillMaxWidth(),
                onClick = { showUserTypeDialog = true }
            ) {
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(16.dp),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Column {
                        Text(
                            text = "I am a...",
                            style = MaterialTheme.typography.bodySmall,
                            color = MaterialTheme.colorScheme.onSurfaceVariant
                        )
                        Text(
                            text = selectedUserType.displayName(),
                            style = MaterialTheme.typography.bodyLarge,
                            fontWeight = FontWeight.Medium
                        )
                    }
                    Icon(
                        imageVector = Icons.Default.ArrowDropDown,
                        contentDescription = "Select"
                    )
                }
            }
            
            Spacer(modifier = Modifier.height(16.dp))
            
            // Mobile Number
            OutlinedTextField(
                value = mobileNumber,
                onValueChange = { mobileNumber = it },
                label = { Text("Mobile Number *") },
                placeholder = { Text("+91 9876543210") },
                leadingIcon = { Icon(Icons.Default.Phone, "Phone") },
                keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Phone),
                singleLine = true,
                modifier = Modifier.fillMaxWidth()
            )
            
            Spacer(modifier = Modifier.height(12.dp))
            
            // Name
            OutlinedTextField(
                value = name,
                onValueChange = { name = it },
                label = { Text("Full Name *") },
                leadingIcon = { Icon(Icons.Default.Person, "Name") },
                singleLine = true,
                modifier = Modifier.fillMaxWidth()
            )
            
            // Conditional fields based on user type
            when (selectedUserType) {
                UserType.BUYER -> {
                    Spacer(modifier = Modifier.height(12.dp))
                    OutlinedTextField(
                        value = businessName,
                        onValueChange = { businessName = it },
                        label = { Text("Business Name") },
                        leadingIcon = { Icon(Icons.Default.Business, "Business") },
                        singleLine = true,
                        modifier = Modifier.fillMaxWidth()
                    )
                }
                
                UserType.SELLER -> {
                    Spacer(modifier = Modifier.height(12.dp))
                    OutlinedTextField(
                        value = village,
                        onValueChange = { village = it },
                        label = { Text("Village") },
                        leadingIcon = { Icon(Icons.Default.Home, "Village") },
                        singleLine = true,
                        modifier = Modifier.fillMaxWidth()
                    )
                    
                    Spacer(modifier = Modifier.height(12.dp))
                    OutlinedTextField(
                        value = district,
                        onValueChange = { district = it },
                        label = { Text("District") },
                        leadingIcon = { Icon(Icons.Default.LocationCity, "District") },
                        singleLine = true,
                        modifier = Modifier.fillMaxWidth()
                    )
                }
                
                UserType.LOGISTIC -> {
                    Spacer(modifier = Modifier.height(12.dp))
                    OutlinedTextField(
                        value = businessName,
                        onValueChange = { businessName = it },
                        label = { Text("Business Name") },
                        leadingIcon = { Icon(Icons.Default.Business, "Business") },
                        singleLine = true,
                        modifier = Modifier.fillMaxWidth()
                    )
                    
                    Spacer(modifier = Modifier.height(12.dp))
                    OutlinedTextField(
                        value = vehicleTypes,
                        onValueChange = { vehicleTypes = it },
                        label = { Text("Vehicle Types (comma-separated") },
                        placeholder = { Text("Truck, Tempo, Mini-truck") },
                        leadingIcon = { Icon(Icons.Default.LocalShipping, "Vehicle") },
                        modifier = Modifier.fillMaxWidth()
                    )
                    
                    Spacer(modifier = Modifier.height(12.dp))
                    OutlinedTextField(
                        value = operatingStates,
                        onValueChange = { operatingStates = it },
                        label = { Text("Operating States (comma-separated)") },
                        placeholder = { Text("Maharashtra, Gujarat") },
                        leadingIcon = { Icon(Icons.Default.Map, "States") },
                        modifier = Modifier.fillMaxWidth()
                    )
                }
            }
            
            // Common location fields
            Spacer(modifier = Modifier.height(12.dp))
            OutlinedTextField(
                value = city,
                onValueChange = { city = it },
                label = { Text("City") },
                leadingIcon = { Icon(Icons.Default.LocationOn, "City") },
                singleLine = true,
                modifier = Modifier.fillMaxWidth()
            )
            
            Spacer(modifier = Modifier.height(12.dp))
            OutlinedTextField(
                value = state,
                onValueChange = { state = it },
                label = { Text("State") },
                leadingIcon = { Icon(Icons.Default.Map, "State") },
                singleLine = true,
                modifier = Modifier.fillMaxWidth()
            )
            
            Spacer(modifier = Modifier.height(12.dp))
            OutlinedTextField(
                value = pincode,
                onValueChange = { if (it.length <= 6) pincode = it },
                label = { Text("Pincode") },
                leadingIcon = { Icon(Icons.Default.PinDrop, "Pincode") },
                keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
                singleLine = true,
                modifier = Modifier.fillMaxWidth()
            )
            
            Spacer(modifier = Modifier.height(24.dp))
            
            // Register Button
            Button(
                onClick = {
                    if (mobileNumber.isNotBlank() && name.isNotBlank()) {
                        viewModel.register(
                            mobileNumber = mobileNumber.trim(),
                            userType = selectedUserType,
                            name = name.trim(),
                            businessName = businessName.takeIf { it.isNotBlank() },
                            vehicleTypes = vehicleTypes.takeIf { it.isNotBlank() }
                                ?.split(",")?.map { it.trim() },
                            operatingStates = operatingStates.takeIf { it.isNotBlank() }
                                ?.split(",")?.map { it.trim() },
                            city = city.takeIf { it.isNotBlank() },
                            state = state.takeIf { it.isNotBlank() },
                            pincode = pincode.takeIf { it.isNotBlank() },
                            village = village.takeIf { it.isNotBlank() },
                            district = district.takeIf { it.isNotBlank() }
                        )
                    }
                },
                enabled = mobileNumber.isNotBlank() && name.isNotBlank() && authState !is AuthState.Loading,
                modifier = Modifier
                    .fillMaxWidth()
                    .height(56.dp),
                shape = RoundedCornerShape(12.dp)
            ) {
                if (authState is AuthState.Loading) {
                    CircularProgressIndicator(
                        modifier = Modifier.size(24.dp),
                        color = MaterialTheme.colorScheme.onPrimary
                    )
                } else {
                    Text("Register", fontSize = 16.sp, fontWeight = FontWeight.Bold)
                }
            }
            
            Spacer(modifier = Modifier.height(16.dp))
            
            // Error/Success Message
            when (authState) {
                is AuthState.Error -> {
                    Card(
                        colors = CardDefaults.cardColors(
                            containerColor = MaterialTheme.colorScheme.errorContainer
                        ),
                        modifier = Modifier.fillMaxWidth()
                    ) {
                        Text(
                            text = (authState as AuthState.Error).message,
                            modifier = Modifier.padding(16.dp),
                            color = MaterialTheme.colorScheme.onErrorContainer
                        )
                    }
                }
                is AuthState.RegistrationSuccess -> {
                    Card(
                        colors = CardDefaults.cardColors(
                            containerColor = MaterialTheme.colorScheme.primaryContainer
                        ),
                        modifier = Modifier.fillMaxWidth()
                    ) {
                        Column(modifier = Modifier.padding(16.dp)) {
                            Text(
                                text = "✓ Registration Successful!",
                                fontWeight = FontWeight.Bold,
                                color = MaterialTheme.colorScheme.primary
                            )
                            Text(
                                text = "Redirecting to login...",
                                style = MaterialTheme.typography.bodySmall,
                                color = MaterialTheme.colorScheme.onPrimaryContainer
                            )
                        }
                    }
                }
                else -> Unit
            }
            
            Spacer(modifier = Modifier.height(32.dp))
        }
    }
    
    // User Type Selection Dialog
    if (showUserTypeDialog) {
        AlertDialog(
            onDismissRequest = { showUserTypeDialog = false },
            title = { Text("Select User Type") },
            text = {
                Column {
                    UserType.values().forEach { type ->
                        Row(
                            modifier = Modifier
                                .fillMaxWidth()
                                .padding(vertical = 8.dp),
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            RadioButton(
                                selected = selectedUserType == type,
                                onClick = {
                                    selectedUserType = type
                                    showUserTypeDialog = false
                                }
                            )
                            Spacer(modifier = Modifier.width(8.dp))
                            Column {
                                Text(
                                    text = type.displayName(),
                                    style = MaterialTheme.typography.bodyLarge
                                )
                                Text(
                                    text = when (type) {
                                        UserType.BUYER -> "I purchase agricultural produce"
                                        UserType.SELLER -> "I am a farmer/seller"
                                        UserType.LOGISTIC -> "I provide transportation services"
                                    },
                                    style = MaterialTheme.typography.bodySmall,
                                    color = MaterialTheme.colorScheme.onSurfaceVariant
                                )
                            }
                        }
                    }
                }
            },
            confirmButton = {
                TextButton(onClick = { showUserTypeDialog = false }) {
                    Text("Close")
                }
            }
        )
    }
}

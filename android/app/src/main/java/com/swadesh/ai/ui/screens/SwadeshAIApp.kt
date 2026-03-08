package com.swadesh.ai.ui.screens

import androidx.compose.foundation.layout.*
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material.icons.outlined.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.navigation.NavDestination.Companion.hierarchy
import androidx.navigation.NavGraph.Companion.findStartDestination
import androidx.navigation.compose.*

/**
 * Main app composable with bottom navigation.
 */

sealed class Screen(val route: String, val title: String, val icon: @Composable () -> Unit) {
    data object Dashboard : Screen("dashboard", "Home", { Icon(Icons.Filled.Dashboard, contentDescription = "Dashboard") })
    data object Produce : Screen("produce", "My Produce", { Icon(Icons.Filled.Inventory, contentDescription = "Produce") })
    data object Scanner : Screen("scanner", "Scan", { Icon(Icons.Filled.CameraAlt, contentDescription = "Freshness Scanner") })
    data object Prices : Screen("prices", "Prices", { Icon(Icons.Filled.TrendingUp, contentDescription = "Prices") })
    data object Buyers : Screen("buyers", "Buyers", { Icon(Icons.Filled.Store, contentDescription = "Buyers") })
    data object Chat : Screen("chat", "Ask AI", { Icon(Icons.Filled.Chat, contentDescription = "Chat") })
}

val bottomNavItems = listOf(
    Screen.Dashboard,
    Screen.Produce,
    Screen.Scanner,
    Screen.Prices,
    Screen.Chat,
)

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun SwadeshAIApp() {
    val navController = rememberNavController()

    Scaffold(
        topBar = {
            CenterAlignedTopAppBar(
                title = {
                    Text("SwadeshAI", style = MaterialTheme.typography.titleLarge)
                },
                colors = TopAppBarDefaults.centerAlignedTopAppBarColors(
                    containerColor = MaterialTheme.colorScheme.primaryContainer,
                    titleContentColor = MaterialTheme.colorScheme.onPrimaryContainer,
                ),
                actions = {
                    IconButton(onClick = { /* TODO: notifications */ }) {
                        Icon(Icons.Outlined.Notifications, contentDescription = "Alerts")
                    }
                }
            )
        },
        bottomBar = {
            NavigationBar {
                val navBackStackEntry by navController.currentBackStackEntryAsState()
                val currentDestination = navBackStackEntry?.destination

                bottomNavItems.forEach { screen ->
                    NavigationBarItem(
                        icon = screen.icon,
                        label = { Text(screen.title) },
                        selected = currentDestination?.hierarchy?.any { it.route == screen.route } == true,
                        onClick = {
                            navController.navigate(screen.route) {
                                popUpTo(navController.graph.findStartDestination().id) {
                                    saveState = true
                                }
                                launchSingleTop = true
                                restoreState = true
                            }
                        }
                    )
                }
            }
        }
    ) { innerPadding ->
        NavHost(
            navController = navController,
            startDestination = Screen.Dashboard.route,
            modifier = Modifier.padding(innerPadding)
        ) {
            composable(Screen.Dashboard.route) { DashboardScreen() }
            composable(Screen.Produce.route) { ProduceScreen() }
            composable(Screen.Scanner.route) { FreshnessScannerScreen() }
            composable(Screen.Prices.route) { PricesScreen() }
            composable(Screen.Buyers.route) { BuyersScreen() }
            composable(Screen.Chat.route) { ChatScreen() }
        }
    }
}

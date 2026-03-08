package com.swadesh.ai.data.repository

import android.content.Context
import androidx.datastore.core.DataStore
import androidx.datastore .preferences.core.Preferences
import androidx.datastore.preferences.core.edit
import androidx.datastore.preferences.core.stringPreferencesKey
import androidx.datastore.preferences.preferencesDataStore
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map

/**
 * Token management using DataStore
 * Stores authentication token and user info locally
 */

private val Context.dataStore: DataStore<Preferences> by preferencesDataStore(name = "auth_prefs")

class AuthRepository(private val context: Context) {
    
    companion object {
        private val TOKEN_KEY = stringPreferencesKey("auth_token")
        private val USER_ID_KEY = stringPreferencesKey("user_id")
        private val USER_TYPE_KEY = stringPreferencesKey("user_type")
        private val USER_NAME_KEY = stringPreferencesKey("user_name")
        private val MOBILE_KEY = stringPreferencesKey("mobile_number")
    }
    
    // Save authentication data
    suspend fun saveAuthData(
        token: String,
        userId: Int,
        userType: String,
        name: String,
        mobileNumber: String
    ) {
        context.dataStore.edit { prefs ->
            prefs[TOKEN_KEY] = token
            prefs[USER_ID_KEY] = userId.toString()
            prefs[USER_TYPE_KEY] = userType
            prefs[USER_NAME_KEY] = name
            prefs[MOBILE_KEY] = mobileNumber
        }
    }
    
    // Get token
    val authToken: Flow<String?> = context.dataStore.data.map { prefs ->
        prefs[TOKEN_KEY]
    }
    
    // Get user ID
    val userId: Flow<Int?> = context.dataStore.data.map { prefs ->
        prefs[USER_ID_KEY]?.toIntOrNull()
    }
    
    // Get user type
    val userType: Flow<String?> = context.dataStore.data.map { prefs ->
        prefs[USER_TYPE_KEY]
    }
    
    // Get user name
    val userName: Flow<String?> = context.dataStore.data.map { prefs ->
        prefs[USER_NAME_KEY]
    }
    
    // Get mobile number
    val mobileNumber: Flow<String?> = context.dataStore.data.map { prefs ->
        prefs[MOBILE_KEY]
    }
    
    // Check if user is logged in
    val isLoggedIn: Flow<Boolean> = context.dataStore.data.map { prefs ->
        prefs[TOKEN_KEY] != null
    }
    
    // Clear all auth data (logout)
    suspend fun clearAuthData() {
        context.dataStore.edit { prefs ->
            prefs.clear()
        }
    }
    
    // Get bearer token for API calls
    suspend fun getBearerToken(): String? {
        var token: String? = null
        context.dataStore.data.collect { prefs ->
            token = prefs[TOKEN_KEY]
        }
        return token?.let { "Bearer $it" }
    }
}

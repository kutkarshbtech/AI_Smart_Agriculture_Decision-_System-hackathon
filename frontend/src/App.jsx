import { useState } from 'react'
import { BrowserRouter as Router, Routes, Route, NavLink, Navigate } from 'react-router-dom'
import {
  Sprout, TrendingUp, Store, Users, Info, LogOut, User, Cloud, FlaskConical,
  Truck, MessageCircle, LayoutDashboard, ShieldAlert, Bell, BarChart3,
} from 'lucide-react'
import { AuthProvider, useAuth } from './context/AuthContext'
import Login from './components/Login'
import Register from './components/Register'
import QualityAssessment from './components/QualityAssessment'
import MandiPrices from './components/MandiPrices'
import BuyerMatching from './components/BuyerMatching'
import WeatherForecast from './components/WeatherForecast'
import CausalAnalysis from './components/CausalAnalysis'
import LogisticsPlanner from './components/LogisticsPlanner'
import Chatbot from './components/Chatbot'
import DashboardSummary from './components/DashboardSummary'
import SpoilageAssessment from './components/SpoilageAssessment'
import AlertsPanel from './components/AlertsPanel'
import PriceForecast from './components/PriceForecast'
import About from './components/About'
import ProduceForm from './components/ProduceForm'

// Protected Route Component
const ProtectedRoute = ({ children }) => {
  const { isAuthenticated, loading } = useAuth();
  
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-green-50 to-blue-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-green-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading...</p>
        </div>
      </div>
    );
  }
  
  return isAuthenticated ? children : <Navigate to="/login" />;
};

// Main App Content
function AppContent() {
  const { isAuthenticated, user, logout } = useAuth();
  const [produceData, setProduceData] = useState({
    cropName: 'tomato',
    quantity: 100,
    location: 'Pune, Maharashtra',
    latitude: 18.5204,
    longitude: 73.8567,
  })

  const getUserIcon = (userType) => {
    const icons = {
      buyer: '🛒',
      seller: '🌾',
      logistic: '🚚'
    };
    return icons[userType] || '👤';
  };

  return (
    <Router>
      <div className="min-h-screen bg-gradient-to-br from-green-50 to-blue-50">
        {/* Header */}
        <header className="bg-gradient-to-r from-primary-700 via-primary-600 to-accent-500 text-white shadow-lg">
          <div className="container mx-auto px-4 py-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <Sprout className="w-10 h-10" />
                <div>
                  <h1 className="text-3xl font-bold">SwadeshAI</h1>
                  <p className="text-green-100 text-sm">Farm-to-Market Intelligence Platform</p>
                </div>
              </div>
              <div className="flex items-center gap-6">
                {isAuthenticated && user ? (
                  <>
                    <div className="text-right">
                      <div className="flex items-center gap-2 text-sm">
                        <span>{getUserIcon(user.user_type)}</span>
                        <span className="font-semibold">{user.name}</span>
                      </div>
                      <p className="text-xs opacity-75">{user.user_type} • {user.mobile_number}</p>
                    </div>
                    <button
                      onClick={() => logout()}
                      className="flex items-center gap-2 px-4 py-2 bg-white/20 hover:bg-white/30 rounded-lg transition-colors"
                    >
                      <LogOut className="w-4 h-4" />
                      <span className="text-sm">Logout</span>
                    </button>
                  </>
                ) : (
                  <div className="text-right">
                    <p className="text-sm opacity-90">Powered by AWS AI</p>
                    <p className="text-xs opacity-75">Reducing Post-Harvest Losses</p>
                  </div>
                )}
              </div>
            </div>
          </div>
        </header>

        {/* Navigation - Only show if authenticated */}
        {isAuthenticated && (
          <div className="container mx-auto px-4">
            <div className="flex space-x-1 overflow-x-auto">
              <NavLink
                to="/"
                className={({ isActive }) =>
                  `flex items-center space-x-2 px-4 py-3 font-medium transition-colors whitespace-nowrap ${
                    isActive
                      ? 'text-primary-700 border-b-2 border-primary-700'
                      : 'text-gray-600 hover:text-primary-600'
                  }`
                }
              >
                <Sprout className="w-5 h-5" />
                <span>Quality Assessment</span>
              </NavLink>
              <NavLink
                to="/mandi-prices"
                className={({ isActive }) =>
                  `flex items-center space-x-2 px-4 py-3 font-medium transition-colors whitespace-nowrap ${
                    isActive
                      ? 'text-primary-700 border-b-2 border-primary-700'
                      : 'text-gray-600 hover:text-primary-600'
                  }`
                }
              >
                <Store className="w-5 h-5" />
                <span>Mandi Prices</span>
              </NavLink>
              <NavLink
                to="/find-buyers"
                className={({ isActive }) =>
                  `flex items-center space-x-2 px-4 py-3 font-medium transition-colors whitespace-nowrap ${
                    isActive
                      ? 'text-primary-700 border-b-2 border-primary-700'
                      : 'text-gray-600 hover:text-primary-600'
                  }`
                }
              >
                <Users className="w-5 h-5" />
                <span>Find Buyers</span>
              </NavLink>
              <NavLink
                to="/weather"
                className={({ isActive }) =>
                  `flex items-center space-x-2 px-4 py-3 font-medium transition-colors whitespace-nowrap ${
                    isActive
                      ? 'text-primary-700 border-b-2 border-primary-700'
                      : 'text-gray-600 hover:text-primary-600'
                  }`
                }
              >
                <Cloud className="w-5 h-5" />
                <span>Weather Forecast</span>
              </NavLink>
              <NavLink
                to="/causal"
                className={({ isActive }) =>
                  `flex items-center space-x-2 px-4 py-3 font-medium transition-colors whitespace-nowrap ${
                    isActive
                      ? 'text-primary-700 border-b-2 border-primary-700'
                      : 'text-gray-600 hover:text-primary-600'
                  }`
                }
              >
                <FlaskConical className="w-5 h-5" />
                <span>Causal Analysis</span>
              </NavLink>
              <NavLink
                to="/logistics"
                className={({ isActive }) =>
                  `flex items-center space-x-2 px-4 py-3 font-medium transition-colors whitespace-nowrap ${
                    isActive
                      ? 'text-primary-700 border-b-2 border-primary-700'
                      : 'text-gray-600 hover:text-primary-600'
                  }`
                }
              >
                <Truck className="w-5 h-5" />
                <span>Logistics</span>
              </NavLink>
              <NavLink
                to="/price-forecast"
                className={({ isActive }) =>
                  `flex items-center space-x-2 px-4 py-3 font-medium transition-colors whitespace-nowrap ${
                    isActive
                      ? 'text-primary-700 border-b-2 border-primary-700'
                      : 'text-gray-600 hover:text-primary-600'
                  }`
                }
              >
                <BarChart3 className="w-5 h-5" />
                <span>Price Forecast</span>
              </NavLink>
              <NavLink
                to="/spoilage"
                className={({ isActive }) =>
                  `flex items-center space-x-2 px-4 py-3 font-medium transition-colors whitespace-nowrap ${
                    isActive
                      ? 'text-primary-700 border-b-2 border-primary-700'
                      : 'text-gray-600 hover:text-primary-600'
                  }`
                }
              >
                <ShieldAlert className="w-5 h-5" />
                <span>Spoilage</span>
              </NavLink>
              <NavLink
                to="/chatbot"
                className={({ isActive }) =>
                  `flex items-center space-x-2 px-4 py-3 font-medium transition-colors whitespace-nowrap ${
                    isActive
                      ? 'text-primary-700 border-b-2 border-primary-700'
                      : 'text-gray-600 hover:text-primary-600'
                  }`
                }
              >
                <MessageCircle className="w-5 h-5" />
                <span>AI Chat</span>
              </NavLink>
              <NavLink
                to="/dashboard"
                className={({ isActive }) =>
                  `flex items-center space-x-2 px-4 py-3 font-medium transition-colors whitespace-nowrap ${
                    isActive
                      ? 'text-primary-700 border-b-2 border-primary-700'
                      : 'text-gray-600 hover:text-primary-600'
                  }`
                }
              >
                <LayoutDashboard className="w-5 h-5" />
                <span>Dashboard</span>
              </NavLink>
              <NavLink
                to="/alerts"
                className={({ isActive }) =>
                  `flex items-center space-x-2 px-4 py-3 font-medium transition-colors whitespace-nowrap ${
                    isActive
                      ? 'text-primary-700 border-b-2 border-primary-700'
                      : 'text-gray-600 hover:text-primary-600'
                  }`
                }
              >
                <Bell className="w-5 h-5" />
                <span>Alerts</span>
              </NavLink>
              <NavLink
                to="/about"
                className={({ isActive }) =>
                  `flex items-center space-x-2 px-4 py-3 font-medium transition-colors whitespace-nowrap ${
                    isActive
                      ? 'text-primary-700 border-b-2 border-primary-700'
                      : 'text-gray-600 hover:text-primary-600'
                  }`
                }
              >
                <Info className="w-5 h-5" />
                <span>About</span>
              </NavLink>
            </div>
          </div>
        )}

        {/* Main Content */}
        <Routes>
          {/* Public Routes */}
          <Route path="/login" element={
            isAuthenticated ? <Navigate to="/" /> : <Login />
          } />
          <Route path="/register" element={
            isAuthenticated ? <Navigate to="/" /> : <Register />
          } />

          {/* Protected Routes */}
          <Route path="/" element={
            <ProtectedRoute>
              <div className="container mx-auto px-4 py-6">
                <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
                  <aside className="lg:col-span-1">
                    <ProduceForm produceData={produceData} setProduceData={setProduceData} />
                  </aside>
                  <main className="lg:col-span-3">
                    <QualityAssessment produceData={produceData} />
                  </main>
                </div>
              </div>
            </ProtectedRoute>
          } />
          <Route path="/mandi-prices" element={
            <ProtectedRoute>
              <div className="container mx-auto px-4 py-6">
                <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
                  <aside className="lg:col-span-1">
                    <ProduceForm produceData={produceData} setProduceData={setProduceData} />
                  </aside>
                  <main className="lg:col-span-3">
                    <MandiPrices produceData={produceData} />
                  </main>
                </div>
              </div>
            </ProtectedRoute>
          } />
          <Route path="/find-buyers" element={
            <ProtectedRoute>
              <div className="container mx-auto px-4 py-6">
                <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
                  <aside className="lg:col-span-1">
                    <ProduceForm produceData={produceData} setProduceData={setProduceData} />
                  </aside>
                  <main className="lg:col-span-3">
                    <BuyerMatching produceData={produceData} />
                  </main>
                </div>
              </div>
            </ProtectedRoute>
          } />
          <Route path="/weather" element={
            <ProtectedRoute>
              <div className="container mx-auto px-4 py-6">
                <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
                  <aside className="lg:col-span-1">
                    <ProduceForm produceData={produceData} setProduceData={setProduceData} />
                  </aside>
                  <main className="lg:col-span-3">
                    <WeatherForecast produceData={produceData} />
                  </main>
                </div>
              </div>
            </ProtectedRoute>
          } />
          <Route path="/causal" element={
            <ProtectedRoute>
              <div className="container mx-auto px-4 py-6">
                <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
                  <aside className="lg:col-span-1">
                    <ProduceForm produceData={produceData} setProduceData={setProduceData} />
                  </aside>
                  <main className="lg:col-span-3">
                    <CausalAnalysis produceData={produceData} />
                  </main>
                </div>
              </div>
            </ProtectedRoute>
          } />
          <Route path="/logistics" element={
            <ProtectedRoute>
              <div className="container mx-auto px-4 py-6">
                <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
                  <aside className="lg:col-span-1">
                    <ProduceForm produceData={produceData} setProduceData={setProduceData} />
                  </aside>
                  <main className="lg:col-span-3">
                    <LogisticsPlanner produceData={produceData} />
                  </main>
                </div>
              </div>
            </ProtectedRoute>
          } />
          <Route path="/price-forecast" element={
            <ProtectedRoute>
              <div className="container mx-auto px-4 py-6">
                <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
                  <aside className="lg:col-span-1">
                    <ProduceForm produceData={produceData} setProduceData={setProduceData} />
                  </aside>
                  <main className="lg:col-span-3">
                    <PriceForecast produceData={produceData} />
                  </main>
                </div>
              </div>
            </ProtectedRoute>
          } />
          <Route path="/spoilage" element={
            <ProtectedRoute>
              <div className="container mx-auto px-4 py-6">
                <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
                  <aside className="lg:col-span-1">
                    <ProduceForm produceData={produceData} setProduceData={setProduceData} />
                  </aside>
                  <main className="lg:col-span-3">
                    <SpoilageAssessment produceData={produceData} />
                  </main>
                </div>
              </div>
            </ProtectedRoute>
          } />
          <Route path="/chatbot" element={
            <ProtectedRoute>
              <div className="container mx-auto px-4 py-6">
                <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
                  <aside className="lg:col-span-1">
                    <ProduceForm produceData={produceData} setProduceData={setProduceData} />
                  </aside>
                  <main className="lg:col-span-3">
                    <Chatbot produceData={produceData} />
                  </main>
                </div>
              </div>
            </ProtectedRoute>
          } />
          <Route path="/dashboard" element={
            <ProtectedRoute>
              <div className="container mx-auto px-4 py-6">
                <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
                  <aside className="lg:col-span-1">
                    <ProduceForm produceData={produceData} setProduceData={setProduceData} />
                  </aside>
                  <main className="lg:col-span-3">
                    <DashboardSummary produceData={produceData} />
                  </main>
                </div>
              </div>
            </ProtectedRoute>
          } />
          <Route path="/alerts" element={
            <ProtectedRoute>
              <div className="container mx-auto px-4 py-6">
                <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
                  <aside className="lg:col-span-1">
                    <ProduceForm produceData={produceData} setProduceData={setProduceData} />
                  </aside>
                  <main className="lg:col-span-3">
                    <AlertsPanel produceData={produceData} />
                  </main>
                </div>
              </div>
            </ProtectedRoute>
          } />
          <Route path="/about" element={
            <ProtectedRoute>
              <div className="container mx-auto px-4 py-6">
                <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
                  <aside className="lg:col-span-1">
                    <ProduceForm produceData={produceData} setProduceData={setProduceData} />
                  </aside>
                  <main className="lg:col-span-3">
                    <About />
                  </main>
                </div>
              </div>
            </ProtectedRoute>
          } />
        </Routes>

        {/* Footer */}
        {isAuthenticated && (
        <footer className="bg-gray-800 text-white mt-12">
          <div className="container mx-auto px-4 py-6">
            <div className="text-center">
              <p className="text-sm">
                &copy; 2026 SwadeshAI - AWS AI for Bharat Hackathon | Reducing ₹92,651 Cr Annual Post-Harvest Losses
              </p>
              <p className="text-xs text-gray-400 mt-2">
                Powered by AWS Bedrock, SageMaker, and Rekognition
              </p>
            </div>
          </div>
        </footer>
        )}
      </div>
    </Router>
  )
}

// Main App Component with AuthProvider
function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
}

export default App

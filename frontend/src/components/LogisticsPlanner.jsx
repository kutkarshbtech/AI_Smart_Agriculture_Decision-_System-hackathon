import { useState, useEffect, useCallback } from 'react'
import axios from 'axios'
import { Truck, MapPin, Package, Clock, IndianRupee, Star, Phone, ChevronRight } from 'lucide-react'
import SpeakButton from './SpeakButton'

// Approximate road distances (km) between major Indian cities
const CITY_DISTANCES = {
  'Mumbai, Maharashtra':   { 'Mumbai, Maharashtra': 0, 'Delhi': 1400, 'Bengaluru, Karnataka': 980, 'Chennai, Tamil Nadu': 1340, 'Kolkata, West Bengal': 2050, 'Hyderabad, Telangana': 710, 'Pune, Maharashtra': 150, 'Ahmedabad, Gujarat': 530, 'Jaipur, Rajasthan': 1150, 'Lucknow, Uttar Pradesh': 1350, 'Surat, Gujarat': 290, 'Nagpur, Maharashtra': 840, 'Indore, Madhya Pradesh': 590, 'Patna, Bihar': 1680, 'Chandigarh': 1600, 'Kochi, Kerala': 1350 },
  'Delhi':                 { 'Mumbai, Maharashtra': 1400, 'Delhi': 0, 'Bengaluru, Karnataka': 2150, 'Chennai, Tamil Nadu': 2200, 'Kolkata, West Bengal': 1500, 'Hyderabad, Telangana': 1550, 'Pune, Maharashtra': 1430, 'Ahmedabad, Gujarat': 940, 'Jaipur, Rajasthan': 280, 'Lucknow, Uttar Pradesh': 550, 'Surat, Gujarat': 1180, 'Nagpur, Maharashtra': 1100, 'Indore, Madhya Pradesh': 810, 'Patna, Bihar': 1000, 'Chandigarh': 250, 'Kochi, Kerala': 2700 },
  'Bengaluru, Karnataka':  { 'Mumbai, Maharashtra': 980, 'Delhi': 2150, 'Bengaluru, Karnataka': 0, 'Chennai, Tamil Nadu': 350, 'Kolkata, West Bengal': 1870, 'Hyderabad, Telangana': 570, 'Pune, Maharashtra': 840, 'Ahmedabad, Gujarat': 1500, 'Jaipur, Rajasthan': 1900, 'Lucknow, Uttar Pradesh': 2050, 'Surat, Gujarat': 1200, 'Nagpur, Maharashtra': 1050, 'Indore, Madhya Pradesh': 1300, 'Patna, Bihar': 2100, 'Chandigarh': 2400, 'Kochi, Kerala': 530 },
  'Chennai, Tamil Nadu':   { 'Mumbai, Maharashtra': 1340, 'Delhi': 2200, 'Bengaluru, Karnataka': 350, 'Chennai, Tamil Nadu': 0, 'Kolkata, West Bengal': 1660, 'Hyderabad, Telangana': 630, 'Pune, Maharashtra': 1170, 'Ahmedabad, Gujarat': 1770, 'Jaipur, Rajasthan': 2100, 'Lucknow, Uttar Pradesh': 2100, 'Surat, Gujarat': 1500, 'Nagpur, Maharashtra': 1200, 'Indore, Madhya Pradesh': 1560, 'Patna, Bihar': 1870, 'Chandigarh': 2400, 'Kochi, Kerala': 700 },
  'Kolkata, West Bengal':  { 'Mumbai, Maharashtra': 2050, 'Delhi': 1500, 'Bengaluru, Karnataka': 1870, 'Chennai, Tamil Nadu': 1660, 'Kolkata, West Bengal': 0, 'Hyderabad, Telangana': 1490, 'Pune, Maharashtra': 1880, 'Ahmedabad, Gujarat': 1930, 'Jaipur, Rajasthan': 1500, 'Lucknow, Uttar Pradesh': 990, 'Surat, Gujarat': 1900, 'Nagpur, Maharashtra': 1100, 'Indore, Madhya Pradesh': 1400, 'Patna, Bihar': 570, 'Chandigarh': 1560, 'Kochi, Kerala': 2350 },
  'Hyderabad, Telangana':  { 'Mumbai, Maharashtra': 710, 'Delhi': 1550, 'Bengaluru, Karnataka': 570, 'Chennai, Tamil Nadu': 630, 'Kolkata, West Bengal': 1490, 'Hyderabad, Telangana': 0, 'Pune, Maharashtra': 560, 'Ahmedabad, Gujarat': 1100, 'Jaipur, Rajasthan': 1360, 'Lucknow, Uttar Pradesh': 1350, 'Surat, Gujarat': 910, 'Nagpur, Maharashtra': 500, 'Indore, Madhya Pradesh': 850, 'Patna, Bihar': 1560, 'Chandigarh': 1750, 'Kochi, Kerala': 1100 },
  'Pune, Maharashtra':     { 'Mumbai, Maharashtra': 150, 'Delhi': 1430, 'Bengaluru, Karnataka': 840, 'Chennai, Tamil Nadu': 1170, 'Kolkata, West Bengal': 1880, 'Hyderabad, Telangana': 560, 'Pune, Maharashtra': 0, 'Ahmedabad, Gujarat': 660, 'Jaipur, Rajasthan': 1200, 'Lucknow, Uttar Pradesh': 1350, 'Surat, Gujarat': 420, 'Nagpur, Maharashtra': 700, 'Indore, Madhya Pradesh': 600, 'Patna, Bihar': 1700, 'Chandigarh': 1650, 'Kochi, Kerala': 1200 },
  'Ahmedabad, Gujarat':    { 'Mumbai, Maharashtra': 530, 'Delhi': 940, 'Bengaluru, Karnataka': 1500, 'Chennai, Tamil Nadu': 1770, 'Kolkata, West Bengal': 1930, 'Hyderabad, Telangana': 1100, 'Pune, Maharashtra': 660, 'Ahmedabad, Gujarat': 0, 'Jaipur, Rajasthan': 670, 'Lucknow, Uttar Pradesh': 1000, 'Surat, Gujarat': 270, 'Nagpur, Maharashtra': 860, 'Indore, Madhya Pradesh': 400, 'Patna, Bihar': 1510, 'Chandigarh': 1180, 'Kochi, Kerala': 1870 },
  'Jaipur, Rajasthan':     { 'Mumbai, Maharashtra': 1150, 'Delhi': 280, 'Bengaluru, Karnataka': 1900, 'Chennai, Tamil Nadu': 2100, 'Kolkata, West Bengal': 1500, 'Hyderabad, Telangana': 1360, 'Pune, Maharashtra': 1200, 'Ahmedabad, Gujarat': 670, 'Jaipur, Rajasthan': 0, 'Lucknow, Uttar Pradesh': 580, 'Surat, Gujarat': 920, 'Nagpur, Maharashtra': 970, 'Indore, Madhya Pradesh': 590, 'Patna, Bihar': 1100, 'Chandigarh': 510, 'Kochi, Kerala': 2450 },
  'Lucknow, Uttar Pradesh':{ 'Mumbai, Maharashtra': 1350, 'Delhi': 550, 'Bengaluru, Karnataka': 2050, 'Chennai, Tamil Nadu': 2100, 'Kolkata, West Bengal': 990, 'Hyderabad, Telangana': 1350, 'Pune, Maharashtra': 1350, 'Ahmedabad, Gujarat': 1000, 'Jaipur, Rajasthan': 580, 'Lucknow, Uttar Pradesh': 0, 'Surat, Gujarat': 1200, 'Nagpur, Maharashtra': 900, 'Indore, Madhya Pradesh': 700, 'Patna, Bihar': 530, 'Chandigarh': 700, 'Kochi, Kerala': 2550 },
  'Surat, Gujarat':        { 'Mumbai, Maharashtra': 290, 'Delhi': 1180, 'Bengaluru, Karnataka': 1200, 'Chennai, Tamil Nadu': 1500, 'Kolkata, West Bengal': 1900, 'Hyderabad, Telangana': 910, 'Pune, Maharashtra': 420, 'Ahmedabad, Gujarat': 270, 'Jaipur, Rajasthan': 920, 'Lucknow, Uttar Pradesh': 1200, 'Surat, Gujarat': 0, 'Nagpur, Maharashtra': 780, 'Indore, Madhya Pradesh': 430, 'Patna, Bihar': 1620, 'Chandigarh': 1400, 'Kochi, Kerala': 1600 },
  'Nagpur, Maharashtra':   { 'Mumbai, Maharashtra': 840, 'Delhi': 1100, 'Bengaluru, Karnataka': 1050, 'Chennai, Tamil Nadu': 1200, 'Kolkata, West Bengal': 1100, 'Hyderabad, Telangana': 500, 'Pune, Maharashtra': 700, 'Ahmedabad, Gujarat': 860, 'Jaipur, Rajasthan': 970, 'Lucknow, Uttar Pradesh': 900, 'Surat, Gujarat': 780, 'Nagpur, Maharashtra': 0, 'Indore, Madhya Pradesh': 470, 'Patna, Bihar': 980, 'Chandigarh': 1250, 'Kochi, Kerala': 1540 },
  'Indore, Madhya Pradesh': { 'Mumbai, Maharashtra': 590, 'Delhi': 810, 'Bengaluru, Karnataka': 1300, 'Chennai, Tamil Nadu': 1560, 'Kolkata, West Bengal': 1400, 'Hyderabad, Telangana': 850, 'Pune, Maharashtra': 600, 'Ahmedabad, Gujarat': 400, 'Jaipur, Rajasthan': 590, 'Lucknow, Uttar Pradesh': 700, 'Surat, Gujarat': 430, 'Nagpur, Maharashtra': 470, 'Indore, Madhya Pradesh': 0, 'Patna, Bihar': 1250, 'Chandigarh': 1040, 'Kochi, Kerala': 1850 },
  'Patna, Bihar':          { 'Mumbai, Maharashtra': 1680, 'Delhi': 1000, 'Bengaluru, Karnataka': 2100, 'Chennai, Tamil Nadu': 1870, 'Kolkata, West Bengal': 570, 'Hyderabad, Telangana': 1560, 'Pune, Maharashtra': 1700, 'Ahmedabad, Gujarat': 1510, 'Jaipur, Rajasthan': 1100, 'Lucknow, Uttar Pradesh': 530, 'Surat, Gujarat': 1620, 'Nagpur, Maharashtra': 980, 'Indore, Madhya Pradesh': 1250, 'Patna, Bihar': 0, 'Chandigarh': 1200, 'Kochi, Kerala': 2500 },
  'Chandigarh':            { 'Mumbai, Maharashtra': 1600, 'Delhi': 250, 'Bengaluru, Karnataka': 2400, 'Chennai, Tamil Nadu': 2400, 'Kolkata, West Bengal': 1560, 'Hyderabad, Telangana': 1750, 'Pune, Maharashtra': 1650, 'Ahmedabad, Gujarat': 1180, 'Jaipur, Rajasthan': 510, 'Lucknow, Uttar Pradesh': 700, 'Surat, Gujarat': 1400, 'Nagpur, Maharashtra': 1250, 'Indore, Madhya Pradesh': 1040, 'Patna, Bihar': 1200, 'Chandigarh': 0, 'Kochi, Kerala': 2900 },
  'Kochi, Kerala':         { 'Mumbai, Maharashtra': 1350, 'Delhi': 2700, 'Bengaluru, Karnataka': 530, 'Chennai, Tamil Nadu': 700, 'Kolkata, West Bengal': 2350, 'Hyderabad, Telangana': 1100, 'Pune, Maharashtra': 1200, 'Ahmedabad, Gujarat': 1870, 'Jaipur, Rajasthan': 2450, 'Lucknow, Uttar Pradesh': 2550, 'Surat, Gujarat': 1600, 'Nagpur, Maharashtra': 1540, 'Indore, Madhya Pradesh': 1850, 'Patna, Bihar': 2500, 'Chandigarh': 2900, 'Kochi, Kerala': 0 },
}

function lookupDistance(source, destination) {
  // Direct lookup
  if (CITY_DISTANCES[source]?.[destination] !== undefined) {
    return CITY_DISTANCES[source][destination]
  }
  // Try matching by first part of the string (city name)
  const srcKey = Object.keys(CITY_DISTANCES).find(k => k.split(',')[0].trim() === source.split(',')[0].trim())
  const destKey = srcKey ? Object.keys(CITY_DISTANCES[srcKey] || {}).find(k => k.split(',')[0].trim() === destination.split(',')[0].trim()) : null
  if (srcKey && destKey && CITY_DISTANCES[srcKey][destKey] !== undefined) {
    return CITY_DISTANCES[srcKey][destKey]
  }
  return null // unknown pair
}

export default function LogisticsPlanner({ produceData }) {
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [buyerLocation, setBuyerLocation] = useState('Mumbai, Maharashtra')
  const [distance, setDistance] = useState(150)
  const [urgency, setUrgency] = useState('medium')

  const buyerCities = [
    'Mumbai, Maharashtra', 'Delhi', 'Bengaluru, Karnataka', 'Chennai, Tamil Nadu',
    'Kolkata, West Bengal', 'Hyderabad, Telangana', 'Pune, Maharashtra',
    'Ahmedabad, Gujarat', 'Jaipur, Rajasthan', 'Lucknow, Uttar Pradesh',
    'Surat, Gujarat', 'Nagpur, Maharashtra', 'Indore, Madhya Pradesh',
    'Patna, Bihar', 'Chandigarh', 'Kochi, Kerala',
  ]

  // Auto-update distance whenever source or destination city changes
  const updateDistance = useCallback((source, destination) => {
    const d = lookupDistance(source, destination)
    if (d !== null) setDistance(d)
  }, [])

  useEffect(() => {
    updateDistance(produceData.location, buyerLocation)
    setResult(null) // clear stale results
  }, [produceData.location, buyerLocation, updateDistance])

  const getRecommendation = async () => {
    setLoading(true)
    try {
      const response = await axios.get('/api/v1/logistics/complete', {
        params: {
          seller_location: produceData.location,
          buyer_location: buyerLocation,
          distance_km: distance,
          quantity_kg: produceData.quantity,
          crop_name: produceData.cropName,
          urgency,
        },
      })

      if (response.data.success) {
        setResult(response.data)
      } else {
        throw new Error(response.data.error || 'Failed to get recommendation')
      }
    } catch (error) {
      console.error('Logistics recommendation failed:', error)
      alert('Failed to get logistics recommendation. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const urgencyColors = {
    low: 'bg-green-100 text-green-800 border-green-300',
    medium: 'bg-yellow-100 text-yellow-800 border-yellow-300',
    high: 'bg-red-100 text-red-800 border-red-300',
  }

  return (
    <div className="space-y-6">
      {/* Header & Form */}
      <div className="card">
        <div className="flex items-center gap-3 mb-6">
          <Truck className="w-8 h-8 text-blue-600" />
          <div>
            <h2 className="text-2xl font-bold text-gray-800">Logistics Planner</h2>
            <p className="text-gray-600 text-sm">AI-powered transport recommendation and cost estimation</p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
          {/* Seller Location (from ProduceForm) */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              <MapPin className="w-4 h-4 inline mr-1" />
              From (Seller)
            </label>
            <input
              type="text"
              className="input-field bg-gray-50"
              value={produceData.location}
              disabled
            />
          </div>

          {/* Buyer Location */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              <MapPin className="w-4 h-4 inline mr-1" />
              To (Buyer)
            </label>
            <select
              className="input-field"
              value={buyerLocation}
              onChange={(e) => setBuyerLocation(e.target.value)}
            >
              {buyerCities.map((city) => (
                <option key={city} value={city}>{city}</option>
              ))}
            </select>
          </div>

          {/* Distance */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Distance (km)
            </label>
            <input
              type="number"
              className="input-field"
              value={distance}
              onChange={(e) => setDistance(parseInt(e.target.value) || 0)}
              min="1"
              max="3000"
            />
          </div>

          {/* Urgency */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              <Clock className="w-4 h-4 inline mr-1" />
              Urgency
            </label>
            <select
              className="input-field"
              value={urgency}
              onChange={(e) => setUrgency(e.target.value)}
            >
              <option value="low">Low — Flexible timing</option>
              <option value="medium">Medium — Within 1-2 days</option>
              <option value="high">High — Urgent / Same day</option>
            </select>
          </div>
        </div>

        {/* Summary Bar */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 mb-4 flex flex-wrap items-center gap-4 text-sm">
          <span className="font-semibold text-blue-900">
            <Package className="w-4 h-4 inline mr-1" />
            {produceData.quantity} kg {produceData.cropName}
          </span>
          <ChevronRight className="w-4 h-4 text-blue-400" />
          <span className="text-blue-800">{produceData.location}</span>
          <ChevronRight className="w-4 h-4 text-blue-400" />
          <span className="text-blue-800">{buyerLocation}</span>
          <span className={`ml-auto badge ${urgencyColors[urgency]} border px-3 py-1 rounded-full text-xs font-semibold`}>
            {urgency.toUpperCase()} URGENCY
          </span>
        </div>

        <button
          onClick={getRecommendation}
          disabled={loading}
          className="w-full btn-primary py-3 text-lg"
        >
          {loading ? (
            <span className="flex items-center justify-center">
              <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              Finding best transport...
            </span>
          ) : (
            '🚚 Get Transport Recommendation'
          )}
        </button>
      </div>

      {/* Results */}
      {result && (
        <div className="space-y-6">
          {/* Voice Summary */}
          <div className="flex justify-end">
            <SpeakButton
              text={(() => {
                const vr = result.vehicle_recommendation?.primary_recommendation
                const cb = result.cost_breakdown
                const ri = result.route_info
                let t = `Logistics recommendation for ${produceData.quantity} kg ${produceData.cropName} from ${produceData.location} to ${buyerLocation}. `
                if (vr) t += `Recommended vehicle: ${vr.vehicle_name || vr.vehicle_type}. Estimated cost: ${vr.estimated_cost} rupees. Estimated time: ${vr.estimated_time_hours?.toFixed(1)} hours. Capacity utilization: ${vr.capacity_utilization} percent. `
                if (cb) t += `Total cost breakdown: ${cb.total_estimated} rupees including transport, loading and tolls. `
                if (ri) t += `Route distance: ${ri.distance_km} km. Travel time: ${ri.estimated_travel_time_hours?.toFixed(1)} hours. `
                if (ri?.estimated_delivery) t += `Estimated delivery: ${ri.estimated_delivery}. `
                if (result.vehicle_recommendation?.alternatives?.length > 0) t += `Alternatives: ${result.vehicle_recommendation.alternatives.map(a => a.vehicle_name).join(', ')}.`
                return t
              })()}
              textHindi={(() => {
                const vr = result.vehicle_recommendation?.primary_recommendation
                let t = `${produceData.quantity} किलो ${produceData.cropName} के लिए परिवहन सुझाव। `
                if (vr) t += `सुझावा वाहन: ${vr.vehicle_name || vr.vehicle_type}। अनुमानित लागत: ${vr.estimated_cost} रुपये। अनुमानित समय: ${vr.estimated_time_hours?.toFixed(1)} घंटे।`
                return t
              })()}
              label="Read Results"
              size="md"
            />
          </div>

          {/* Vehicle Recommendation */}
          {result.vehicle_recommendation?.primary_recommendation && (
            <div className="card">
              <h3 className="text-xl font-bold text-gray-800 mb-4 flex items-center gap-2">
                <Truck className="w-6 h-6 text-blue-600" />
                Recommended Vehicle
              </h3>
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-5">
                <div className="flex items-start justify-between mb-3">
                  <div>
                    <h4 className="text-lg font-bold text-blue-900">{result.vehicle_recommendation.primary_recommendation.vehicle_name || result.vehicle_recommendation.primary_recommendation.vehicle_type}</h4>
                    <p className="text-sm text-blue-700">{result.vehicle_recommendation.primary_recommendation.reasons?.[0] || 'Best match for your requirements'}</p>
                  </div>
                  <span className="badge-info">Score: {result.vehicle_recommendation.primary_recommendation.score}</span>
                </div>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mt-4">
                  <div className="bg-white p-3 rounded-lg text-center">
                    <p className="text-xs text-gray-500">Est. Cost</p>
                    <p className="text-lg font-bold text-gray-800">₹{result.vehicle_recommendation.primary_recommendation.estimated_cost?.toLocaleString('en-IN') || '—'}</p>
                  </div>
                  <div className="bg-white p-3 rounded-lg text-center">
                    <p className="text-xs text-gray-500">Est. Time</p>
                    <p className="text-lg font-bold text-gray-800">{result.vehicle_recommendation.primary_recommendation.estimated_time_hours?.toFixed(1) || '—'} hrs</p>
                  </div>
                  <div className="bg-white p-3 rounded-lg text-center">
                    <p className="text-xs text-gray-500">Capacity Used</p>
                    <p className="text-lg font-bold text-gray-800">{result.vehicle_recommendation.primary_recommendation.capacity_utilization || '—'}%</p>
                  </div>
                  <div className="bg-white p-3 rounded-lg text-center">
                    <p className="text-xs text-gray-500">Distance</p>
                    <p className="text-lg font-bold text-gray-800">{result.vehicle_recommendation.distance_km || '—'} km</p>
                  </div>
                </div>
                {/* Alternative vehicles */}
                {result.vehicle_recommendation.alternatives?.length > 0 && (
                  <div className="mt-4">
                    <p className="text-sm font-semibold text-blue-800 mb-2">Alternatives:</p>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                      {result.vehicle_recommendation.alternatives.map((alt, idx) => (
                        <div key={idx} className="bg-white p-3 rounded-lg border border-blue-100">
                          <p className="font-semibold text-gray-800 text-sm">{alt.vehicle_name}</p>
                          <p className="text-xs text-gray-600">₹{alt.estimated_cost?.toLocaleString('en-IN')} · {alt.estimated_time_hours?.toFixed(1)} hrs · {alt.capacity_utilization}% capacity</p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Cost Breakdown */}
          {result.cost_breakdown && (
            <div className="card">
              <h3 className="text-xl font-bold text-gray-800 mb-4 flex items-center gap-2">
                <IndianRupee className="w-6 h-6 text-green-600" />
                Cost Breakdown
              </h3>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                <div className="bg-gradient-to-br from-green-50 to-green-100 p-4 rounded-lg text-center">
                  <p className="text-sm text-gray-600">Total Cost</p>
                  <p className="text-2xl font-bold text-green-700">₹{result.cost_breakdown.total_estimated?.toLocaleString('en-IN') || '—'}</p>
                </div>
                <div className="bg-gray-50 p-4 rounded-lg text-center">
                  <p className="text-sm text-gray-600">Transport</p>
                  <p className="text-xl font-semibold text-gray-700">₹{result.cost_breakdown.transport_cost?.toLocaleString('en-IN') || '—'}</p>
                </div>
                <div className="bg-gray-50 p-4 rounded-lg text-center">
                  <p className="text-sm text-gray-600">Loading</p>
                  <p className="text-xl font-semibold text-gray-700">₹{result.cost_breakdown.loading_charges?.toLocaleString('en-IN') || '—'}</p>
                </div>
                <div className="bg-gray-50 p-4 rounded-lg text-center">
                  <p className="text-sm text-gray-600">Tolls (est.)</p>
                  <p className="text-xl font-semibold text-gray-700">₹{result.cost_breakdown.toll_estimated?.toLocaleString('en-IN') || '—'}</p>
                </div>
              </div>
            </div>
          )}

          {/* Route Info */}
          {result.route_info && (
            <div className="card">
              <h3 className="text-xl font-bold text-gray-800 mb-4 flex items-center gap-2">
                <MapPin className="w-6 h-6 text-orange-600" />
                Route Details
              </h3>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                <div className="bg-orange-50 p-4 rounded-lg text-center">
                  <p className="text-sm text-gray-600">Distance</p>
                  <p className="text-2xl font-bold text-orange-700">{result.route_info.distance_km} km</p>
                </div>
                <div className="bg-orange-50 p-4 rounded-lg text-center">
                  <p className="text-sm text-gray-600">Travel Time</p>
                  <p className="text-2xl font-bold text-orange-700">{result.route_info.estimated_travel_time_hours?.toFixed(1) || '—'} hrs</p>
                </div>
                <div className="bg-orange-50 p-4 rounded-lg text-center">
                  <p className="text-sm text-gray-600">Total Time (incl. loading)</p>
                  <p className="text-2xl font-bold text-orange-700">{result.route_info.estimated_total_time_hours?.toFixed(1) || '—'} hrs</p>
                </div>
              </div>
              {result.route_info.estimated_delivery && (
                <p className="mt-3 text-sm text-orange-800 text-center">
                  📅 Estimated Delivery: <span className="font-semibold">{result.route_info.estimated_delivery}</span>
                </p>
              )}
              <p className="mt-2 text-sm text-gray-500 text-center">
                {result.route_info.source} → {result.route_info.destination}
              </p>
            </div>
          )}

          {/* Logistics Providers */}
          {result.logistics_providers && result.logistics_providers.length > 0 && (
            <div className="card">
              <h3 className="text-xl font-bold text-gray-800 mb-4">📋 Available Logistics Providers</h3>
              <div className="space-y-3">
                {result.logistics_providers.map((provider, idx) => (
                  <div
                    key={idx}
                    className="bg-gray-50 p-4 rounded-lg border border-gray-200 hover:shadow-md transition-shadow"
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <h4 className="font-semibold text-gray-800">{provider.name}</h4>
                        <p className="text-sm text-gray-600 mt-1">{provider.service_type || 'Full-service logistics'}</p>
                        {provider.phone && (
                          <p className="text-sm text-gray-500 mt-1 flex items-center gap-1">
                            <Phone className="w-3 h-3" /> {provider.phone}
                          </p>
                        )}
                      </div>
                      <div className="text-right">
                        <div className="flex items-center gap-1 text-yellow-600">
                          <Star className="w-4 h-4 fill-current" />
                          <span className="font-semibold">{provider.rating?.toFixed(1) || '—'}</span>
                        </div>
                        {provider.price_range && (
                          <p className="text-sm text-green-600 font-semibold mt-1">{provider.price_range}</p>
                        )}
                      </div>
                    </div>
                    {provider.coverage && (
                      <div className="mt-2 flex flex-wrap gap-1">
                        {provider.coverage.map((area, i) => (
                          <span key={i} className="badge-info text-xs">{area}</span>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

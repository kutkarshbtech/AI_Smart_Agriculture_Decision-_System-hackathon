import { useState } from 'react'
import axios from 'axios'
import { Store, TrendingUp, MapPin, Search, Filter } from 'lucide-react'
import SpeakButton from './SpeakButton'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'

const indianStates = [
  'All States', 'Andhra Pradesh', 'Bihar', 'Chhattisgarh', 'Delhi',
  'Gujarat', 'Haryana', 'Karnataka', 'Kerala', 'Madhya Pradesh',
  'Maharashtra', 'Odisha', 'Punjab', 'Rajasthan', 'Tamil Nadu',
  'Telangana', 'Uttar Pradesh', 'West Bengal',
]

export default function MandiPrices({ produceData }) {
  const [loading, setLoading] = useState(false)
  const [prices, setPrices] = useState(null)
  const [selectedState, setSelectedState] = useState('Andhra Pradesh')

  const fetchMandiPrices = async () => {
    setLoading(true)
    
    try {
      const params = {}
      if (selectedState && selectedState !== 'All States') {
        params.state = selectedState
      }
      // Call backend API with optional state filter
      const response = await axios.get(`/api/v1/pricing/mandi/prices/${produceData.cropName}`, { params })
      setPrices(response.data.records || [])
      setLoading(false)
    } catch (error) {
      console.error('Failed to fetch mandi prices:', error)
      setLoading(false)
      alert('Failed to fetch mandi prices. Please try again.')
    }
  }

  const avgPrice = prices ? (prices.reduce((sum, p) => sum + p.modal_price_per_kg, 0) / prices.length).toFixed(2) : 0
  const minPrice = prices ? Math.min(...prices.map(p => p.min_price_per_kg)).toFixed(2) : 0
  const maxPrice = prices ? Math.max(...prices.map(p => p.max_price_per_kg)).toFixed(2) : 0
  const statesCount = prices ? new Set(prices.map(p => p.state)).size : 0

  return (
    <div className="space-y-6">
      <div className="card">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-2xl font-bold text-gray-800 flex items-center">
              <Store className="w-7 h-7 mr-2 text-primary-600" />
              Live Mandi Prices
            </h2>
            <p className="text-gray-600 mt-1">
              Real-time market prices from mandis across India
            </p>
          </div>
        </div>

        {/* State Filter + Fetch */}
        <div className="flex flex-col sm:flex-row items-stretch sm:items-end gap-3 mb-6">
          <div className="flex-1">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              <Filter className="w-4 h-4 inline mr-1" />
              Filter by State
            </label>
            <select
              className="input-field"
              value={selectedState}
              onChange={(e) => setSelectedState(e.target.value)}
            >
              {indianStates.map((state) => (
                <option key={state} value={state}>{state}</option>
              ))}
            </select>
          </div>
          <button
            onClick={fetchMandiPrices}
            disabled={loading}
            className="btn-primary flex items-center justify-center space-x-2 px-6 py-2.5"
          >
            {loading ? (
              <>
                <svg className="animate-spin h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                <span>Loading...</span>
              </>
            ) : (
              <>
                <Search className="w-5 h-5" />
                <span>Fetch Prices</span>
              </>
            )}
          </button>
        </div>

        {!prices && !loading && (
          <div className="text-center py-12 bg-gray-50 rounded-lg">
            <Store className="w-16 h-16 text-gray-300 mx-auto mb-4" />
            <p className="text-gray-500 mb-4">
              Click "Fetch Prices" to get latest mandi prices for {produceData.cropName}
            </p>
            <p className="text-sm text-gray-400">
              {selectedState && selectedState !== 'All States' ? `Filtering by ${selectedState}` : 'Showing all states'}
            </p>
          </div>
        )}

        {prices && (
          <>
            {/* Voice Summary */}
            <div className="flex justify-end mb-4">
              <SpeakButton
                text={prices.length > 0 ? `Mandi prices for ${produceData.cropName}${selectedState !== 'All States' ? ` in ${selectedState}` : ''}. ${prices.length} mandis found across ${statesCount} states. Average price: ${avgPrice} rupees per kg. Lowest price: ${minPrice} rupees per kg. Highest price: ${maxPrice} rupees per kg. Top market: ${prices[0]?.market} in ${prices[0]?.district}, ${prices[0]?.state} at ${prices[0]?.modal_price_per_kg} rupees per kg.` : `No mandi price data found for ${produceData.cropName}.`}
                textHindi={prices.length > 0 ? `${produceData.cropName} की मंडी कीमतें। ${prices.length} मंडियों से डेटा। औसत कीमत: ${avgPrice} रुपये प्रति किलो। न्यूनतम: ${minPrice} रुपये। अधिकतम: ${maxPrice} रुपये।` : `${produceData.cropName} के लिए कोई डेटा नहीं मिला।`}
                label="Read Prices"
                size="md"
              />
            </div>

            {/* Summary Metrics */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
              <div className="bg-gradient-to-br from-blue-50 to-blue-100 p-4 rounded-lg text-center">
                <p className="text-sm text-gray-600">Avg Price</p>
                <p className="text-2xl font-bold text-blue-700">₹{avgPrice}</p>
                <p className="text-xs text-gray-500">per kg</p>
              </div>
              <div className="bg-gradient-to-br from-green-50 to-green-100 p-4 rounded-lg text-center">
                <p className="text-sm text-gray-600">Lowest</p>
                <p className="text-2xl font-bold text-green-700">₹{minPrice}</p>
                <p className="text-xs text-gray-500">per kg</p>
              </div>
              <div className="bg-gradient-to-br from-orange-50 to-orange-100 p-4 rounded-lg text-center">
                <p className="text-sm text-gray-600">Highest</p>
                <p className="text-2xl font-bold text-orange-700">₹{maxPrice}</p>
                <p className="text-xs text-gray-500">per kg</p>
              </div>
              <div className="bg-gradient-to-br from-purple-50 to-purple-100 p-4 rounded-lg text-center">
                <p className="text-sm text-gray-600">States</p>
                <p className="text-2xl font-bold text-purple-700">{statesCount}</p>
                <p className="text-xs text-gray-500">covered</p>
              </div>
            </div>

            {/* Chart */}
            <div className="mb-6">
              <h3 className="text-lg font-semibold text-gray-800 mb-4">Price Comparison</h3>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={prices.slice(0, 10)}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="market" angle={-45} textAnchor="end" height={100} fontSize={12} />
                  <YAxis label={{ value: 'Price (₹/kg)', angle: -90, position: 'insideLeft' }} />
                  <Tooltip />
                  <Legend />
                  <Bar dataKey="modal_price_per_kg" fill="#22c55e" name="Modal Price" />
                  <Bar dataKey="min_price_per_kg" fill="#f59e0b" name="Min Price" />
                  <Bar dataKey="max_price_per_kg" fill="#ef4444" name="Max Price" />
                </BarChart>
              </ResponsiveContainer>
            </div>

            {/* Price Table */}
            <div>
              <h3 className="text-lg font-semibold text-gray-800 mb-4">Detailed Prices</h3>
              <div className="space-y-3">
                {prices.map((price, idx) => (
                  <div key={idx} className="bg-gray-50 p-4 rounded-lg border border-gray-200 hover:shadow-md transition-shadow">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <h4 className="font-semibold text-gray-800">{price.market}</h4>
                        <p className="text-sm text-gray-600 flex items-center mt-1">
                          <MapPin className="w-4 h-4 mr-1" />
                          {price.district}, {price.state}
                        </p>
                      </div>
                      <div className="text-right">
                        <p className="text-2xl font-bold text-green-600">₹{price.modal_price_per_kg}</p>
                        <p className="text-xs text-gray-500">per kg</p>
                      </div>
                    </div>
                    <div className="mt-3 flex items-center justify-between text-sm">
                      <div className="flex space-x-4">
                        <span className="text-gray-600">
                          Min: <span className="font-semibold">₹{price.min_price_per_kg}</span>
                        </span>
                        <span className="text-gray-600">
                          Max: <span className="font-semibold">₹{price.max_price_per_kg}</span>
                        </span>
                      </div>
                      <div className="flex space-x-4 text-gray-500">
                        <span>{price.variety}</span>
                        <span>{price.arrival_date}</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  )
}

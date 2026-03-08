import { useState } from 'react'
import axios from 'axios'
import { Users, Search, Star, MapPin, Phone, Truck, Clock, DollarSign, Package } from 'lucide-react'
import SpeakButton from './SpeakButton'

export default function BuyerMatching({ produceData }) {
  const [loading, setLoading] = useState(false)
  const [buyers, setBuyers] = useState(null)
  const [filters, setFilters] = useState({
    buyerType: 'all',
    minRating: 0,
    sortBy: 'score',
  })

  const findBuyers = async () => {
    setLoading(true)
    
    try {
      // Call /nearby endpoint (no batch_id required)
      const response = await axios.get('/api/v1/buyers/nearby', {
        params: {
          crop_name: produceData.cropName,
          lat: produceData.latitude || 28.6,
          lng: produceData.longitude || 77.2,
          quantity_kg: produceData.quantity || 100,
          max_distance_km: 100,
          buyer_type: filters.buyerType !== 'all' ? filters.buyerType : undefined,
          min_rating: filters.minRating > 0 ? filters.minRating : undefined,
          sort_by: filters.sortBy,
        },
      })
      
      setBuyers(response.data.matched_buyers || [])
      setLoading(false)
    } catch (error) {
      console.error('Failed to find buyers:', error)
      setLoading(false)
      alert('Failed to find buyers. Please try again.')
    }
  }

  const filteredBuyers = buyers?.filter(buyer => {
    if (filters.buyerType !== 'all' && buyer.buyer_type !== filters.buyerType) return false
    if (buyer.rating < filters.minRating) return false
    return true
  }).sort((a, b) => {
    if (filters.sortBy === 'score') return b.match_score - a.match_score
    if (filters.sortBy === 'distance') return a.distance_km - b.distance_km
    if (filters.sortBy === 'rating') return b.rating - a.rating
    return 0
  })

  const buyerTypeEmoji = {
    retailer: '🏪',
    wholesaler: '🏢',
    aggregator: '🏭',
  }

  return (
    <div className="space-y-6">
      <div className="card">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-2xl font-bold text-gray-800 flex items-center">
              <Users className="w-7 h-7 mr-2 text-primary-600" />
              Find Verified Buyers
            </h2>
            <p className="text-gray-600 mt-1">
              AI-powered geospatial matching connects you with verified buyers in your area
            </p>
          </div>
        </div>

        {/* Filters */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Buyer Type</label>
            <select
              className="input-field"
              value={filters.buyerType}
              onChange={(e) => setFilters({ ...filters, buyerType: e.target.value })}
            >
              <option value="all">All Types</option>
              <option value="retailer">Retailer</option>
              <option value="wholesaler">Wholesaler</option>
              <option value="aggregator">Aggregator</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Minimum Rating</label>
            <select
              className="input-field"
              value={filters.minRating}
              onChange={(e) => setFilters({ ...filters, minRating: parseFloat(e.target.value) })}
            >
              <option value="0">Any</option>
              <option value="3.0">3.0+</option>
              <option value="3.5">3.5+</option>
              <option value="4.0">4.0+</option>
              <option value="4.5">4.5+</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Sort By</label>
            <select
              className="input-field"
              value={filters.sortBy}
              onChange={(e) => setFilters({ ...filters, sortBy: e.target.value })}
            >
              <option value="score">Match Score</option>
              <option value="distance">Distance</option>
              <option value="rating">Rating</option>
            </select>
          </div>
        </div>

        <button
          onClick={findBuyers}
          disabled={loading}
          className="btn-primary w-full flex items-center justify-center space-x-2 py-3"
        >
          {loading ? (
            <>
              <svg className="animate-spin h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              <span>Searching...</span>
            </>
          ) : (
            <>
              <Search className="w-5 h-5" />
              <span>Find Buyers</span>
            </>
          )}
        </button>
      </div>

      {/* Results */}
      {filteredBuyers && filteredBuyers.length > 0 && (
        <div className="card">
          <div className="mb-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-xl font-bold text-gray-800">
                🎉 Found {filteredBuyers.length} Matching Buyers
              </h3>
              <SpeakButton
                text={(() => {
                  const top3 = filteredBuyers.slice(0, 3)
                  let t = `Found ${filteredBuyers.length} matching buyers for ${produceData.quantity} kg ${produceData.cropName}. `
                  t += `Average distance: ${(filteredBuyers.reduce((sum, b) => sum + b.distance_km, 0) / filteredBuyers.length).toFixed(1)} km. `
                  t += `Average rating: ${(filteredBuyers.reduce((sum, b) => sum + b.rating, 0) / filteredBuyers.length).toFixed(1)} stars. `
                  t += 'Top matches: ' + top3.map((b, i) => `${i+1}. ${b.shop_name}, ${b.distance_km} km away, rating ${b.rating}, match score ${b.match_score}`).join('. ') + '.'
                  const urgent = top3.filter(b => b.has_active_demand)
                  if (urgent.length > 0) t += ` ${urgent.length} buyer${urgent.length > 1 ? 's have' : ' has'} active demand.`
                  return t
                })()}
                textHindi={(() => {
                  let t = `${produceData.cropName} के लिए ${filteredBuyers.length} खरीदार मिले। `
                  const top = filteredBuyers[0]
                  if (top) t += `सबसे अच्छा मैच: ${top.shop_name}, ${top.distance_km} किमी दूर, रेटिंग ${top.rating}।`
                  return t
                })()}
                label="Read Results"
                size="md"
              />
            </div>
            
            {/* Summary Metrics */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="bg-blue-50 p-3 rounded-lg text-center">
                <p className="text-sm text-gray-600">Total Matches</p>
                <p className="text-2xl font-bold text-blue-700">{filteredBuyers.length}</p>
              </div>
              <div className="bg-green-50 p-3 rounded-lg text-center">
                <p className="text-sm text-gray-600">Avg Distance</p>
                <p className="text-2xl font-bold text-green-700">
                  {(filteredBuyers.reduce((sum, b) => sum + b.distance_km, 0) / filteredBuyers.length).toFixed(1)} km
                </p>
              </div>
              <div className="bg-yellow-50 p-3 rounded-lg text-center">
                <p className="text-sm text-gray-600">Avg Rating</p>
                <p className="text-2xl font-bold text-yellow-700">
                  {(filteredBuyers.reduce((sum, b) => sum + b.rating, 0) / filteredBuyers.length).toFixed(1)} ⭐
                </p>
              </div>
              <div className="bg-purple-50 p-3 rounded-lg text-center">
                <p className="text-sm text-gray-600">Verified</p>
                <p className="text-2xl font-bold text-purple-700">
                  {filteredBuyers.filter(b => b.is_verified).length}/{filteredBuyers.length}
                </p>
              </div>
            </div>
          </div>

          {/* Buyer Cards */}
          <div className="space-y-4">
            {filteredBuyers.map((buyer, idx) => (
              <div key={buyer.id} className="border border-gray-200 rounded-lg p-5 hover:shadow-lg transition-shadow">
                {/* Header */}
                <div className="flex items-start justify-between mb-4">
                  <div className="flex-1">
                    <div className="flex items-center space-x-3 mb-2">
                      <h4 className="text-xl font-bold text-gray-800">
                        #{idx + 1}. {buyer.shop_name}
                      </h4>
                      {buyer.is_verified && (
                        <span className="badge-success text-xs">✓ Verified</span>
                      )}
                    </div>
                    <p className="text-gray-600">{buyer.contact_name}</p>
                  </div>
                  <div className="text-right">
                    <div className="flex items-center space-x-2 justify-end mb-1">
                      <Star className="w-5 h-5 text-yellow-500 fill-yellow-500" />
                      <span className="text-lg font-bold text-gray-800">{buyer.rating}</span>
                    </div>
                    <p className="text-sm text-gray-500">Match: {buyer.match_score}/100</p>
                  </div>
                </div>

                {/* Info Grid */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4 text-sm">
                  <div className="flex items-center space-x-2">
                    <MapPin className="w-4 h-4 text-gray-500" />
                    <span>{buyer.distance_km} km away</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <span>{buyerTypeEmoji[buyer.buyer_type]}</span>
                    <span className="capitalize">{buyer.buyer_type}</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Phone className="w-4 h-4 text-gray-500" />
                    <span>{buyer.contact_phone}</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Package className="w-4 h-4 text-gray-500" />
                    <span>Max: {buyer.max_quantity_kg} kg</span>
                  </div>
                </div>

                <div className="text-sm text-gray-600 mb-4">
                  <p><strong>Location:</strong> {buyer.district}, {buyer.state}</p>
                  <p><strong>Operating Hours:</strong> {buyer.operating_hours}</p>
                  <p><strong>Payment:</strong> {buyer.payment_modes.join(', ')} | Avg {buyer.avg_payment_days} days</p>
                  <p><strong>Delivery:</strong> {buyer.accepts_delivery ? '✓ Yes' : '✗ No'}</p>
                </div>

                {/* Active Demand Alert */}
                {buyer.has_active_demand && (
                  <div className={`mb-4 p-3 rounded-lg ${buyer.active_demand.urgency === 'high' ? 'bg-red-50 border border-red-200' : 'bg-yellow-50 border border-yellow-200'}`}>
                    <p className="font-semibold text-sm mb-1">
                      📢 ACTIVE DEMAND {buyer.active_demand.urgency === 'high' && '- URGENT!'}
                    </p>
                    <p className="text-xs">
                      Needs: <strong>{buyer.active_demand.quantity_needed_kg} kg</strong> | 
                      Max Price: <strong>₹{buyer.active_demand.max_price_per_kg}/kg</strong> | 
                      Valid: <strong>{buyer.active_demand.valid_until}</strong>
                    </p>
                  </div>
                )}

                {/* Logistics Recommendation */}
                {buyer.logistics && (
                <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-4">
                  <h5 className="font-semibold text-gray-800 mb-3 flex items-center">
                    <Truck className="w-5 h-5 mr-2" />
                    Logistics Recommendation
                  </h5>
                  <div className="bg-white p-3 rounded-lg mb-3">
                    <p className="font-semibold text-green-700 mb-2">
                      {buyer.logistics.vehicle_icon} Recommended: {buyer.logistics.vehicle_name}
                    </p>
                    <div className="grid grid-cols-3 gap-3 text-sm">
                      <div className="flex items-center space-x-1">
                        <DollarSign className="w-4 h-4 text-gray-500" />
                        <span>₹{buyer.logistics.estimated_cost}</span>
                      </div>
                      <div className="flex items-center space-x-1">
                        <Clock className="w-4 h-4 text-gray-500" />
                        <span>{buyer.logistics.estimated_time_hours}h</span>
                      </div>
                      <div className="text-xs">
                        <span>{buyer.logistics.capacity_utilization}% utilized</span>
                      </div>
                    </div>
                  </div>
                  <div className="text-xs space-y-1">
                    <p className="font-medium text-gray-700">Why this vehicle?</p>
                    {buyer.logistics.reasons.map((reason, idx) => (
                      <p key={idx} className="text-gray-600">✓ {reason}</p>
                    ))}
                  </div>
                </div>
                )}

                {/* Match Score Breakdown */}
                <div>
                  <p className="text-sm font-medium text-gray-700 mb-2">Match Score Breakdown:</p>
                  <div className="grid grid-cols-3 md:grid-cols-6 gap-2 text-center text-xs">
                    {Object.entries(buyer.sub_scores).map(([key, value]) => (
                      <div key={key} className="bg-gray-50 p-2 rounded">
                        <p className="text-gray-600 capitalize">{key.replace('_', ' ')}</p>
                        <p className="font-bold text-gray-800">{value}</p>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Contact Button */}
                <button className="btn-primary w-full mt-4 flex items-center justify-center space-x-2">
                  <Phone className="w-4 h-4" />
                  <span>Contact {buyer.shop_name}</span>
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {filteredBuyers && filteredBuyers.length === 0 && (
        <div className="card text-center py-12">
          <Users className="w-16 h-16 text-gray-300 mx-auto mb-4" />
          <p className="text-gray-500">
            No buyers found with the current filters. Try adjusting your search criteria.
          </p>
        </div>
      )}

      {!buyers && !loading && (
        <div className="card text-center py-12">
          <Users className="w-16 h-16 text-gray-300 mx-auto mb-4" />
          <p className="text-gray-500">
            Click "Find Buyers" to search for verified buyers near your location
          </p>
        </div>
      )}
    </div>
  )
}

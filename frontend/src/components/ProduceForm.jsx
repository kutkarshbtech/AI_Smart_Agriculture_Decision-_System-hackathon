import { useState } from 'react'
import { MapPin, Package } from 'lucide-react'

const indianCities = {
  'Lucknow, Uttar Pradesh': [26.8467, 80.9462],
  'Delhi': [28.6139, 77.2090],
  'Mumbai, Maharashtra': [19.0760, 72.8777],
  'Bengaluru, Karnataka': [12.9716, 77.5946],
  'Chennai, Tamil Nadu': [13.0827, 80.2707],
  'Kolkata, West Bengal': [22.5726, 88.3639],
  'Hyderabad, Telangana': [17.3850, 78.4867],
  'Pune, Maharashtra': [18.5204, 73.8567],
  'Ahmedabad, Gujarat': [23.0225, 72.5714],
  'Jaipur, Rajasthan': [26.9124, 75.7873],
  'Surat, Gujarat': [21.1702, 72.8311],
  'Kanpur, Uttar Pradesh': [26.4499, 80.3319],
  'Nagpur, Maharashtra': [21.1458, 79.0882],
  'Indore, Madhya Pradesh': [22.7196, 75.8577],
  'Patna, Bihar': [25.5941, 85.1376],
  'Vadodara, Gujarat': [22.3072, 73.1812],
  'Ludhiana, Punjab': [30.9010, 75.8573],
  'Agra, Uttar Pradesh': [27.1767, 78.0081],
  'Varanasi, Uttar Pradesh': [25.3176, 82.9739],
  'Chandigarh': [30.7333, 76.7794],
  'Coimbatore, Tamil Nadu': [11.0168, 76.9558],
  'Kochi, Kerala': [9.9312, 76.2673],
}

const cropOptions = [
  'tomato', 'potato', 'onion', 'apple', 'banana', 'mango',
  'carrot', 'capsicum', 'cucumber', 'spinach', 'cauliflower'
]

const indianStates = [
  'All States', 'Andhra Pradesh', 'Bihar', 'Chhattisgarh', 'Delhi',
  'Gujarat', 'Haryana', 'Karnataka', 'Kerala', 'Madhya Pradesh',
  'Maharashtra', 'Odisha', 'Punjab', 'Rajasthan', 'Tamil Nadu',
  'Telangana', 'Uttar Pradesh', 'West Bengal'
]

export default function ProduceForm({ produceData, setProduceData }) {
  const [useCustomLocation, setUseCustomLocation] = useState(false)

  const handleCityChange = (city) => {
    if (city === 'Custom Location') {
      setUseCustomLocation(true)
    } else {
      const [lat, lng] = indianCities[city]
      setProduceData({
        ...produceData,
        location: city,
        latitude: lat,
        longitude: lng,
      })
      setUseCustomLocation(false)
    }
  }

  return (
    <div className="card sticky top-20">
      <h2 className="text-xl font-bold text-gray-800 mb-4 flex items-center">
        <Package className="w-6 h-6 mr-2 text-primary-600" />
        Produce Details
      </h2>

      <div className="space-y-4">
        {/* Crop Selection */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Crop Type
          </label>
          <select
            className="input-field"
            value={produceData.cropName}
            onChange={(e) => setProduceData({ ...produceData, cropName: e.target.value })}
          >
            {cropOptions.map((crop) => (
              <option key={crop} value={crop}>
                {crop.charAt(0).toUpperCase() + crop.slice(1)}
              </option>
            ))}
          </select>
        </div>

        {/* Quantity */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Quantity (kg)
          </label>
          <input
            type="number"
            className="input-field"
            value={produceData.quantity}
            onChange={(e) => setProduceData({ ...produceData, quantity: parseInt(e.target.value) })}
            min="1"
            max="10000"
            step="10"
          />
        </div>

        {/* State Filter */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            State (for mandi prices)
          </label>
          <select
            className="input-field"
            value={produceData.state || 'All States'}
            onChange={(e) => setProduceData({ ...produceData, state: e.target.value })}
          >
            {indianStates.map((state) => (
              <option key={state} value={state}>
                {state}
              </option>
            ))}
          </select>
        </div>

        <hr className="my-4" />

        {/* Location */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2 flex items-center">
            <MapPin className="w-4 h-4 mr-1" />
            Your Location
          </label>
          <select
            className="input-field"
            value={useCustomLocation ? 'Custom Location' : produceData.location}
            onChange={(e) => handleCityChange(e.target.value)}
          >
            {Object.keys(indianCities).map((city) => (
              <option key={city} value={city}>
                {city}
              </option>
            ))}
            <option value="Custom Location">Custom Location</option>
          </select>
        </div>

        {useCustomLocation && (
          <div className="grid grid-cols-2 gap-2">
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">
                Latitude
              </label>
              <input
                type="number"
                className="input-field text-sm"
                value={produceData.latitude}
                onChange={(e) => setProduceData({ ...produceData, latitude: parseFloat(e.target.value) })}
                step="0.0001"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">
                Longitude
              </label>
              <input
                type="number"
                className="input-field text-sm"
                value={produceData.longitude}
                onChange={(e) => setProduceData({ ...produceData, longitude: parseFloat(e.target.value) })}
                step="0.0001"
              />
            </div>
          </div>
        )}

        {!useCustomLocation && (
          <div className="text-xs text-gray-500">
            📍 {produceData.latitude?.toFixed(4)}, {produceData.longitude?.toFixed(4)}
          </div>
        )}

        {/* Search Distance for Buyers */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Search Distance (km)
          </label>
          <input
            type="range"
            className="w-full"
            value={produceData.maxDistance || 50}
            onChange={(e) => setProduceData({ ...produceData, maxDistance: parseInt(e.target.value) })}
            min="10"
            max="200"
            step="10"
          />
          <div className="text-center text-sm text-gray-600 mt-1">
            {produceData.maxDistance || 50} km
          </div>
        </div>
      </div>

      {/* Info Box */}
      <div className="mt-6 p-4 bg-blue-50 rounded-lg border border-blue-200">
        <p className="text-xs text-blue-800">
          💡 <strong>Tip:</strong> Upload produce images in the Quality Assessment tab to get
          AI-powered freshness analysis and price recommendations.
        </p>
      </div>
    </div>
  )
}

import { useState } from 'react'
import axios from 'axios'
import { Cloud, CloudRain, Sun, Wind, Droplets, Thermometer, Calendar } from 'lucide-react'

const WEATHER_ICONS = {
  Clear: Sun,
  Clouds: Cloud,
  Rain: CloudRain,
  Drizzle: CloudRain,
  Thunderstorm: CloudRain,
  Snow: Cloud,
  Mist: Wind,
}

const getWeatherIcon = (condition) => {
  const Icon = WEATHER_ICONS[condition] || Cloud
  return <Icon className="w-8 h-8" />
}

export default function WeatherForecast({ produceData }) {
  const [loading, setLoading] = useState(false)
  const [forecast, setForecast] = useState(null)

  const fetchForecast = async () => {
    setLoading(true)
    
    try {
      // Extract city from location
      const city = produceData.location.split(',')[0]
      
      // Call backend API
      const response = await axios.get(`/api/v1/weather/forecast/city/${city}`, {
        params: {
          days: 5
        }
      })
      
      // Backend returns a flat array; wrap it for the UI
      setForecast({ daily_summary: response.data })
      setLoading(false)
    } catch (error) {
      console.error('Failed to fetch weather forecast:', error)
      setLoading(false)
      alert('Failed to fetch weather forecast. Please try again.')
    }
  }

  const getAgriculturalAdvisory = (day) => {
    const advisories = []
    
    if (day.temp_max > 35) {
      advisories.push({
        type: 'warning',
        message: '🔥 High heat alert - Increase irrigation',
      })
    }
    
    if (day.rainfall_mm > 10) {
      advisories.push({
        type: 'warning',
        message: '🌧️ Heavy rainfall expected - Protect stored produce',
      })
    }
    
    if (day.humidity_avg > 80) {
      advisories.push({
        type: 'info',
        message: '💧 High humidity - Risk of fungal growth',
      })
    } else if (day.humidity_avg < 40) {
      advisories.push({
        type: 'info',
        message: '☀️ Low humidity - Good for drying crops',
      })
    }
    
    return advisories
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold text-gray-800 flex items-center gap-2">
              <Cloud className="w-8 h-8 text-blue-600" />
              Weather Forecast
            </h2>
            <p className="text-gray-600 mt-1">5-day agricultural weather forecast for {produceData.location}</p>
          </div>
          <button
            onClick={fetchForecast}
            disabled={loading}
            className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-semibold"
          >
            {loading ? 'Loading...' : 'Get Forecast'}
          </button>
        </div>
      </div>

      {/* Forecast Display */}
      {forecast && (
        <div className="space-y-6">
          {/* 5-Day Overview */}
          <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
            {forecast.daily_summary.map((day, idx) => (
              <div key={idx} className="bg-gradient-to-br from-blue-50 to-white rounded-lg shadow-md p-4 border border-blue-100">
                <div className="text-center">
                  <div className="text-sm font-semibold text-gray-600">
                    {new Date(day.date).toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' })}
                  </div>
                  <div className="my-3 flex justify-center text-blue-600">
                    {getWeatherIcon(day.condition)}
                  </div>
                  <div className="text-xs text-gray-500 mb-2">{day.condition}</div>
                  <div className="text-2xl font-bold text-gray-800">{day.temp_max}°</div>
                  <div className="text-sm text-gray-600">{day.temp_min}°</div>
                  {day.rainfall_mm > 0 && (
                    <div className="mt-2 text-xs text-blue-600 flex items-center justify-center gap-1">
                      <CloudRain className="w-3 h-3" />
                      {day.rainfall_mm}mm
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>

          {/* Detailed Forecast */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <h3 className="text-xl font-bold text-gray-800 mb-4">Detailed Forecast</h3>
            <div className="space-y-4">
              {forecast.daily_summary.map((day, idx) => {
                const advisories = getAgriculturalAdvisory(day)
                return (
                  <div key={idx} className="border border-gray-200 rounded-lg p-4 hover:border-blue-300 transition-colors">
                    <div className="flex items-center justify-between mb-3">
                      <div className="flex items-center gap-3">
                        <div className="text-blue-600">
                          {getWeatherIcon(day.condition)}
                        </div>
                        <div>
                          <div className="font-semibold text-gray-800">
                            {new Date(day.date).toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric' })}
                          </div>
                          <div className="text-sm text-gray-500">{day.condition}</div>
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="text-2xl font-bold text-gray-800">{day.temp_avg}°C</div>
                        <div className="text-xs text-gray-500">{day.temp_min}° - {day.temp_max}°</div>
                      </div>
                    </div>
                    
                    <div className="grid grid-cols-3 gap-4 mb-3">
                      <div className="flex items-center gap-2 text-sm">
                        <Droplets className="w-4 h-4 text-blue-500" />
                        <span className="text-gray-600">Humidity: {day.humidity_avg}%</span>
                      </div>
                      <div className="flex items-center gap-2 text-sm">
                        <CloudRain className="w-4 h-4 text-blue-500" />
                        <span className="text-gray-600">Rain: {day.rainfall_mm}mm</span>
                      </div>
                      <div className="flex items-center gap-2 text-sm">
                        <Wind className="w-4 h-4 text-blue-500" />
                        <span className="text-gray-600">Wind: {day.wind_speed_avg} km/h</span>
                      </div>
                    </div>

                    {advisories.length > 0 && (
                      <div className="space-y-2">
                        {advisories.map((advisory, i) => (
                          <div
                            key={i}
                            className={`text-sm p-2 rounded ${
                              advisory.type === 'warning'
                                ? 'bg-yellow-50 text-yellow-800 border border-yellow-200'
                                : 'bg-blue-50 text-blue-800 border border-blue-200'
                            }`}
                          >
                            {advisory.message}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )
              })}
            </div>
          </div>

          {/* Summary Statistics */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <h3 className="text-xl font-bold text-gray-800 mb-4">5-Day Summary</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="bg-gradient-to-br from-orange-50 to-white p-4 rounded-lg border border-orange-100">
                <div className="flex items-center gap-2 mb-2">
                  <Thermometer className="w-5 h-5 text-orange-600" />
                  <span className="text-sm font-semibold text-gray-600">Average Temperature</span>
                </div>
                <div className="text-3xl font-bold text-orange-600">
                  {(forecast.daily_summary.reduce((sum, d) => sum + d.temp_avg, 0) / forecast.daily_summary.length).toFixed(1)}°C
                </div>
              </div>
              <div className="bg-gradient-to-br from-blue-50 to-white p-4 rounded-lg border border-blue-100">
                <div className="flex items-center gap-2 mb-2">
                  <CloudRain className="w-5 h-5 text-blue-600" />
                  <span className="text-sm font-semibold text-gray-600">Total Rainfall</span>
                </div>
                <div className="text-3xl font-bold text-blue-600">
                  {forecast.daily_summary.reduce((sum, d) => sum + d.rainfall_mm, 0)} mm
                </div>
              </div>
              <div className="bg-gradient-to-br from-green-50 to-white p-4 rounded-lg border border-green-100">
                <div className="flex items-center gap-2 mb-2">
                  <Droplets className="w-5 h-5 text-green-600" />
                  <span className="text-sm font-semibold text-gray-600">Average Humidity</span>
                </div>
                <div className="text-3xl font-bold text-green-600">
                  {(forecast.daily_summary.reduce((sum, d) => sum + d.humidity_avg, 0) / forecast.daily_summary.length).toFixed(0)}%
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {!forecast && !loading && (
        <div className="bg-white rounded-lg shadow-md p-12 text-center">
          <Cloud className="w-16 h-16 text-gray-300 mx-auto mb-4" />
          <p className="text-gray-500">Click "Get Forecast" to view 5-day weather prediction</p>
        </div>
      )}
    </div>
  )
}

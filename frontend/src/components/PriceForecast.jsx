import { useState } from 'react'
import axios from 'axios'
import {
  TrendingUp, CloudSun, BarChart3, ArrowUpDown, Search, Lightbulb, Truck, Package, Store,
} from 'lucide-react'
import SpeakButton from './SpeakButton'
import {
  LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, Legend, ResponsiveContainer,
} from 'recharts'

const TABS = [
  { key: 'trends', label: 'Price Trends', icon: TrendingUp },
  { key: 'forecast', label: 'Weather Forecast', icon: CloudSun },
  { key: 'compare', label: 'State Compare', icon: ArrowUpDown },
]

export default function PriceForecast({ produceData }) {
  const [activeTab, setActiveTab] = useState('trends')
  const [loading, setLoading] = useState(false)

  // Trends state
  const [trends, setTrends] = useState(null)

  // Weather-based forecast state
  const [weatherForecast, setWeatherForecast] = useState(null)
  const [forecastDays, setForecastDays] = useState(5)
  const [qualityGrade, setQualityGrade] = useState('good')
  const [storageType, setStorageType] = useState('ambient')

  // Compare state
  const [compareData, setCompareData] = useState(null)
  const [compareStates, setCompareStates] = useState('Andhra Pradesh,Madhya Pradesh')

  // ── Fetch Trends ──────────────────────────────
  const fetchTrends = async () => {
    setLoading(true)
    try {
      const response = await axios.get(`/api/v1/pricing/trends/${produceData.cropName}`)
      setTrends(response.data)
    } catch (error) {
      console.error('Trends fetch failed:', error)
      alert('Failed to fetch price trends.')
    } finally {
      setLoading(false)
    }
  }

  // ── Fetch Weather Forecast ────────────────────
  const fetchWeatherForecast = async () => {
    setLoading(true)
    try {
      const city = produceData.location.split(',')[0].trim()
      const response = await axios.get(`/api/v1/pricing/weather-forecast/${produceData.cropName}`, {
        params: {
          days_ahead: forecastDays,
          city,
          quality_grade: qualityGrade,
          storage_type: storageType,
          harvest_days_ago: 1,
        },
      })
      const data = response.data
      // Flatten nested daily_forecast so Recharts can access keys directly
      if (data.daily_forecast) {
        data.daily_forecast = data.daily_forecast.map((day) => ({
          ...day,
          projected_price: day.price_impact?.projected_price,
          crop_health_score: day.crop_health?.health_score,
          temperature: day.weather?.temp_avg,
          humidity: day.weather?.humidity,
          weather_risk: day.crop_health?.weather_risk,
          condition: day.weather?.condition,
          advisory: day.advisory,
        }))
      }
      setWeatherForecast(data)
    } catch (error) {
      console.error('Weather forecast failed:', error)
      alert('Failed to fetch weather-based price forecast.')
    } finally {
      setLoading(false)
    }
  }

  // ── Fetch State Compare ───────────────────────
  const fetchCompare = async () => {
    setLoading(true)
    try {
      const response = await axios.get(`/api/v1/pricing/mandi/compare/${produceData.cropName}`, {
        params: {
          states: compareStates,
          limit_per_state: 10,
        },
      })
      setCompareData(response.data)
    } catch (error) {
      console.error('Compare failed:', error)
      alert('Failed to fetch price comparison.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="card">
        <div className="flex items-center gap-3 mb-4">
          <BarChart3 className="w-8 h-8 text-emerald-600" />
          <div>
            <h2 className="text-2xl font-bold text-gray-800">Price Intelligence</h2>
            <p className="text-gray-600 text-sm">Trends, weather-based forecasts, and cross-state comparison</p>
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="flex border-b border-gray-200">
          {TABS.map((tab) => {
            const Icon = tab.icon
            return (
              <button
                key={tab.key}
                onClick={() => setActiveTab(tab.key)}
                className={`flex items-center gap-2 px-4 py-3 font-medium text-sm transition-colors border-b-2 ${
                  activeTab === tab.key
                    ? 'text-emerald-700 border-emerald-700'
                    : 'text-gray-500 border-transparent hover:text-emerald-600'
                }`}
              >
                <Icon className="w-4 h-4" />
                {tab.label}
              </button>
            )
          })}
        </div>
      </div>

      {/* ═════════════════ TRENDS TAB ═════════════════ */}
      {activeTab === 'trends' && (
        <div className="space-y-6">
          <div className="card">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-bold text-gray-800">
                📈 Price Trends — {produceData.cropName}
              </h3>
              <button onClick={fetchTrends} disabled={loading} className="btn-primary flex items-center gap-2">
                <Search className="w-4 h-4" />
                {loading ? 'Loading...' : 'Fetch Trends'}
              </button>
            </div>

            {!trends && !loading && (
              <div className="text-center py-8 bg-gray-50 rounded-lg">
                <TrendingUp className="w-12 h-12 text-gray-300 mx-auto mb-3" />
                <p className="text-gray-500">Click "Fetch Trends" to see 14-day price trend analysis</p>
              </div>
            )}

            {trends && (
              <>
                {/* Voice Summary for Trends */}
                <div className="flex justify-end mb-4">
                  <SpeakButton
                    text={`Price trends for ${produceData.cropName}. 7-day average price: ${trends.avg_price_7d} rupees per kg. 14-day average: ${trends.avg_price_14d} rupees per kg. Latest price: ${trends.latest_price || 'unavailable'} rupees per kg. Current trend: ${trends.trend || 'stable'}.`}
                    textHindi={`${produceData.cropName} की कीमत रुझान। 7 दिन का औसत: ${trends.avg_price_7d} रुपये प्रति किलो। 14 दिन का औसत: ${trends.avg_price_14d} रुपये। वर्तमान रुझान: ${trends.trend === 'rising' ? 'बढ़ता' : trends.trend === 'falling' ? 'गिरता' : 'स्थिर'}।`}
                    label="Read Trends"
                    size="md"
                  />
                </div>

                {/* Summary Cards */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                  <div className="bg-gradient-to-br from-blue-50 to-blue-100 p-4 rounded-lg text-center">
                    <p className="text-sm text-gray-600">7-day Avg</p>
                    <p className="text-2xl font-bold text-blue-700">₹{trends.avg_price_7d}</p>
                    <p className="text-xs text-gray-500">per kg</p>
                  </div>
                  <div className="bg-gradient-to-br from-purple-50 to-purple-100 p-4 rounded-lg text-center">
                    <p className="text-sm text-gray-600">14-day Avg</p>
                    <p className="text-2xl font-bold text-purple-700">₹{trends.avg_price_14d}</p>
                    <p className="text-xs text-gray-500">per kg</p>
                  </div>
                  <div className="bg-gradient-to-br from-green-50 to-green-100 p-4 rounded-lg text-center">
                    <p className="text-sm text-gray-600">Latest Price</p>
                    <p className="text-2xl font-bold text-green-700">₹{trends.latest_price || '—'}</p>
                    <p className="text-xs text-gray-500">per kg</p>
                  </div>
                  <div className={`p-4 rounded-lg text-center ${
                    trends.trend === 'rising' ? 'bg-green-100' : trends.trend === 'falling' ? 'bg-red-100' : 'bg-gray-100'
                  }`}>
                    <p className="text-sm text-gray-600">Trend</p>
                    <p className={`text-2xl font-bold capitalize ${
                      trends.trend === 'rising' ? 'text-green-700' : trends.trend === 'falling' ? 'text-red-700' : 'text-gray-700'
                    }`}>
                      {trends.trend === 'rising' ? '📈' : trends.trend === 'falling' ? '📉' : '➡️'} {trends.trend}
                    </p>
                  </div>
                </div>

                {/* Price Chart */}
                {trends.price_history && trends.price_history.length > 0 && (
                  <div>
                    <h4 className="font-semibold text-gray-800 mb-3">Price History</h4>
                    <ResponsiveContainer width="100%" height={300}>
                      <LineChart data={trends.price_history}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="date" fontSize={12} />
                        <YAxis label={{ value: '₹/kg', angle: -90, position: 'insideLeft' }} />
                        <Tooltip />
                        <Legend />
                        <Line type="monotone" dataKey="modal_price" stroke="#22c55e" strokeWidth={2} name="Modal Price" dot={{ r: 3 }} />
                        <Line type="monotone" dataKey="min_price" stroke="#f59e0b" strokeDasharray="5 5" name="Min Price" dot={false} />
                        <Line type="monotone" dataKey="max_price" stroke="#ef4444" strokeDasharray="5 5" name="Max Price" dot={false} />
                      </LineChart>
                    </ResponsiveContainer>
                  </div>
                )}

                {/* 💡 AI Selling Strategy based on trends */}
                <div className="mt-6 border-l-4 border-emerald-500 bg-emerald-50 rounded-lg p-5">
                  <h4 className="font-bold text-gray-800 mb-3 flex items-center gap-2">
                    <Lightbulb className="w-5 h-5 text-emerald-600" />
                    💡 AI Selling Strategy — {produceData.cropName}
                  </h4>
                  <div className="space-y-3">
                    {/* Trend-based advice */}
                    <div className="bg-white/70 p-3 rounded-lg border border-emerald-200">
                      <span className="text-lg mr-2">
                        {trends.trend === 'rising' ? '📈' : trends.trend === 'falling' ? '📉' : '➡️'}
                      </span>
                      <span className="text-sm text-gray-800 font-medium">
                        {trends.trend === 'rising'
                          ? `Prices are RISING — consider holding your ${produceData.cropName} for 2-3 more days if storage conditions allow. Expected better returns.`
                          : trends.trend === 'falling'
                          ? `Prices are FALLING — sell your ${produceData.cropName} as soon as possible. Delaying will reduce your income. Consider selling at the current best mandi.`
                          : `Prices are STABLE — good time to sell at current market rates. No significant advantage to holding.`}
                      </span>
                    </div>
                    {/* Storage recommendation */}
                    <div className="bg-white/70 p-3 rounded-lg border border-emerald-200 flex items-start gap-2">
                      <Package className="w-5 h-5 text-teal-600 flex-shrink-0 mt-0.5" />
                      <span className="text-sm text-gray-800">
                        {trends.trend === 'rising'
                          ? `Use cold storage (if available at ₹2-3/kg/day) to hold and sell at peak. Potential gain: ₹${((trends.avg_price_7d || 0) * 0.1).toFixed(0)}-${((trends.avg_price_7d || 0) * 0.2).toFixed(0)}/kg.`
                          : `Don't invest in cold storage costs when prices are ${trends.trend || 'stable'}. Sell directly to reduce overhead.`}
                      </span>
                    </div>
                    {/* Market channel advice */}
                    <div className="bg-white/70 p-3 rounded-lg border border-emerald-200 flex items-start gap-2">
                      <Store className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
                      <span className="text-sm text-gray-800">
                        {(trends.latest_price || 0) > (trends.avg_price_7d || 0) * 1.1
                          ? `Current price (₹${trends.latest_price}/kg) is above 7-day average — sell now through FPO or direct mandi for maximum return.`
                          : `Consider aggregating with nearby farmers through FPO/cooperative for better negotiating power. Bulk selling can add ₹2-5/kg premium.`}
                      </span>
                    </div>
                    {/* Price volatility warning */}
                    {trends.price_history?.length > 3 && (() => {
                      const prices = trends.price_history.map(p => p.modal_price).filter(Boolean)
                      const min = Math.min(...prices)
                      const max = Math.max(...prices)
                      const volatility = min > 0 ? ((max - min) / min * 100).toFixed(0) : 0
                      if (volatility > 20) {
                        return (
                          <div className="bg-yellow-50 p-3 rounded-lg border border-yellow-300 flex items-start gap-2">
                            <span className="text-lg">⚠️</span>
                            <span className="text-sm text-yellow-800">
                              High price volatility detected ({volatility}% range). Lock in forward contracts or negotiate fixed-price deals to reduce uncertainty.
                            </span>
                          </div>
                        )
                      }
                      return null
                    })()}
                  </div>
                </div>
              </>
            )}
          </div>
        </div>
      )}

      {/* ═════════════════ WEATHER FORECAST TAB ═════════════════ */}
      {activeTab === 'forecast' && (
        <div className="space-y-6">
          <div className="card">
            <h3 className="text-lg font-bold text-gray-800 mb-4 flex items-center gap-2">
              <CloudSun className="w-6 h-6 text-sky-600" />
              Weather-Based Price & Crop Health Forecast
            </h3>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Days Ahead</label>
                <select className="input-field" value={forecastDays} onChange={(e) => setForecastDays(parseInt(e.target.value))}>
                  {[1, 2, 3, 4, 5].map((d) => (
                    <option key={d} value={d}>{d} day{d > 1 ? 's' : ''}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Quality Grade</label>
                <select className="input-field" value={qualityGrade} onChange={(e) => setQualityGrade(e.target.value)}>
                  <option value="excellent">Excellent</option>
                  <option value="good">Good</option>
                  <option value="average">Average</option>
                  <option value="poor">Poor</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Storage Type</label>
                <select className="input-field" value={storageType} onChange={(e) => setStorageType(e.target.value)}>
                  <option value="ambient">Ambient</option>
                  <option value="cold">Cold Storage</option>
                  <option value="controlled">Controlled Atmosphere</option>
                </select>
              </div>
            </div>

            <button onClick={fetchWeatherForecast} disabled={loading} className="w-full btn-primary py-3">
              {loading ? 'Fetching forecast...' : '🌦️ Get Weather-Based Forecast'}
            </button>
          </div>

          {/* Forecast Results */}
          {weatherForecast && (
            <div className="space-y-6">
              {/* Voice Summary for Forecast */}
              <div className="flex justify-end">
                <SpeakButton
                  text={(() => {
                    let t = `Weather-based price forecast for ${produceData.cropName}. `
                    if (weatherForecast.overall_action) t += `Recommendation: ${weatherForecast.overall_action.replace(/_/g, ' ')}. `
                    if (weatherForecast.overall_reason) t += `${weatherForecast.overall_reason}. `
                    if (weatherForecast.best_selling_day) t += `Best selling day: ${weatherForecast.best_selling_day}`
                    if (weatherForecast.best_projected_price) t += ` at ${weatherForecast.best_projected_price.toFixed(2)} rupees per kg`
                    t += '. '
                    if (weatherForecast.current_market_price) t += `Current market price: ${weatherForecast.current_market_price.toFixed(2)} rupees per kg. `
                    if (weatherForecast.remaining_shelf_life_days) t += `Remaining shelf life: ${weatherForecast.remaining_shelf_life_days} days. `
                    return t
                  })()}
                  textHindi={(() => {
                    let t = `${produceData.cropName} के लिए मौसम आधारित कीमत पूर्वानुमान। `
                    if (weatherForecast.overall_action) t += `सुझाव: ${weatherForecast.overall_action.replace(/_/g, ' ')}। `
                    if (weatherForecast.best_selling_day) t += `बिक्री का सबसे अच्छा दिन: ${weatherForecast.best_selling_day}। `
                    return t
                  })()}
                  label="Read Forecast"
                  size="md"
                />
              </div>

              {/* Overall Recommendation */}
              {weatherForecast.overall_action && (
                <div className={`card border-l-4 ${
                  weatherForecast.overall_action?.includes('sell') ? 'border-green-500 bg-green-50' :
                  weatherForecast.overall_action?.includes('store') ? 'border-blue-500 bg-blue-50' :
                  'border-yellow-500 bg-yellow-50'
                }`}>
                  <h3 className="font-bold text-gray-800 mb-2">🎯 Recommendation</h3>
                  <p className="text-lg font-semibold text-gray-700 capitalize">{weatherForecast.overall_action?.replace(/_/g, ' ')}</p>
                  {weatherForecast.overall_reason && (
                    <p className="text-sm text-gray-600 mt-1">{weatherForecast.overall_reason}</p>
                  )}
                  {weatherForecast.best_selling_day && (
                    <p className="text-sm text-gray-600 mt-1">
                      Best selling day: <strong>{weatherForecast.best_selling_day}</strong>
                      {weatherForecast.best_projected_price && (
                        <> at <strong>₹{weatherForecast.best_projected_price?.toFixed(2)}/kg</strong></>
                      )}
                    </p>
                  )}
                </div>
              )}

              {/* 💡 AI Weather-Adjusted Selling Tips */}
              {weatherForecast.daily_forecast && weatherForecast.daily_forecast.length > 0 && (
                <div className="card border-l-4 border-sky-500 bg-sky-50">
                  <h3 className="font-bold text-gray-800 mb-3 flex items-center gap-2">
                    <Lightbulb className="w-5 h-5 text-sky-600" />
                    🌦️ Weather-Smart Advice for {produceData.cropName}
                  </h3>
                  <div className="space-y-2">
                    {/* Shelf life warning */}
                    {weatherForecast.remaining_shelf_life_days !== undefined && (
                      <div className={`p-3 rounded-lg border flex items-start gap-2 ${
                        weatherForecast.remaining_shelf_life_days <= 2
                          ? 'bg-red-50 border-red-300'
                          : 'bg-green-50 border-green-200'
                      }`}>
                        <span className="text-lg">⏰</span>
                        <span className={`text-sm font-medium ${
                          weatherForecast.remaining_shelf_life_days <= 2 ? 'text-red-800' : 'text-green-800'
                        }`}>
                          {weatherForecast.remaining_shelf_life_days <= 2
                            ? `URGENT: Only ${weatherForecast.remaining_shelf_life_days} day(s) of shelf life remaining! Sell today or process immediately.`
                            : `${weatherForecast.remaining_shelf_life_days} days of shelf life remaining — you have time to wait for the best price day.`}
                        </span>
                      </div>
                    )}
                    {/* Rain warning */}
                    {weatherForecast.daily_forecast.some(d => d.condition?.toLowerCase().includes('rain')) && (
                      <div className="bg-blue-50 p-3 rounded-lg border border-blue-200 flex items-start gap-2">
                        <span className="text-lg">🌧️</span>
                        <span className="text-sm text-blue-800">
                          Rain expected in the forecast period. Rainy days typically reduce mandi arrivals and can push prices UP by 5-15%.
                          However, transport may be difficult — plan logistics accordingly.
                        </span>
                      </div>
                    )}
                    {/* High temperature warning */}
                    {weatherForecast.daily_forecast.some(d => (d.temperature || 0) > 35) && (
                      <div className="bg-orange-50 p-3 rounded-lg border border-orange-200 flex items-start gap-2">
                        <span className="text-lg">🔥</span>
                        <span className="text-sm text-orange-800">
                          High temperatures (&gt;35°C) forecast. This accelerates spoilage — sell BEFORE high-temp days or use wet gunny/newspaper cover during transport.
                        </span>
                      </div>
                    )}
                    {/* Best day strategy */}
                    {weatherForecast.best_selling_day && weatherForecast.best_projected_price && weatherForecast.current_market_price && (
                      <div className="bg-white/70 p-3 rounded-lg border border-sky-200 flex items-start gap-2">
                        <span className="text-lg">💰</span>
                        <span className="text-sm text-gray-800">
                          {weatherForecast.best_projected_price > weatherForecast.current_market_price
                            ? `Waiting until ${weatherForecast.best_selling_day} could earn you ₹${(weatherForecast.best_projected_price - weatherForecast.current_market_price).toFixed(2)}/kg more than today's price. For 100kg, that's ₹${((weatherForecast.best_projected_price - weatherForecast.current_market_price) * 100).toFixed(0)} extra.`
                            : `Today's price (₹${weatherForecast.current_market_price.toFixed(2)}/kg) is already competitive. Consider selling now.`}
                        </span>
                      </div>
                    )}
                    {/* Transport tip */}
                    <div className="bg-white/70 p-3 rounded-lg border border-sky-200 flex items-start gap-2">
                      <Truck className="w-5 h-5 text-gray-600 flex-shrink-0 mt-0.5" />
                      <span className="text-sm text-gray-800">
                        Transport early morning (4-7 AM) to avoid heat damage. Use ventilated vehicles and avoid stacking produce more than 3 layers deep.
                      </span>
                    </div>
                  </div>
                </div>
              )}

              {/* Daily Forecast */}
              {weatherForecast.daily_forecast && weatherForecast.daily_forecast.length > 0 && (
                <div className="card">
                  <h3 className="text-lg font-bold text-gray-800 mb-4">📅 Daily Forecast</h3>

                  {/* Chart */}
                  <ResponsiveContainer width="100%" height={300}>
                    <LineChart data={weatherForecast.daily_forecast}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="date" fontSize={12} />
                      <YAxis yAxisId="price" label={{ value: '₹/kg', angle: -90, position: 'insideLeft' }} />
                      <YAxis yAxisId="health" orientation="right" label={{ value: 'Health %', angle: 90, position: 'insideRight' }} />
                      <Tooltip />
                      <Legend />
                      <Line yAxisId="price" type="monotone" dataKey="projected_price" stroke="#22c55e" strokeWidth={2} name="Projected Price" />
                      <Line yAxisId="health" type="monotone" dataKey="crop_health_score" stroke="#3b82f6" strokeWidth={2} name="Crop Health" />
                    </LineChart>
                  </ResponsiveContainer>

                  {/* Daily Cards */}
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3 mt-4">
                    {weatherForecast.daily_forecast.map((day, idx) => (
                      <div key={idx} className="bg-gray-50 p-4 rounded-lg border border-gray-200">
                        <p className="font-semibold text-gray-800 mb-2">{day.date}</p>
                        <div className="space-y-1 text-sm">
                          {day.projected_price && (
                            <div className="flex justify-between">
                              <span className="text-gray-600">Price:</span>
                              <span className="font-semibold text-green-700">₹{day.projected_price?.toFixed(2)}/kg</span>
                            </div>
                          )}
                          {day.crop_health_score !== undefined && (
                            <div className="flex justify-between">
                              <span className="text-gray-600">Crop Health:</span>
                              <span className={`font-semibold ${day.crop_health_score > 70 ? 'text-green-600' : day.crop_health_score > 40 ? 'text-yellow-600' : 'text-red-600'}`}>
                                {day.crop_health_score?.toFixed(0)}%
                              </span>
                            </div>
                          )}
                          {day.temperature && (
                            <div className="flex justify-between">
                              <span className="text-gray-600">Temp:</span>
                              <span className="font-semibold">{day.temperature?.toFixed(1)}°C</span>
                            </div>
                          )}
                          {day.humidity && (
                            <div className="flex justify-between">
                              <span className="text-gray-600">Humidity:</span>
                              <span className="font-semibold">{day.humidity}%</span>
                            </div>
                          )}
                          {day.weather_risk && (
                            <div className="mt-1">
                              <span className={`text-xs px-2 py-0.5 rounded-full ${
                                day.weather_risk === 'high' ? 'bg-red-100 text-red-700' :
                                day.weather_risk === 'medium' ? 'bg-yellow-100 text-yellow-700' :
                                'bg-green-100 text-green-700'
                              }`}>
                                {day.weather_risk} risk
                              </span>
                            </div>
                          )}
                          {day.condition && (
                            <div className="flex justify-between">
                              <span className="text-gray-600">Weather:</span>
                              <span className="font-semibold capitalize">{day.condition}</span>
                            </div>
                          )}
                          {day.advisory && (
                            <p className="text-xs text-gray-500 mt-2 border-t pt-2">{day.advisory}</p>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Summary Info */}
          {weatherForecast && weatherForecast.current_market_price && (
            <div className="card">
              <h3 className="text-lg font-bold text-gray-800 mb-4">📊 Forecast Summary</h3>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="bg-green-50 p-4 rounded-lg text-center">
                  <p className="text-sm text-gray-600">Current Price</p>
                  <p className="text-2xl font-bold text-green-700">₹{weatherForecast.current_market_price?.toFixed(2)}</p>
                  <p className="text-xs text-gray-500">per kg</p>
                </div>
                <div className="bg-blue-50 p-4 rounded-lg text-center">
                  <p className="text-sm text-gray-600">Location</p>
                  <p className="text-lg font-bold text-blue-700">{weatherForecast.location}</p>
                </div>
                <div className="bg-purple-50 p-4 rounded-lg text-center">
                  <p className="text-sm text-gray-600">Shelf Life Left</p>
                  <p className="text-2xl font-bold text-purple-700">{weatherForecast.remaining_shelf_life_days}</p>
                  <p className="text-xs text-gray-500">days</p>
                </div>
                <div className="bg-gray-50 p-4 rounded-lg text-center">
                  <p className="text-sm text-gray-600">Health Trend</p>
                  <p className="text-lg font-bold text-gray-700 capitalize">{weatherForecast.health_trend || '—'}</p>
                </div>
              </div>
            </div>
          )}

          {/* Empty State */}
          {!weatherForecast && !loading && (
            <div className="card text-center py-8">
              <CloudSun className="w-12 h-12 text-gray-300 mx-auto mb-3" />
              <p className="text-gray-500">Configure parameters and click "Get Forecast" to see weather-based price predictions</p>
            </div>
          )}
        </div>
      )}

      {/* ═════════════════ COMPARE TAB ═════════════════ */}
      {activeTab === 'compare' && (
        <div className="space-y-6">
          <div className="card">
            <h3 className="text-lg font-bold text-gray-800 mb-4 flex items-center gap-2">
              <ArrowUpDown className="w-6 h-6 text-violet-600" />
              Cross-State Price Comparison
            </h3>

            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                States (comma-separated)
              </label>
              <input
                type="text"
                className="input-field"
                value={compareStates}
                onChange={(e) => setCompareStates(e.target.value)}
                placeholder="Maharashtra,Karnataka,Delhi"
              />
            </div>

            <button onClick={fetchCompare} disabled={loading} className="w-full btn-primary py-3">
              {loading ? 'Comparing...' : '🔍 Compare Prices Across States'}
            </button>
          </div>

          {/* Compare Results */}
          {compareData && (
            <div className="space-y-6">
              {/* Voice Summary for Compare */}
              <div className="flex justify-end">
                <SpeakButton
                  text={(() => {
                    let t = `Cross-state price comparison for ${produceData.cropName}. `
                    if (compareData.best_market) t += `Best market: ${compareData.best_market.market} in ${compareData.best_market.state} at ${compareData.best_market.modal_price_per_kg} rupees per kg. `
                    if (compareData.state_summaries?.length > 0) {
                      t += compareData.state_summaries.map(s => `${s.state}: average ${s.avg_price_per_kg} rupees, ${s.num_mandis} mandis`).join('. ') + '.'
                    }
                    return t
                  })()}
                  textHindi={(() => {
                    let t = `${produceData.cropName} का राज्यवार कीमत तुलना। `
                    if (compareData.best_market) t += `सबसे अच्छी मंडी: ${compareData.best_market.market}, ${compareData.best_market.state} में ${compareData.best_market.modal_price_per_kg} रुपये प्रति किलो। `
                    return t
                  })()}
                  label="Read Compare"
                  size="md"
                />
              </div>

              {/* Best Market */}
              {compareData.best_market && (
                <div className="card border-l-4 border-green-500 bg-green-50">
                  <h3 className="font-bold text-gray-800 mb-2">🏆 Best Market</h3>
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-lg font-semibold text-gray-700">{compareData.best_market.market}</p>
                      <p className="text-sm text-gray-600">{compareData.best_market.state}</p>
                    </div>
                    <div className="text-right">
                      <p className="text-3xl font-bold text-green-700">₹{compareData.best_market.modal_price_per_kg}</p>
                      <p className="text-xs text-gray-500">per kg</p>
                    </div>
                  </div>
                </div>
              )}

              {/* 🚚 Logistics & Selling Recommendations */}
              {compareData.state_summaries && compareData.state_summaries.length > 0 && (
                <div className="card border-l-4 border-violet-500 bg-violet-50">
                  <h3 className="font-bold text-gray-800 mb-3 flex items-center gap-2">
                    <Truck className="w-5 h-5 text-violet-600" />
                    🚚 Smart Selling & Logistics Advice
                  </h3>
                  <div className="space-y-2">
                    {/* Best vs local price analysis */}
                    {compareData.best_market && compareData.state_summaries.length > 1 && (() => {
                      const prices = compareData.state_summaries.map(s => s.avg_price_per_kg).filter(Boolean)
                      const minAvg = Math.min(...prices)
                      const maxAvg = Math.max(...prices)
                      const diff = maxAvg - minAvg
                      return (
                        <div className="bg-white/70 p-3 rounded-lg border border-violet-200">
                          <p className="text-sm text-gray-800">
                            <span className="font-semibold">📊 Price Gap:</span> ₹{diff.toFixed(2)}/kg between the cheapest and most expensive state.
                            {diff > 5
                              ? ` This is a significant gap — transporting to the higher-priced state can be profitable even after transport costs (typically ₹1-3/kg for <300km).`
                              : ` The gap is small — selling locally may be better after accounting for transport costs.`}
                          </p>
                        </div>
                      )
                    })()}
                    {/* Best market recommendation */}
                    {compareData.best_market && (
                      <div className="bg-white/70 p-3 rounded-lg border border-violet-200 flex items-start gap-2">
                        <Store className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
                        <span className="text-sm text-gray-800">
                          <strong>{compareData.best_market.market}</strong> ({compareData.best_market.state}) offers the highest price at ₹{compareData.best_market.modal_price_per_kg}/kg.
                          Contact this mandi's commission agent before transporting to confirm current arrivals and demand.
                        </span>
                      </div>
                    )}
                    {/* Aggregation tip */}
                    <div className="bg-white/70 p-3 rounded-lg border border-violet-200 flex items-start gap-2">
                      <Package className="w-5 h-5 text-teal-600 flex-shrink-0 mt-0.5" />
                      <span className="text-sm text-gray-800">
                        💡 <strong>FPO Tip:</strong> Pool your {produceData.cropName} with neighboring farmers for bulk transport.
                        A full truck (5-10 tonnes) costs ₹1-2/kg to transport vs ₹3-5/kg for small loads.
                      </span>
                    </div>
                    {/* eNAM tip */}
                    <div className="bg-white/70 p-3 rounded-lg border border-violet-200 flex items-start gap-2">
                      <span className="text-lg">🏛️</span>
                      <span className="text-sm text-gray-800">
                        Register on <strong>eNAM</strong> (National Agriculture Market) to list your produce across all these mandis simultaneously.
                        eNAM allows online bidding from traders across states — often 5-10% higher than walk-in prices.
                      </span>
                    </div>
                  </div>
                </div>
              )}

              {/* State Summaries Chart */}
              {compareData.state_summaries && compareData.state_summaries.length > 0 && (
                <div className="card">
                  <h3 className="text-lg font-bold text-gray-800 mb-4">State-wise Average Prices</h3>
                  <ResponsiveContainer width="100%" height={300}>
                    <BarChart data={compareData.state_summaries}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="state" fontSize={12} />
                      <YAxis label={{ value: '₹/kg', angle: -90, position: 'insideLeft' }} />
                      <Tooltip />
                      <Legend />
                      <Bar dataKey="avg_price_per_kg" fill="#22c55e" name="Avg Price" />
                      <Bar dataKey="min_price_per_kg" fill="#f59e0b" name="Min Price" />
                      <Bar dataKey="max_price_per_kg" fill="#ef4444" name="Max Price" />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              )}

              {/* State Details */}
              {compareData.state_summaries?.map((state, idx) => (
                <div key={idx} className="card">
                  <div className="flex items-center justify-between mb-3">
                    <h4 className="font-semibold text-gray-800">{state.state}</h4>
                    <span className="text-sm text-gray-500">{state.num_mandis} mandis reporting</span>
                  </div>
                  <div className="grid grid-cols-3 gap-3 mb-3">
                    <div className="bg-green-50 p-3 rounded-lg text-center">
                      <p className="text-xs text-gray-600">Avg</p>
                      <p className="text-lg font-bold text-green-700">₹{state.avg_price_per_kg}</p>
                    </div>
                    <div className="bg-yellow-50 p-3 rounded-lg text-center">
                      <p className="text-xs text-gray-600">Min</p>
                      <p className="text-lg font-bold text-yellow-700">₹{state.min_price_per_kg}</p>
                    </div>
                    <div className="bg-red-50 p-3 rounded-lg text-center">
                      <p className="text-xs text-gray-600">Max</p>
                      <p className="text-lg font-bold text-red-700">₹{state.max_price_per_kg}</p>
                    </div>
                  </div>
                  {state.markets && state.markets.length > 0 && (
                    <div className="space-y-1">
                      {state.markets.map((m, i) => (
                        <div key={i} className="flex justify-between text-sm bg-gray-50 px-3 py-2 rounded">
                          <span className="text-gray-700">{m.market}</span>
                          <span className="font-semibold text-green-700">₹{m.modal_price_per_kg}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}

          {/* No Data State */}
          {compareData && (!compareData.state_summaries || compareData.state_summaries.length === 0) && !loading && (
            <div className="card text-center py-8">
              <ArrowUpDown className="w-12 h-12 text-gray-300 mx-auto mb-3" />
              <p className="text-gray-500 mb-2">No mandi price data found for the selected states</p>
              <p className="text-sm text-gray-400">
                The external mandi API (data.gov.in) may not have current data for this crop/state combination.
                Try different states or a different crop.
              </p>
            </div>
          )}

          {/* Empty State */}
          {!compareData && !loading && (
            <div className="card text-center py-8">
              <ArrowUpDown className="w-12 h-12 text-gray-300 mx-auto mb-3" />
              <p className="text-gray-500">Enter states and click "Compare" to see price differences across states</p>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

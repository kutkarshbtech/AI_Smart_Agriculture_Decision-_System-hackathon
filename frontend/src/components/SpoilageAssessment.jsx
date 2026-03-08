import { useState } from 'react'
import axios from 'axios'
import { ShieldAlert, Thermometer, Droplets, Clock, Leaf, CloudRain, AlertTriangle, Lightbulb, Package } from 'lucide-react'
import SpeakButton from './SpeakButton'

// Crop-specific storage and handling advice
const CROP_STORAGE_ADVICE = {
  tomato: {
    optimal_temp: '10-15°C',
    optimal_humidity: '85-90%',
    tips: [
      { icon: '🌡️', text: 'Store at 10-15°C — never refrigerate below 10°C as it kills flavour and texture' },
      { icon: '📦', text: 'Keep in single layers in ventilated crates, not stacked — pressure causes bruising and rapid decay' },
      { icon: '🚫', text: 'Keep away from ethylene-producers like bananas/mangoes — they ripen tomatoes too fast' },
      { icon: '🧴', text: 'If slightly damaged, make tomato puree, ketchup, or sun-dried tomatoes to recover ₹30-50/kg value' },
    ],
  },
  mango: {
    optimal_temp: '12-14°C',
    optimal_humidity: '85-90%',
    tips: [
      { icon: '🌡️', text: 'Store at 12-14°C with 85-90% humidity for optimal shelf life of 2-3 weeks' },
      { icon: '📰', text: 'Wrap individual mangoes in newspaper to absorb moisture and prevent fungal growth' },
      { icon: '🧃', text: 'Overripe mangoes can be processed into aam ras, mango pulp, or jam — ₹40-80/kg value' },
      { icon: '🥒', text: 'Semi-ripe/raw mangoes make excellent pickle (aachar) — retails at ₹100-200/kg' },
    ],
  },
  banana: {
    optimal_temp: '13-15°C',
    optimal_humidity: '85-95%',
    tips: [
      { icon: '🌡️', text: 'Store at 13-15°C — below 12°C causes chilling injury (blackening of skin)' },
      { icon: '🔗', text: 'Separate bunches and wrap stems to slow ethylene release and ripening' },
      { icon: '🍌', text: 'Overripe bananas are perfect for chips (₹150-250/kg), flour, or bakery supply (₹20-30/kg)' },
      { icon: '⚡', text: 'For biogas production, banana waste generates excellent methane yield' },
    ],
  },
  potato: {
    optimal_temp: '4-8°C',
    optimal_humidity: '90-95%',
    tips: [
      { icon: '🌡️', text: 'Store at 4-8°C in dark, well-ventilated conditions to prevent sprouting' },
      { icon: '🌑', text: 'Keep away from light — light exposure causes greening (solanine, toxic)' },
      { icon: '🧅', text: 'Store separately from onions — both release gases that accelerate each other\'s spoilage' },
      { icon: '🍟', text: 'Slightly damaged potatoes can be processed into chips, fries, or starch — value up to ₹150/kg' },
    ],
  },
  onion: {
    optimal_temp: '0-4°C',
    optimal_humidity: '65-70%',
    tips: [
      { icon: '🌡️', text: 'Store at 0-4°C with LOW humidity (65-70%) — onions rot fast in high humidity' },
      { icon: '🌬️', text: 'Ensure good air circulation with mesh bags, not plastic — trapped moisture causes fungal rot' },
      { icon: '🧄', text: 'Cure onions for 2-3 weeks before storage to toughen outer layers' },
      { icon: '☀️', text: 'Damaged onions can be dehydrated into flakes/powder — export value ₹150-300/kg' },
    ],
  },
  cauliflower: {
    optimal_temp: '0-2°C',
    optimal_humidity: '95-98%',
    tips: [
      { icon: '🌡️', text: 'Store at 0-2°C with very high humidity (95-98%) — cauliflower wilts extremely fast' },
      { icon: '🥦', text: 'Keep leaves attached to protect the curd and slow yellowing' },
      { icon: '📦', text: 'Use perforated plastic bags to maintain humidity without condensation' },
      { icon: '🥒', text: 'Quick pickle or freeze blanched cauliflower to extend usable life by weeks' },
    ],
  },
  capsicum: {
    optimal_temp: '7-10°C',
    optimal_humidity: '90-95%',
    tips: [
      { icon: '🌡️', text: 'Store at 7-10°C — below 7°C causes pitting and water-soaked spots' },
      { icon: '📦', text: 'Use shallow containers with good ventilation to prevent fungal growth' },
      { icon: '🥫', text: 'Slightly soft capsicums are perfect for roasting, pickling, or making paste' },
      { icon: '☀️', text: 'Dehydrated capsicum flakes sell at ₹200-400/kg in spice markets' },
    ],
  },
}

export default function SpoilageAssessment({ produceData }) {
  const [loading, setLoading] = useState(false)
  const [weatherImpact, setWeatherImpact] = useState(null)
  const [spoilageAssessment, setSpoilageAssessment] = useState(null)
  const [storageType, setStorageType] = useState('ambient')
  const [currentTemp, setCurrentTemp] = useState('')
  const [currentHumidity, setCurrentHumidity] = useState('')
  const [harvestDaysAgo, setHarvestDaysAgo] = useState(1)

  const fetchWeatherImpact = async () => {
    setLoading(true)
    try {
      // Fetch weather impact
      const response = await axios.get('/api/v1/spoilage/weather-impact', {
        params: {
          crop_name: produceData.cropName,
          lat: produceData.latitude,
          lng: produceData.longitude,
        },
      })
      setWeatherImpact(response.data)

      // Also fetch detailed spoilage assessment with recs
      try {
        const temp = response.data?.weather?.temperature || response.data?.weather?.temp || 30
        const humidity = response.data?.weather?.humidity || 70
        const assessResp = await axios.post('/api/v1/spoilage/assess', {
          crop_name: produceData.cropName,
          quantity_kg: produceData.quantity || 100,
          storage_type: storageType,
          days_since_harvest: harvestDaysAgo,
          current_temp: temp,
          current_humidity: humidity,
          batch_id: 1,
        })
        setSpoilageAssessment(assessResp.data)
      } catch (e) {
        console.warn('Spoilage assess secondary call failed:', e)
      }
    } catch (error) {
      console.error('Weather impact fetch failed:', error)
      alert('Failed to fetch weather impact on spoilage. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const riskColors = {
    low: { bg: 'bg-green-50', border: 'border-green-500', text: 'text-green-700', badge: 'badge-success' },
    medium: { bg: 'bg-yellow-50', border: 'border-yellow-500', text: 'text-yellow-700', badge: 'badge-warning' },
    high: { bg: 'bg-orange-50', border: 'border-orange-500', text: 'text-orange-700', badge: 'badge-warning' },
    critical: { bg: 'bg-red-50', border: 'border-red-500', text: 'text-red-700', badge: 'badge-danger' },
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="card">
        <div className="flex items-center gap-3 mb-6">
          <ShieldAlert className="w-8 h-8 text-orange-600" />
          <div>
            <h2 className="text-2xl font-bold text-gray-800">Spoilage Risk Assessment</h2>
            <p className="text-gray-600 text-sm">Check weather impact on spoilage and shelf-life predictions</p>
          </div>
        </div>

        {/* Weather Impact Section */}
        <div className="bg-orange-50 border border-orange-200 rounded-lg p-4 mb-4">
          <h3 className="font-semibold text-orange-900 mb-2 flex items-center gap-2">
            <CloudRain className="w-5 h-5" />
            Weather Impact on Spoilage
          </h3>
          <p className="text-sm text-orange-800 mb-3">
            Check how current weather at your location affects spoilage risk for {produceData.cropName}.
          </p>
          <div className="flex items-center gap-3 text-sm text-orange-700">
            <span>📍 {produceData.location}</span>
            <span>({produceData.latitude?.toFixed(2)}, {produceData.longitude?.toFixed(2)})</span>
          </div>
        </div>

        <button
          onClick={fetchWeatherImpact}
          disabled={loading}
          className="w-full btn-primary py-3 text-lg"
        >
          {loading ? (
            <span className="flex items-center justify-center">
              <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              Analyzing...
            </span>
          ) : (
            '🌦️ Check Weather Impact on Spoilage'
          )}
        </button>
      </div>

      {/* Weather Impact Results */}
      {weatherImpact && (
        <div className="space-y-6">
          {/* Voice Summary */}
          <div className="flex justify-end">
            <SpeakButton
              text={(() => {
                let t = `Spoilage risk assessment for ${produceData.cropName} at ${produceData.location}. `
                if (weatherImpact.overall_impact) {
                  const risk = weatherImpact.overall_impact === 'negative' ? 'High' : weatherImpact.overall_impact === 'neutral' ? 'Medium' : 'Low'
                  t += `Overall risk level: ${risk}. `
                }
                if (weatherImpact.advisory) t += `Advisory: ${weatherImpact.advisory}. `
                if (weatherImpact.weather) {
                  const w = weatherImpact.weather
                  t += `Current weather: Temperature ${w.temperature?.toFixed(1) || w.temp || 'unknown'} degrees Celsius, Humidity ${w.humidity || 'unknown'} percent. `
                  if (w.description) t += `Conditions: ${w.description}. `
                }
                if (weatherImpact.risk_factors?.length > 0) {
                  t += 'Risk factors: ' + weatherImpact.risk_factors.map(rf => `${rf.factor} is ${rf.severity} severity, ${rf.impact}`).join('. ') + '.'
                }
                return t
              })()}
              textHindi={(() => {
                let t = `${produceData.cropName} के लिए खराब होने का जोखिम आकलन। `
                if (weatherImpact.overall_impact) {
                  const risk = weatherImpact.overall_impact === 'negative' ? 'उच्च' : weatherImpact.overall_impact === 'neutral' ? 'मध्यम' : 'कम'
                  t += `जोखिम का स्तर: ${risk}। `
                }
                if (weatherImpact.advisory) t += `सलाह: ${weatherImpact.advisory}। `
                return t
              })()}
              label="Read Results"
              size="md"
            />
          </div>

          {/* Risk Level */}
          {weatherImpact.overall_impact && (
            <div className={`card border-l-4 ${
              weatherImpact.overall_impact === 'negative' ? riskColors.high?.border :
              weatherImpact.overall_impact === 'neutral' ? riskColors.medium?.border :
              riskColors.low?.border
            } ${
              weatherImpact.overall_impact === 'negative' ? riskColors.high?.bg :
              weatherImpact.overall_impact === 'neutral' ? riskColors.medium?.bg :
              riskColors.low?.bg
            }`}>
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-xl font-bold text-gray-800">Spoilage Risk Level</h3>
                <span className={
                  weatherImpact.overall_impact === 'negative' ? riskColors.high?.badge :
                  weatherImpact.overall_impact === 'neutral' ? riskColors.medium?.badge :
                  riskColors.low?.badge
                }>
                  {weatherImpact.overall_impact === 'negative' ? 'HIGH' :
                   weatherImpact.overall_impact === 'neutral' ? 'MEDIUM' : 'LOW'}
                </span>
              </div>
              {weatherImpact.advisory && (
                <p className="text-gray-700">{weatherImpact.advisory}</p>
              )}
            </div>
          )}

          {/* Current Weather */}
          {weatherImpact.weather && (
            <div className="card">
              <h3 className="text-lg font-bold text-gray-800 mb-4 flex items-center gap-2">
                <CloudRain className="w-5 h-5 text-blue-600" />
                Current Weather Conditions
              </h3>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="bg-red-50 p-4 rounded-lg text-center">
                  <Thermometer className="w-6 h-6 text-red-600 mx-auto mb-2" />
                  <p className="text-2xl font-bold text-gray-800">
                    {weatherImpact.weather.temperature?.toFixed(1) || weatherImpact.weather.temp || '—'}°C
                  </p>
                  <p className="text-sm text-gray-600">Temperature</p>
                </div>
                <div className="bg-blue-50 p-4 rounded-lg text-center">
                  <Droplets className="w-6 h-6 text-blue-600 mx-auto mb-2" />
                  <p className="text-2xl font-bold text-gray-800">
                    {weatherImpact.weather.humidity || '—'}%
                  </p>
                  <p className="text-sm text-gray-600">Humidity</p>
                </div>
                {weatherImpact.weather.wind_speed !== undefined && (
                  <div className="bg-gray-50 p-4 rounded-lg text-center">
                    <p className="text-2xl font-bold text-gray-800">
                      {weatherImpact.weather.wind_speed?.toFixed(1) || '—'}
                    </p>
                    <p className="text-sm text-gray-600">Wind Speed (km/h)</p>
                  </div>
                )}
                {weatherImpact.weather.description && (
                  <div className="bg-gray-50 p-4 rounded-lg text-center">
                    <p className="text-lg font-bold text-gray-800 capitalize">
                      {weatherImpact.weather.description}
                    </p>
                    <p className="text-sm text-gray-600">Conditions</p>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Risk Factors (from backend risk_factors array) */}
          {weatherImpact.risk_factors && weatherImpact.risk_factors.length > 0 && (
            <div className="card">
              <h3 className="text-lg font-bold text-gray-800 mb-4 flex items-center gap-2">
                <Leaf className="w-5 h-5 text-green-600" />
                Risk Factors for {produceData.cropName}
              </h3>
              <div className="space-y-3">
                {weatherImpact.risk_factors.map((rf, idx) => {
                  const severityColors = {
                    high: 'border-red-300 bg-red-50',
                    medium: 'border-yellow-300 bg-yellow-50',
                    low: 'border-green-300 bg-green-50',
                  };
                  const icon = rf.factor?.toLowerCase().includes('temp')
                    ? <Thermometer className="w-4 h-4 text-red-500" />
                    : rf.factor?.toLowerCase().includes('humid')
                    ? <Droplets className="w-4 h-4 text-blue-500" />
                    : <Clock className="w-4 h-4 text-purple-500" />;
                  return (
                    <div key={idx} className={`p-4 rounded-lg border ${severityColors[rf.severity] || 'border-gray-200 bg-gray-50'}`}>
                      <div className="flex items-center justify-between mb-1">
                        <div className="flex items-center gap-2">
                          {icon}
                          <span className="font-semibold text-gray-800 capitalize">{rf.factor}</span>
                        </div>
                        <span className={`text-xs px-2 py-0.5 rounded-full font-semibold ${
                          rf.severity === 'high' ? 'bg-red-100 text-red-700' :
                          rf.severity === 'medium' ? 'bg-yellow-100 text-yellow-700' :
                          'bg-green-100 text-green-700'
                        }`}>{rf.severity}</span>
                      </div>
                      <p className="text-sm text-gray-600">{rf.impact}</p>
                      {rf.value && <p className="text-xs text-gray-500 mt-1">Current: {rf.value}</p>}
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* 🤖 AI Spoilage Recommendations from /assess endpoint */}
          {spoilageAssessment && (
            <div className="card border-l-4 border-orange-500 bg-orange-50">
              <h3 className="text-lg font-bold text-gray-800 mb-4 flex items-center gap-2">
                <AlertTriangle className="w-5 h-5 text-orange-600" />
                🤖 AI Spoilage Recommendations
              </h3>

              {/* Risk + Shelf Life badges */}
              <div className="flex flex-wrap gap-3 mb-4">
                {spoilageAssessment.spoilage_risk && (
                  <span className={`px-3 py-1 rounded-full text-sm font-bold ${
                    spoilageAssessment.spoilage_risk === 'critical' ? 'bg-red-100 text-red-800' :
                    spoilageAssessment.spoilage_risk === 'high' ? 'bg-orange-100 text-orange-800' :
                    spoilageAssessment.spoilage_risk === 'medium' ? 'bg-yellow-100 text-yellow-800' :
                    'bg-green-100 text-green-800'
                  }`}>
                    {spoilageAssessment.spoilage_risk === 'critical' ? '🔴' :
                     spoilageAssessment.spoilage_risk === 'high' ? '🟠' :
                     spoilageAssessment.spoilage_risk === 'medium' ? '🟡' : '🟢'}{' '}
                    Risk: {spoilageAssessment.spoilage_risk.toUpperCase()}
                  </span>
                )}
                {spoilageAssessment.remaining_shelf_life_days !== undefined && (
                  <span className={`px-3 py-1 rounded-full text-sm font-bold ${
                    spoilageAssessment.remaining_shelf_life_days <= 1 ? 'bg-red-100 text-red-800' :
                    spoilageAssessment.remaining_shelf_life_days <= 3 ? 'bg-yellow-100 text-yellow-800' :
                    'bg-green-100 text-green-800'
                  }`}>
                    ⏰ Shelf Life: {spoilageAssessment.remaining_shelf_life_days} day(s) remaining
                  </span>
                )}
              </div>

              {/* Recommendations list */}
              {spoilageAssessment.recommendations && spoilageAssessment.recommendations.length > 0 && (
                <div className="space-y-2 mb-4">
                  {spoilageAssessment.recommendations.map((rec, idx) => (
                    <div key={idx} className="flex items-start gap-2 bg-white/70 p-3 rounded-lg border border-orange-200">
                      <span className="text-lg flex-shrink-0">{rec.startsWith('⚠️') || rec.startsWith('🔴') ? '' : '💡'}</span>
                      <p className="text-sm text-gray-800">{rec}</p>
                    </div>
                  ))}
                </div>
              )}

              {/* Causal Explanation */}
              {spoilageAssessment.explanation && (
                <div className="bg-white/80 p-4 rounded-lg border border-orange-200">
                  <h4 className="font-semibold text-gray-800 mb-2 flex items-center gap-2">
                    <Lightbulb className="w-4 h-4 text-yellow-600" />
                    Why this risk level?
                  </h4>
                  <p className="text-sm text-gray-700 leading-relaxed whitespace-pre-line">{spoilageAssessment.explanation}</p>
                </div>
              )}
            </div>
          )}

          {/* 📦 Crop-Specific Storage & Handling Tips */}
          {(() => {
            const cropKey = produceData.cropName?.toLowerCase()
            const advice = CROP_STORAGE_ADVICE[cropKey]
            if (!advice) return null
            return (
              <div className="card border-l-4 border-teal-500 bg-teal-50">
                <h3 className="text-lg font-bold text-gray-800 mb-4 flex items-center gap-2">
                  <Package className="w-5 h-5 text-teal-600" />
                  📦 Storage & Handling Tips for {produceData.cropName}
                </h3>
                <div className="mb-3 text-sm text-teal-800">
                  <span className="font-semibold">Optimal Conditions:</span> {advice.optimal_temp}, {advice.optimal_humidity} humidity
                </div>
                <div className="space-y-2">
                  {advice.tips.map((tip, idx) => (
                    <div key={idx} className="flex items-start gap-3 bg-white/70 p-3 rounded-lg border border-teal-200">
                      <span className="text-lg flex-shrink-0">{tip.icon}</span>
                      <p className="text-sm text-gray-800">{tip.text}</p>
                    </div>
                  ))}
                </div>
              </div>
            )
          })()}

          {/* 💡 Value-Added Alternatives for high/critical risk */}
          {spoilageAssessment && (spoilageAssessment.spoilage_risk === 'high' || spoilageAssessment.spoilage_risk === 'critical') && (
            <div className="card border-l-4 border-purple-500 bg-purple-50">
              <h3 className="text-lg font-bold text-gray-800 mb-4 flex items-center gap-2">
                <Lightbulb className="w-5 h-5 text-purple-600" />
                💡 Value-Added Alternatives — Don't Let It Go to Waste!
              </h3>
              <p className="text-sm text-gray-600 mb-4">
                Your {produceData.cropName} has {spoilageAssessment.spoilage_risk} spoilage risk. Consider these processing options to recover value:
              </p>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {(() => {
                  const crop = produceData.cropName?.toLowerCase()
                  const alternatives = {
                    tomato: [
                      { name: 'Tomato Puree / Paste', price: '₹30-50/kg', desc: 'Simple processing, huge demand from restaurants & food industry' },
                      { name: 'Sun-Dried Tomatoes', price: '₹200-400/kg', desc: 'Premium export product — air-dry or use solar dehydrator' },
                      { name: 'Tomato Ketchup', price: '₹80-120/kg', desc: 'Small-batch artisanal ketchup sells well at local markets' },
                      { name: 'Tomato Powder', price: '₹300-500/kg', desc: 'Dehydrate & grind — long shelf life, easy to ship' },
                    ],
                    mango: [
                      { name: 'Mango Pulp / Aam Ras', price: '₹60-100/kg', desc: 'High demand year-round, can be frozen for off-season sales' },
                      { name: 'Mango Pickle (Aachar)', price: '₹100-200/kg', desc: 'Traditional recipe, long shelf life, great margins' },
                      { name: 'Mango Jam / Chutney', price: '₹80-150/kg', desc: 'Value-added product popular in urban markets' },
                      { name: 'Dried Mango Slices', price: '₹200-350/kg', desc: 'Healthy snack category — growing rapidly' },
                    ],
                    banana: [
                      { name: 'Banana Chips', price: '₹150-250/kg', desc: 'Kerala-style chips have huge market across India' },
                      { name: 'Banana Flour', price: '₹100-180/kg', desc: 'Gluten-free flour — growing health food trend' },
                      { name: 'Banana Puree', price: '₹40-80/kg', desc: 'Baby food & bakery ingredient — steady B2B demand' },
                      { name: 'Dried Banana', price: '₹120-200/kg', desc: 'Simple solar drying — popular snack item' },
                    ],
                    potato: [
                      { name: 'Potato Chips / Crisps', price: '₹150-300/kg', desc: 'Huge snack market — even small-scale production is profitable' },
                      { name: 'Potato Starch', price: '₹50-80/kg', desc: 'Industrial & food use — consistent B2B demand' },
                      { name: 'Frozen French Fries', price: '₹80-150/kg', desc: 'Restaurant supply chain — growing with QSR expansion' },
                      { name: 'Potato Flour', price: '₹60-100/kg', desc: 'Gluten-free baking ingredient' },
                    ],
                    onion: [
                      { name: 'Dehydrated Onion Flakes', price: '₹150-300/kg', desc: 'Export quality product — India is #1 exporter' },
                      { name: 'Onion Powder', price: '₹200-400/kg', desc: 'Spice market staple — long shelf life' },
                      { name: 'Onion Paste', price: '₹60-100/kg', desc: 'Restaurant & food service supply' },
                      { name: 'Pickled Onions', price: '₹80-150/kg', desc: 'Growing demand in urban retail' },
                    ],
                  }
                  const items = alternatives[crop] || [
                    { name: 'Dehydrated Product', price: '₹100-300/kg', desc: 'Extend shelf life significantly through solar drying' },
                    { name: 'Pickled / Preserved', price: '₹80-200/kg', desc: 'Traditional preservation method with good margins' },
                    { name: 'Juice / Pulp', price: '₹50-100/kg', desc: 'Quick processing option for immediate value recovery' },
                  ]
                  return items.map((item, idx) => (
                    <div key={idx} className="bg-white/70 p-3 rounded-lg border border-purple-200">
                      <div className="flex items-center justify-between mb-1">
                        <span className="font-semibold text-gray-800 text-sm">{item.name}</span>
                        <span className="text-xs px-2 py-0.5 rounded-full bg-green-100 text-green-700 font-bold">{item.price}</span>
                      </div>
                      <p className="text-xs text-gray-600">{item.desc}</p>
                    </div>
                  ))
                })()}
              </div>
            </div>
          )}

          {/* Raw data fallback for unexpected response shape */}
          {!weatherImpact.overall_impact && !weatherImpact.weather && !weatherImpact.risk_factors && (
            <div className="card">
              <h3 className="text-lg font-bold text-gray-800 mb-4">Weather Impact Analysis</h3>
              <pre className="bg-gray-50 p-4 rounded-lg text-sm overflow-auto max-h-60">
                {JSON.stringify(weatherImpact, null, 2)}
              </pre>
            </div>
          )}
        </div>
      )}

      {/* Info Box */}
      {!weatherImpact && !loading && (
        <div className="card text-center py-8">
          <ShieldAlert className="w-12 h-12 text-gray-300 mx-auto mb-3" />
          <p className="text-gray-500 mb-2">Check how weather affects spoilage of your produce</p>
          <p className="text-sm text-gray-400">
            Uses real-time weather data from your location to estimate spoilage risk for {produceData.cropName}
          </p>
        </div>
      )}
    </div>
  )
}

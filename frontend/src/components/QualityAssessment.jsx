import { useState } from 'react'
import axios from 'axios'
import { Upload, Camera, TrendingUp, AlertCircle, CheckCircle, Info, ImageIcon, Lightbulb, Store, Package, Leaf } from 'lucide-react'
import SpeakButton from './SpeakButton'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts'

const SAMPLE_IMAGES = [
  { src: '/samples/fresh_tomato.png', label: 'Fresh Tomato', crop: 'tomato', quality: 'fresh' },
  { src: '/samples/fresh_mango.png', label: 'Fresh Mango', crop: 'mango', quality: 'fresh' },
  { src: '/samples/rotten_tomato.png', label: 'Rotten Tomato', crop: 'tomato', quality: 'rotten' },
  { src: '/samples/rotten_banana.png', label: 'Rotten Banana', crop: 'banana', quality: 'rotten' },
]

const GRADE_COLORS = {
  excellent: '#22c55e',
  good: '#3b82f6',
  average: '#f59e0b',
  poor: '#ef4444',
  critical: '#991b1b',
}

export default function QualityAssessment({ produceData }) {
  const [selectedImage, setSelectedImage] = useState(null)
  const [previewUrl, setPreviewUrl] = useState(null)
  const [analyzing, setAnalyzing] = useState(false)
  const [results, setResults] = useState(null)

  const handleImageSelect = (e) => {
    const file = e.target.files?.[0]
    if (file) {
      setSelectedImage(file)
      setResults(null)
      const reader = new FileReader()
      reader.onloadend = () => {
        setPreviewUrl(reader.result)
      }
      reader.readAsDataURL(file)
    }
  }

  const handleSampleSelect = async (sample) => {
    try {
      const response = await fetch(sample.src)
      const blob = await response.blob()
      const file = new File([blob], sample.label.replace(/\s+/g, '_') + '.png', { type: 'image/png' })
      setSelectedImage(file)
      setPreviewUrl(sample.src)
      setResults(null)
    } catch (err) {
      console.error('Failed to load sample image:', err)
    }
  }

  const handleAnalyze = async () => {
    if (!selectedImage) return

    setAnalyzing(true)
    
    try {
      // Create FormData for image upload
      const formData = new FormData()
      formData.append('file', selectedImage)
      
      // Backend expects crop_name, quantity_kg, storage_type as query params
      const params = new URLSearchParams({
        crop_name: produceData.cropName,
        quantity_kg: produceData.quantity,
        storage_type: 'ambient',
      })
      
      // Call backend API
      const response = await axios.post(`/api/v1/quality/assess-and-price?${params}`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      })
      
      // Transform backend response into the shape our UI expects
      const data = response.data
      const qa = data.quality_assessment || {}
      const pr = data.price_recommendation || {}
      
      const grade = qa.overall_grade || 'average'
      const qualityScore = qa.quality_score || 50
      const damageScore = qa.damage_score || 0
      
      // Map damage score to level
      let damageLevel = 'none'
      if (damageScore > 60) damageLevel = 'severe'
      else if (damageScore > 30) damageLevel = 'moderate'
      else if (damageScore > 10) damageLevel = 'minor'
      
      // Estimate shelf life from quality
      const shelfLifeMap = { excellent: 7, good: 5, average: 3, poor: 1, critical: 0 }
      const storageTempMap = { excellent: 4, good: 4, average: 8, poor: 2, critical: 2 }
      
      // Extract AI recommendations from backend
      const recs = qa.recommendations || {}
      const bedrock = qa.bedrock_recommendations || {}
      
      const transformed = {
        freshness: {
          grade: grade,
          score: qualityScore,
          confidence: Math.round((qa.confidence || 0.75) * 100),
          predicted_class: qa.predicted_class || qa.freshness_status || 'unknown',
          days_since_harvest: qa.ripeness_level === 'overripe' ? 5 : qa.ripeness_level === 'ripe' ? 2 : 1,
        },
        damage: {
          damage_score: damageScore,
          damage_level: damageLevel,
          types: qa.defects_detected || [],
        },
        spoilage: {
          shelf_life_days: shelfLifeMap[grade] || 3,
          storage_temp: storageTempMap[grade] || 4,
          confidence_level: qualityScore > 70 ? 'high' : qualityScore > 40 ? 'medium' : 'low',
        },
        pricing: {
          sellable: pr.sellable !== undefined ? pr.sellable : true,
          action: pr.action || 'sell_now',
          recommended_price: pr.ideal_price || 0,
          min_price: pr.recommended_min_price || 0,
          max_price: pr.recommended_max_price || 0,
          msp_price: pr.predicted_market_price || 0,
          recommendation_text: pr.recommendation_text || '',
        },
        recommendations: {
          english: recs.english || bedrock.recommendation_en || '',
          hindi: recs.hindi || bedrock.recommendation_hi || '',
          storage_tips_en: recs.storage_tips_en || bedrock.storage_tips_en || '',
          storage_tips_hi: recs.storage_tips_hi || bedrock.storage_tips_hi || '',
          selling_strategy_en: recs.selling_strategy_en || bedrock.selling_strategy_en || '',
          selling_strategy_hi: recs.selling_strategy_hi || bedrock.selling_strategy_hi || '',
          urgency: recs.urgency || bedrock.urgency || 'medium',
          action: recs.action || bedrock.action || 'sell_soon',
          source: recs.source || bedrock.source || 'ai',
        },
      }
      
      setResults(transformed)
      setAnalyzing(false)
    } catch (error) {
      console.error('Quality assessment failed:', error)
      setAnalyzing(false)
      // Show error message to user
      alert('Failed to analyze image. Please try again.')
    }
  }

  const getGradeInfo = (grade) => {
    const info = {
      excellent: { label: 'Excellent', icon: '🌟', color: 'text-green-700', bg: 'bg-green-100', border: 'border-green-500' },
      good: { label: 'Good', icon: '✓', color: 'text-blue-700', bg: 'bg-blue-100', border: 'border-blue-500' },
      average: { label: 'Average', icon: '~', color: 'text-yellow-700', bg: 'bg-yellow-100', border: 'border-yellow-500' },
      poor: { label: 'Poor', icon: '!', color: 'text-red-700', bg: 'bg-red-100', border: 'border-red-500' },
      critical: { label: 'Critical', icon: '✗', color: 'text-red-900', bg: 'bg-red-200', border: 'border-red-700' },
    }
    return info[grade] || info.average
  }

  return (
    <div className="space-y-6">
      <div className="card">
        <h2 className="text-2xl font-bold text-gray-800 mb-2 flex items-center">
          <Camera className="w-7 h-7 mr-2 text-primary-600" />
          AI-Powered Quality Assessment
        </h2>
        <p className="text-gray-600 mb-6">
          Upload images of your produce to get instant freshness analysis, damage assessment, and price recommendations.
        </p>

        {/* Upload Section */}
        <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center hover:border-primary-500 transition-colors">
          <input
            type="file"
            accept="image/*"
            onChange={handleImageSelect}
            className="hidden"
            id="image-upload"
          />
          <label htmlFor="image-upload" className="cursor-pointer">
            <Upload className="w-16 h-16 mx-auto text-gray-400 mb-4" />
            <p className="text-lg font-medium text-gray-700 mb-2">
              Click to upload or drag and drop
            </p>
            <p className="text-sm text-gray-500">
              PNG, JPG, JPEG up to 10MB
            </p>
          </label>
        </div>

        {/* Sample Images */}
        <div className="mt-6">
          <p className="text-sm font-semibold text-gray-600 mb-3 flex items-center">
            <ImageIcon className="w-4 h-4 mr-1.5" />
            Or try a sample image:
          </p>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            {SAMPLE_IMAGES.map((sample) => (
              <button
                key={sample.label}
                onClick={() => handleSampleSelect(sample)}
                className={`group relative rounded-lg overflow-hidden border-2 transition-all hover:shadow-lg hover:scale-[1.03] ${
                  previewUrl === sample.src
                    ? 'border-primary-500 ring-2 ring-primary-300'
                    : 'border-gray-200 hover:border-primary-400'
                }`}
              >
                <img
                  src={sample.src}
                  alt={sample.label}
                  className="w-full h-28 object-cover"
                />
                <div className="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent" />
                <div className="absolute bottom-0 left-0 right-0 p-2">
                  <span className="text-white text-xs font-medium">{sample.label}</span>
                  <span className={`ml-1.5 inline-block text-[10px] px-1.5 py-0.5 rounded-full font-bold ${
                    sample.quality === 'fresh'
                      ? 'bg-green-500/80 text-white'
                      : 'bg-red-500/80 text-white'
                  }`}>
                    {sample.quality === 'fresh' ? '🟢 Fresh' : '🔴 Rotten'}
                  </span>
                </div>
              </button>
            ))}
          </div>
        </div>

        {/* Preview */}
        {previewUrl && (
          <div className="mt-6">
            <img
              src={previewUrl}
              alt="Preview"
              className="max-w-md mx-auto rounded-lg shadow-lg"
            />
            <div className="mt-4 text-center">
              <button
                onClick={handleAnalyze}
                disabled={analyzing}
                className="btn-primary px-8 py-3 text-lg"
              >
                {analyzing ? (
                  <span className="flex items-center">
                    <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    Analyzing...
                  </span>
                ) : (
                  '🔍 Analyze Quality'
                )}
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Results */}
      {results && (
        <div className="space-y-6">
          {/* Voice Summary */}
          <div className="flex justify-end">
            <SpeakButton
              text={(() => {
                let t = `AI Recommendations for your ${produceData.cropName}. `
                if (results.recommendations?.urgency) t += `Urgency: ${results.recommendations.urgency}. `
                if (results.recommendations?.english) t += results.recommendations.english + '. '
                if (results.recommendations?.storage_tips_en) t += `Storage tip: ${results.recommendations.storage_tips_en}. `
                if (results.recommendations?.selling_strategy_en) t += `Selling strategy: ${results.recommendations.selling_strategy_en}. `
                if (results.pricing?.recommendation_text) t += results.pricing.recommendation_text + '. '
                if (!results.recommendations?.english && !results.pricing?.recommendation_text) {
                  t += results.pricing?.sellable
                    ? `Recommended selling price is ${results.pricing.recommended_price} rupees per kg.`
                    : 'This produce is not recommended for direct sale. Consider processing into value-added products.'
                }
                return t
              })()}
              textHindi={(() => {
                let t = `${produceData.cropName} के लिए AI सुझाव। `
                if (results.recommendations?.hindi) t += results.recommendations.hindi + '। '
                if (results.recommendations?.storage_tips_hi) t += `भंडारण सुझाव: ${results.recommendations.storage_tips_hi}। `
                if (results.recommendations?.selling_strategy_hi) t += `बिक्री रणनीति: ${results.recommendations.selling_strategy_hi}। `
                if (!results.recommendations?.hindi) {
                  t += results.pricing?.sellable
                    ? `सुझाई गई बिक्री कीमत ${results.pricing?.recommended_price} रुपये प्रति किलो है।`
                    : 'यह उपज सीधे बिक्री के लिए उपयुक्त नहीं है।'
                }
                return t
              })()}
              label="Read AI Advice"
              size="md"
            />
          </div>

          {/* Freshness Grade */}
          <div className="card">
            <h3 className="text-xl font-bold text-gray-800 mb-4">🌿 Freshness Analysis</h3>
            <div className={`${getGradeInfo(results.freshness.grade).bg} ${getGradeInfo(results.freshness.grade).border} border-l-4 p-6 rounded-lg`}>
              <div className="flex items-center justify-between mb-4">
                <div>
                  <p className="text-sm text-gray-600">Overall Grade</p>
                  <p className={`text-3xl font-bold ${getGradeInfo(results.freshness.grade).color}`}>
                    {getGradeInfo(results.freshness.grade).icon} {getGradeInfo(results.freshness.grade).label}
                  </p>
                </div>
                <div className="text-right">
                  <p className="text-sm text-gray-600">Freshness Score</p>
                  <p className="text-3xl font-bold text-gray-800">{results.freshness.score}/100</p>
                </div>
              </div>
              <div className="grid grid-cols-3 gap-4 text-center">
                <div>
                  <p className="text-sm text-gray-600">Confidence</p>
                  <p className="text-lg font-semibold">{results.freshness.confidence}%</p>
                </div>
                <div>
                  <p className="text-sm text-gray-600">Classification</p>
                  <p className="text-lg font-semibold">{results.freshness.predicted_class}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-600">Days Since Harvest</p>
                  <p className="text-lg font-semibold">{results.freshness.days_since_harvest}</p>
                </div>
              </div>
            </div>
          </div>

          {/* Damage Assessment */}
          <div className="card">
            <h3 className="text-xl font-bold text-gray-800 mb-4">🔍 Damage Assessment</h3>
            <div className="grid grid-cols-2 gap-4">
              <div className="bg-gray-50 p-4 rounded-lg">
                <p className="text-sm text-gray-600 mb-1">Damage Score</p>
                <p className="text-2xl font-bold text-gray-800">{results.damage.damage_score}%</p>
              </div>
              <div className="bg-gray-50 p-4 rounded-lg">
                <p className="text-sm text-gray-600 mb-1">Damage Level</p>
                <p className="text-2xl font-bold text-gray-800 capitalize">{results.damage.damage_level}</p>
              </div>
            </div>
            {results.damage.types.length > 0 && (
              <div className="mt-4">
                <p className="text-sm font-medium text-gray-700 mb-2">Detected Issues:</p>
                <div className="flex flex-wrap gap-2">
                  {results.damage.types.map((type, idx) => (
                    <span key={idx} className="badge-warning">
                      {type.replace('_', ' ')}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Price Recommendation */}
          <div className="card">
            <h3 className="text-xl font-bold text-gray-800 mb-4 flex items-center">
              <TrendingUp className="w-6 h-6 mr-2 text-green-600" />
              Price Recommendation
            </h3>
            
            {results.pricing.sellable ? (
              <>
                <div className={`${results.pricing.action === 'sell_now' ? 'bg-green-50 border-green-500' : 'bg-yellow-50 border-yellow-500'} border-l-4 p-4 rounded-lg mb-4`}>
                  <p className="font-semibold text-lg mb-1">
                    {results.pricing.action === 'sell_now' ? '✓ Sell Now Recommended' : '⏳ Consider Storage/Wait'}
                  </p>
                  <p className="text-sm text-gray-600">
                    Based on quality, market conditions, and shelf life analysis
                  </p>
                </div>

                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="bg-gradient-to-br from-green-50 to-green-100 p-4 rounded-lg text-center">
                    <p className="text-sm text-gray-600">Recommended</p>
                    <p className="text-2xl font-bold text-green-700">₹{results.pricing.recommended_price}</p>
                    <p className="text-xs text-gray-500">per kg</p>
                  </div>
                  <div className="bg-gray-50 p-4 rounded-lg text-center">
                    <p className="text-sm text-gray-600">Min Price</p>
                    <p className="text-xl font-semibold text-gray-700">₹{results.pricing.min_price}</p>
                    <p className="text-xs text-gray-500">per kg</p>
                  </div>
                  <div className="bg-gray-50 p-4 rounded-lg text-center">
                    <p className="text-sm text-gray-600">Max Price</p>
                    <p className="text-xl font-semibold text-gray-700">₹{results.pricing.max_price}</p>
                    <p className="text-xs text-gray-500">per kg</p>
                  </div>
                  <div className="bg-blue-50 p-4 rounded-lg text-center">
                    <p className="text-sm text-gray-600">MSP</p>
                    <p className="text-xl font-semibold text-blue-700">₹{results.pricing.msp_price}</p>
                    <p className="text-xs text-gray-500">per kg</p>
                  </div>
                </div>

                <div className="mt-4 p-3 bg-blue-50 rounded-lg">
                  <p className="text-sm text-blue-800">
                    <strong>Estimated Revenue:</strong> ₹{(results.pricing.recommended_price * produceData.quantity).toLocaleString('en-IN')}
                    {' '}for {produceData.quantity} kg
                  </p>
                </div>
              </>
            ) : (
              <div className="bg-red-50 border-l-4 border-red-500 p-4 rounded-lg">
                <p className="font-semibold text-red-800 mb-2">❌ Not Recommended for Sale</p>
                <p className="text-sm text-red-700">
                  Quality issues detected. Consider alternative uses like composting, animal feed, or biogas production.
                </p>
              </div>
            )}
          </div>

          {/* AI Farmer Recommendations */}
          {results.recommendations && (results.recommendations.english || results.recommendations.hindi) && (
            <div className="card">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-xl font-bold text-gray-800 flex items-center gap-2">
                  <Lightbulb className="w-6 h-6 text-amber-500" />
                  🤖 AI Farmer Recommendations
                </h3>
                <div className="flex items-center gap-2">
                  {results.recommendations.source === 'bedrock' && (
                    <span className="text-xs bg-purple-100 text-purple-700 px-2 py-1 rounded-full">Powered by Amazon Bedrock</span>
                  )}
                  <span className={`text-xs px-2.5 py-1 rounded-full font-bold ${
                    results.recommendations.urgency === 'critical' ? 'bg-red-100 text-red-700 animate-pulse' :
                    results.recommendations.urgency === 'high' ? 'bg-orange-100 text-orange-700' :
                    results.recommendations.urgency === 'medium' ? 'bg-yellow-100 text-yellow-700' :
                    'bg-green-100 text-green-700'
                  }`}>
                    {results.recommendations.urgency === 'critical' ? '🔴 Urgent!' :
                     results.recommendations.urgency === 'high' ? '🟠 Act Quickly' :
                     results.recommendations.urgency === 'medium' ? '🟡 Sell Soon' :
                     '🟢 No Rush'}
                  </span>
                </div>
              </div>

              {/* English Recommendations */}
              <div className="space-y-3 mb-4">
                {results.recommendations.english && (
                  <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                    <p className="text-sm font-semibold text-blue-800 mb-1">📋 Recommendation</p>
                    <p className="text-blue-900">{results.recommendations.english}</p>
                  </div>
                )}
                {results.recommendations.storage_tips_en && (
                  <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                    <p className="text-sm font-semibold text-green-800 mb-1 flex items-center gap-1">
                      <Package className="w-4 h-4" /> Storage Tips
                    </p>
                    <p className="text-green-900">{results.recommendations.storage_tips_en}</p>
                  </div>
                )}
                {results.recommendations.selling_strategy_en && (
                  <div className="bg-amber-50 border border-amber-200 rounded-lg p-4">
                    <p className="text-sm font-semibold text-amber-800 mb-1 flex items-center gap-1">
                      <Store className="w-4 h-4" /> Selling Strategy
                    </p>
                    <p className="text-amber-900">{results.recommendations.selling_strategy_en}</p>
                  </div>
                )}
              </div>

              {/* Hindi Recommendations */}
              {results.recommendations.hindi && (
                <details className="group">
                  <summary className="cursor-pointer text-sm font-semibold text-indigo-700 hover:text-indigo-900 flex items-center gap-1">
                    🇮🇳 हिंदी में सिफारिशें देखें (View in Hindi)
                  </summary>
                  <div className="mt-3 space-y-3">
                    <div className="bg-indigo-50 border border-indigo-200 rounded-lg p-4">
                      <p className="text-sm font-semibold text-indigo-800 mb-1">📋 सिफारिश</p>
                      <p className="text-indigo-900">{results.recommendations.hindi}</p>
                    </div>
                    {results.recommendations.storage_tips_hi && (
                      <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                        <p className="text-sm font-semibold text-green-800 mb-1">🏪 भंडारण सुझाव</p>
                        <p className="text-green-900">{results.recommendations.storage_tips_hi}</p>
                      </div>
                    )}
                    {results.recommendations.selling_strategy_hi && (
                      <div className="bg-amber-50 border border-amber-200 rounded-lg p-4">
                        <p className="text-sm font-semibold text-amber-800 mb-1">💰 बिक्री रणनीति</p>
                        <p className="text-amber-900">{results.recommendations.selling_strategy_hi}</p>
                      </div>
                    )}
                  </div>
                </details>
              )}
            </div>
          )}

          {/* Value-Added Alternatives for poor/critical produce */}
          {(results.freshness.grade === 'poor' || results.freshness.grade === 'critical' || !results.pricing.sellable) && (
            <div className="card border-l-4 border-amber-400">
              <h3 className="text-xl font-bold text-gray-800 mb-3 flex items-center gap-2">
                <Leaf className="w-6 h-6 text-amber-600" />
                💡 Value-Added Alternatives
              </h3>
              <p className="text-gray-600 mb-4 text-sm">
                Your produce may not fetch the best price fresh, but it can still generate income through processing:
              </p>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {[
                  { crop: 'tomato', alts: [
                    { name: 'Tomato Puree / Paste', icon: '🫙', desc: 'Process into puree, sell to food companies — ₹30-50/kg value from damaged tomatoes' },
                    { name: 'Tomato Ketchup / Sauce', icon: '🥫', desc: 'Make ketchup at home or sell to local sauce makers for ₹15-25/kg' },
                    { name: 'Sun-Dried Tomatoes', icon: '☀️', desc: 'Slice and dry — sells at ₹200-400/kg to restaurants and export buyers' },
                    { name: 'Compost / Fertilizer', icon: '🌱', desc: 'Use as organic compost for next crop cycle, saves ₹5-10/kg on fertilizer costs' },
                  ]},
                  { crop: 'mango', alts: [
                    { name: 'Mango Pulp / Jam', icon: '🫙', desc: 'Process into aam ras or jam — ₹40-80/kg value from overripe mangoes' },
                    { name: 'Mango Pickle (Aachar)', icon: '🥒', desc: 'Raw or semi-ripe mangoes make excellent pickle — ₹100-200/kg retail value' },
                    { name: 'Dried Mango (Amchur)', icon: '☀️', desc: 'Sun-dry and powder for spice — sells at ₹150-300/kg' },
                    { name: 'Animal Feed', icon: '🐄', desc: 'Damaged mangoes can feed cattle — saves on feed costs' },
                  ]},
                  { crop: 'banana', alts: [
                    { name: 'Banana Chips', icon: '🍌', desc: 'Fry into chips — raw banana chips sell at ₹150-250/kg in retail' },
                    { name: 'Banana Flour / Powder', icon: '🫙', desc: 'Dry and grind into gluten-free flour — ₹100-200/kg value' },
                    { name: 'Banana Puree for Bakeries', icon: '🍰', desc: 'Overripe bananas are ideal for baking — supply to bakeries at ₹20-30/kg' },
                    { name: 'Compost / Biogas', icon: '🌱', desc: 'Use for biogas production or composting — reduces waste and cuts fuel costs' },
                  ]},
                  { crop: 'potato', alts: [
                    { name: 'Potato Chips / Fries', icon: '🍟', desc: 'Process into chips or frozen fries — value increases to ₹80-150/kg' },
                    { name: 'Potato Starch', icon: '🫙', desc: 'Extract starch for industrial use — ₹30-50/kg' },
                    { name: 'Dehydrated Potato Flakes', icon: '☀️', desc: 'Dry into flakes for instant food — ₹100-200/kg export value' },
                    { name: 'Animal Feed', icon: '🐄', desc: 'Damaged potatoes can supplement cattle feed' },
                  ]},
                  { crop: 'onion', alts: [
                    { name: 'Dehydrated Onion Flakes', icon: '☀️', desc: 'Dry and flake — export value ₹100-200/kg, huge demand' },
                    { name: 'Onion Paste', icon: '🫙', desc: 'Process into paste for restaurants and food companies — ₹40-60/kg' },
                    { name: 'Onion Powder', icon: '🧂', desc: 'Grind into powder for spice market — ₹150-300/kg retail value' },
                    { name: 'Compost', icon: '🌱', desc: 'Use damaged onions as organic compost' },
                  ]},
                ].filter(c => c.crop === produceData.cropName?.toLowerCase()).flatMap(c => c.alts)
                 .concat(
                   !['tomato','mango','banana','potato','onion'].includes(produceData.cropName?.toLowerCase()) ? [
                     { name: 'Processing / Value Addition', icon: '🏭', desc: `Consider processing damaged ${produceData.cropName} into preserved products to recover value` },
                     { name: 'Sell to Food Processing Units', icon: '🏪', desc: 'Food processing companies buy damaged produce at 40-60% of market rate' },
                     { name: 'Compost / Animal Feed', icon: '🌱', desc: 'Use as organic compost or animal feed to reduce waste' },
                     { name: 'Donate to Food Banks', icon: '❤️', desc: 'Slightly damaged produce can be donated to food banks and NGOs' },
                   ] : []
                 ).map((alt, idx) => (
                  <div key={idx} className="bg-amber-50 border border-amber-200 rounded-lg p-3 flex items-start gap-3">
                    <span className="text-2xl">{alt.icon}</span>
                    <div>
                      <p className="font-semibold text-amber-900 text-sm">{alt.name}</p>
                      <p className="text-xs text-amber-800 mt-0.5">{alt.desc}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Price Recommendation Text from backend */}
          {results.pricing.recommendation_text && (
            <div className="card border-l-4 border-blue-400">
              <h3 className="text-lg font-bold text-gray-800 mb-2 flex items-center gap-2">
                <Info className="w-5 h-5 text-blue-600" />
                📊 AI Market Analysis
              </h3>
              <p className="text-gray-700">{results.pricing.recommendation_text}</p>
            </div>
          )}

          {/* Spoilage Prediction */}
          <div className="card">
            <h3 className="text-xl font-bold text-gray-800 mb-4">⏰ Shelf Life Prediction</h3>
            <div className="grid grid-cols-3 gap-4">
              <div className="bg-gradient-to-br from-purple-50 to-purple-100 p-4 rounded-lg text-center">
                <p className="text-sm text-gray-600">Shelf Life</p>
                <p className="text-3xl font-bold text-purple-700">{results.spoilage.shelf_life_days}</p>
                <p className="text-xs text-gray-500">days remaining</p>
              </div>
              <div className="bg-gray-50 p-4 rounded-lg text-center">
                <p className="text-sm text-gray-600">Storage Temp</p>
                <p className="text-3xl font-bold text-gray-700">{results.spoilage.storage_temp}°C</p>
                <p className="text-xs text-gray-500">recommended</p>
              </div>
              <div className="bg-gray-50 p-4 rounded-lg text-center">
                <p className="text-sm text-gray-600">Confidence</p>
                <p className="text-lg font-semibold text-gray-700 capitalize pt-2">{results.spoilage.confidence_level}</p>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

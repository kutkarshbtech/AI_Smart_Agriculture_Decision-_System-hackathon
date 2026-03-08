import { useState } from 'react'
import axios from 'axios'
import { FlaskConical, TrendingDown, Sun, Star, BarChart3, Info, Lightbulb, Package, Truck } from 'lucide-react'
import SpeakButton from './SpeakButton'

export default function CausalAnalysis({ produceData }) {
  const [analysisType, setAnalysisType] = useState('storage')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)

  const runAnalysis = async () => {
    setLoading(true)
    
    try {
      let endpoint
      let params = {
        crop_name: produceData.cropName,
        sample_size: analysisType === 'storage' ? 600 : analysisType === 'weather' ? 400 : 500
      }
      
      if (analysisType === 'storage') {
        endpoint = '/api/v1/causal/storage-spoilage'
      } else if (analysisType === 'weather') {
        endpoint = '/api/v1/causal/weather-prices'
        params.location = produceData.location.split(',')[0]
      } else {
        endpoint = '/api/v1/causal/quality-premium'
      }
      
      // Call backend API
      const response = await axios.get(endpoint, { params })
      
      if (response.data.success) {
        setResult(response.data.analysis)
      } else {
        throw new Error(response.data.message || 'Analysis failed')
      }
      
      setLoading(false)
    } catch (error) {
      console.error('Causal analysis failed:', error)
      setLoading(false)
      alert('Failed to run causal analysis. Please try again.')
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="flex items-center gap-3 mb-4">
          <FlaskConical className="w-8 h-8 text-purple-600" />
          <div>
            <h2 className="text-2xl font-bold text-gray-800">Causal Inference Insights</h2>
            <p className="text-gray-600 text-sm">Understanding cause-and-effect relationships in agricultural decisions</p>
          </div>
        </div>
        
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4">
          <h3 className="font-semibold text-blue-900 mb-2">What is Causal Analysis?</h3>
          <p className="text-sm text-blue-800">
            Causal inference helps answer "what-if" questions:
          </p>
          <ul className="text-sm text-blue-800 mt-2 space-y-1 ml-4">
            <li>🧊 <em>If I use cold storage, will my spoilage actually reduce?</em></li>
            <li>☀️ <em>Does weather causally affect prices, or is it just correlation?</em></li>
            <li>⭐ <em>How much premium will I get if I improve quality?</em></li>
          </ul>
          <p className="text-xs text-blue-700 mt-2">
            Using <strong>DoWhy</strong> (Microsoft Research), we analyze causal relationships, not just correlations.
          </p>
        </div>

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-2">
              Select Causal Question
            </label>
            <select
              value={analysisType}
              onChange={(e) => setAnalysisType(e.target.value)}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
            >
              <option value="storage">🧊 Does cold storage reduce spoilage?</option>
              <option value="weather">☀️ Does weather affect market prices?</option>
              <option value="quality">⭐ What's the quality premium?</option>
            </select>
          </div>
          
          <button
            onClick={runAnalysis}
            disabled={loading}
            className="w-full px-6 py-3 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-semibold"
          >
            {loading ? 'Running Causal Inference...' : '🔬 Run Causal Analysis'}
          </button>
        </div>
      </div>

      {/* Results Display */}
      {result && (
        <div className="space-y-6">
          {/* Voice Summary */}
          <div className="flex justify-end">
            <SpeakButton
              text={(() => {
                let t = `Causal analysis results. Question: ${result.question}. `
                const unit = analysisType === 'storage' ? 'percent' : 'rupees per kg'
                t += `Causal effect: ${result.average_treatment_effect > 0 ? 'positive ' : ''}${result.average_treatment_effect.toFixed(1)} ${unit}. `
                t += `Confidence level: ${result.confidence}. `
                if (result.interpretation) t += `Interpretation: ${result.interpretation}. `
                if (result.recommendation) t += `Recommendation: ${result.recommendation}. `
                if (result.actionable_insight) t += `Actionable insight: ${result.actionable_insight}.`
                return t
              })()}
              textHindi={(() => {
                let t = `कारण विश्लेषण परिणाम। `
                if (result.recommendation) t += `सुझाव: ${result.recommendation}। `
                if (result.actionable_insight) t += `कार्ययोजना: ${result.actionable_insight}।`
                return t
              })()}
              label="Read Results"
              size="md"
            />
          </div>

          {/* Question */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <h3 className="text-xl font-bold text-gray-800 mb-2">{result.question}</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-4">
              <div className="bg-gray-50 p-4 rounded-lg">
                <div className="text-sm text-gray-600 mb-1">Sample Size</div>
                <div className="text-2xl font-bold text-gray-800">{result.sample_size}</div>
              </div>
              <div className="bg-purple-50 p-4 rounded-lg">
                <div className="text-sm text-gray-600 mb-1">Causal Effect</div>
                <div className="text-2xl font-bold text-purple-600">
                  {result.average_treatment_effect > 0 ? '+' : ''}
                  {result.average_treatment_effect.toFixed(1)}
                  {analysisType === 'storage' ? ' %' : ' ₹/kg'}
                </div>
                {result.average_treatment_effect !== 0 && (
                  <div className={`text-xs mt-1 ${result.average_treatment_effect > 0 ? 'text-green-600' : 'text-red-600'}`}>
                    {result.average_treatment_effect > 0 ? '↑ Positive effect' : '↓ Reduces spoilage'}
                  </div>
                )}
              </div>
              <div className="bg-green-50 p-4 rounded-lg">
                <div className="text-sm text-gray-600 mb-1">Confidence</div>
                <div className="text-2xl font-bold text-green-600">{result.confidence}</div>
              </div>
            </div>
          </div>

          {/* Interpretation */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <h4 className="font-semibold text-gray-800 mb-3 flex items-center gap-2">
              <BarChart3 className="w-5 h-5 text-blue-600" />
              What This Means
            </h4>
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <p className="text-blue-900">{result.interpretation}</p>
            </div>
          </div>

          {/* Recommendation */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <h4 className="font-semibold text-gray-800 mb-3 flex items-center gap-2">
              <Star className="w-5 h-5 text-yellow-600" />
              Recommendation
            </h4>
            <div className={`rounded-lg p-4 ${
              result.confidence === 'High' 
                ? 'bg-green-50 border border-green-200' 
                : 'bg-yellow-50 border border-yellow-200'
            }`}>
              <p className={result.confidence === 'High' ? 'text-green-900' : 'text-yellow-900'}>
                {result.recommendation}
              </p>
            </div>
            {result.actionable_insight && (
              <div className="mt-3 bg-purple-50 border border-purple-200 rounded-lg p-4">
                <p className="text-purple-900 font-medium">💡 {result.actionable_insight}</p>
              </div>
            )}
          </div>

          {/* 🌾 Crop-Specific Action Plan */}
          <div className="bg-white rounded-lg shadow-md p-6 border-l-4 border-amber-500">
            <h4 className="font-semibold text-gray-800 mb-4 flex items-center gap-2">
              <Lightbulb className="w-5 h-5 text-amber-600" />
              🌾 Action Plan for {produceData.cropName} Farmers
            </h4>

            {analysisType === 'storage' && (
              <div className="space-y-3">
                <p className="text-sm text-gray-600 mb-3">
                  Based on causal analysis showing cold storage {result.average_treatment_effect < 0 ? 'reduces' : 'affects'} spoilage by {Math.abs(result.average_treatment_effect).toFixed(1)}%:
                </p>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  <div className="bg-blue-50 p-4 rounded-lg border border-blue-200">
                    <h5 className="font-semibold text-blue-800 mb-2 flex items-center gap-2">
                      <Package className="w-4 h-4" /> Cold Storage Options
                    </h5>
                    <ul className="text-sm text-blue-900 space-y-1">
                      <li>• <strong>FPO cold rooms:</strong> Shared facility, ₹1.5-3/kg/day</li>
                      <li>• <strong>Solar cold storage:</strong> Government-subsidized, low operating cost</li>
                      <li>• <strong>Coolbot units:</strong> DIY cold room using AC, ₹25,000-50,000 setup</li>
                      <li>• <strong>Zero-energy cool chambers:</strong> Free, use evaporative cooling</li>
                    </ul>
                  </div>
                  <div className="bg-orange-50 p-4 rounded-lg border border-orange-200">
                    <h5 className="font-semibold text-orange-800 mb-2">🔄 If No Cold Storage Available</h5>
                    <ul className="text-sm text-orange-900 space-y-1">
                      <li>• <strong>Sell within 24-48 hours</strong> of harvest</li>
                      <li>• <strong>Harvest early morning</strong> (5-7 AM) when temp is lowest</li>
                      <li>• <strong>Shade your produce</strong> during transport — never leave in direct sun</li>
                      <li>• <strong>Process immediately:</strong> Dry, pickle, or juice to extend value</li>
                    </ul>
                  </div>
                </div>
                <div className="bg-green-50 p-3 rounded-lg border border-green-200 mt-2">
                  <p className="text-sm text-green-800">
                    <strong>💰 ROI Calculation:</strong> If cold storage reduces spoilage by {Math.abs(result.average_treatment_effect).toFixed(0)}%
                    on 1000 kg valued at ₹20/kg, you save ₹{(Math.abs(result.average_treatment_effect) * 10 * 20 / 100).toFixed(0)} vs storage cost of ₹{(1000 * 2).toFixed(0)}.
                    {Math.abs(result.average_treatment_effect) * 10 * 20 / 100 > 2000
                      ? ' Cold storage is PROFITABLE for your batch size.'
                      : ' Consider if your batch size justifies the cost.'}
                  </p>
                </div>
              </div>
            )}

            {analysisType === 'weather' && (
              <div className="space-y-3">
                <p className="text-sm text-gray-600 mb-3">
                  Weather causally affects {produceData.cropName} prices by ₹{Math.abs(result.average_treatment_effect).toFixed(1)}/kg:
                </p>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  <div className="bg-red-50 p-4 rounded-lg border border-red-200">
                    <h5 className="font-semibold text-red-800 mb-2">🌡️ Hot Weather Strategy</h5>
                    <ul className="text-sm text-red-900 space-y-1">
                      <li>• <strong>Sell quickly:</strong> High temp = faster spoilage = lower shelf-life</li>
                      <li>• <strong>Night transport:</strong> Move produce between 8 PM and 6 AM</li>
                      <li>• <strong>Wet covering:</strong> Use wet gunny bags to reduce produce temperature</li>
                      <li>• <strong>Price advantage:</strong> Less supply at mandis during heat waves</li>
                    </ul>
                  </div>
                  <div className="bg-blue-50 p-4 rounded-lg border border-blue-200">
                    <h5 className="font-semibold text-blue-800 mb-2">🌧️ Rainy Season Strategy</h5>
                    <ul className="text-sm text-blue-900 space-y-1">
                      <li>• <strong>Higher prices:</strong> Rain reduces supply at mandis — sellers advantage</li>
                      <li>• <strong>Protect from moisture:</strong> Use tarpaulin during transport</li>
                      <li>• <strong>Avoid waterlogged markets:</strong> Produce absorbs water, reduces quality</li>
                      <li>• <strong>Plan timing:</strong> Sell on clear days between rain spells</li>
                    </ul>
                  </div>
                </div>
                <div className="bg-amber-50 p-3 rounded-lg border border-amber-200 mt-2">
                  <p className="text-sm text-amber-800">
                    <strong>📱 Action:</strong> Check weather forecast daily. Plan your mandi visit for the best weather-price window.
                    Use SwadeshAI's price forecast tab for day-by-day predictions.
                  </p>
                </div>
              </div>
            )}

            {analysisType === 'quality' && (
              <div className="space-y-3">
                <p className="text-sm text-gray-600 mb-3">
                  Quality improvement yields a ₹{Math.abs(result.average_treatment_effect).toFixed(1)}/kg premium:
                </p>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  <div className="bg-yellow-50 p-4 rounded-lg border border-yellow-200">
                    <h5 className="font-semibold text-yellow-800 mb-2">⭐ Improve Quality Grade</h5>
                    <ul className="text-sm text-yellow-900 space-y-1">
                      <li>• <strong>Grade & sort:</strong> Separate A/B/C grades — A-grade fetches 20-40% more</li>
                      <li>• <strong>Clean & wash:</strong> Remove soil, damaged parts before packing</li>
                      <li>• <strong>Proper packaging:</strong> Use CFB boxes instead of gunny bags</li>
                      <li>• <strong>Timing:</strong> Harvest at right maturity — not too early, not too late</li>
                    </ul>
                  </div>
                  <div className="bg-green-50 p-4 rounded-lg border border-green-200">
                    <h5 className="font-semibold text-green-800 mb-2">💰 Premium Market Channels</h5>
                    <ul className="text-sm text-green-900 space-y-1">
                      <li>• <strong>Direct to retail:</strong> BigBasket, JioMart, Swiggy Instamart pay 15-25% more</li>
                      <li>• <strong>Export markets:</strong> APEDA registration for global premium</li>
                      <li>• <strong>Organic certification:</strong> 30-50% premium, growing demand</li>
                      <li>• <strong>Farm-to-fork apps:</strong> Ninjacart, DeHaat, AgroStar for fair pricing</li>
                    </ul>
                  </div>
                </div>
                <div className="bg-purple-50 p-3 rounded-lg border border-purple-200 mt-2 flex items-start gap-2">
                  <Truck className="w-5 h-5 text-purple-600 flex-shrink-0 mt-0.5" />
                  <p className="text-sm text-purple-800">
                    <strong>Value Chain Tip:</strong> Every ₹1 invested in post-harvest quality (grading, packing, cold chain) typically returns ₹3-5 through better prices and reduced waste.
                  </p>
                </div>
              </div>
            )}
          </div>

          {/* Data Summary */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <h4 className="font-semibold text-gray-800 mb-4">📈 Data Summary</h4>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {analysisType === 'storage' && (
                <>
                  <div className="bg-blue-50 p-4 rounded-lg border border-blue-100">
                    <div className="text-sm font-semibold text-gray-600 mb-2">Cold Storage</div>
                    <div className="space-y-1">
                      <div className="flex justify-between text-sm">
                        <span className="text-gray-600">Avg Temperature:</span>
                        <span className="font-semibold">{result.data_summary.avg_temp_cold}°C</span>
                      </div>
                      <div className="flex justify-between text-sm">
                        <span className="text-gray-600">Avg Spoilage:</span>
                        <span className="font-semibold text-green-600">{result.data_summary.avg_spoilage_cold}%</span>
                      </div>
                    </div>
                  </div>
                  <div className="bg-orange-50 p-4 rounded-lg border border-orange-100">
                    <div className="text-sm font-semibold text-gray-600 mb-2">Ambient Storage</div>
                    <div className="space-y-1">
                      <div className="flex justify-between text-sm">
                        <span className="text-gray-600">Avg Temperature:</span>
                        <span className="font-semibold">{result.data_summary.avg_temp_ambient}°C</span>
                      </div>
                      <div className="flex justify-between text-sm">
                        <span className="text-gray-600">Avg Spoilage:</span>
                        <span className="font-semibold text-red-600">{result.data_summary.avg_spoilage_ambient}%</span>
                      </div>
                    </div>
                  </div>
                </>
              )}
              
              {analysisType === 'weather' && (
                <>
                  <div className="bg-red-50 p-4 rounded-lg border border-red-100">
                    <div className="text-sm font-semibold text-gray-600 mb-2">High Temperature</div>
                    <div className="space-y-1">
                      <div className="flex justify-between text-sm">
                        <span className="text-gray-600">Avg Price:</span>
                        <span className="font-semibold text-red-600">₹{result.data_summary.avg_price_high_temp}/kg</span>
                      </div>
                    </div>
                  </div>
                  <div className="bg-green-50 p-4 rounded-lg border border-green-100">
                    <div className="text-sm font-semibold text-gray-600 mb-2">Normal Temperature</div>
                    <div className="space-y-1">
                      <div className="flex justify-between text-sm">
                        <span className="text-gray-600">Avg Price:</span>
                        <span className="font-semibold text-green-600">₹{result.data_summary.avg_price_normal_temp}/kg</span>
                      </div>
                    </div>
                  </div>
                </>
              )}
              
              {analysisType === 'quality' && (
                <>
                  <div className="bg-yellow-50 p-4 rounded-lg border border-yellow-100">
                    <div className="text-sm font-semibold text-gray-600 mb-2">Excellent Quality</div>
                    <div className="space-y-1">
                      <div className="flex justify-between text-sm">
                        <span className="text-gray-600">Avg Price:</span>
                        <span className="font-semibold text-yellow-700">₹{result.data_summary.avg_price_excellent}/kg</span>
                      </div>
                    </div>
                  </div>
                  <div className="bg-gray-50 p-4 rounded-lg border border-gray-200">
                    <div className="text-sm font-semibold text-gray-600 mb-2">Average Quality</div>
                    <div className="space-y-1">
                      <div className="flex justify-between text-sm">
                        <span className="text-gray-600">Avg Price:</span>
                        <span className="font-semibold">₹{result.data_summary.avg_price_average}/kg</span>
                      </div>
                      <div className="flex justify-between text-sm">
                        <span className="text-gray-600">Premium:</span>
                        <span className="font-semibold text-green-600">+{result.data_summary.premium_percentage}%</span>
                      </div>
                    </div>
                  </div>
                </>
              )}
            </div>
          </div>

          {/* Methodology */}
          {result.mechanism && (
            <div className="bg-white rounded-lg shadow-md p-6">
              <h4 className="font-semibold text-gray-800 mb-3">🔗 Causal Mechanism</h4>
              <div className="bg-gray-50 p-4 rounded-lg font-mono text-sm text-gray-700">
                {result.mechanism}
              </div>
            </div>
          )}
          
          <div className="bg-white rounded-lg shadow-md p-6">
            <h4 className="font-semibold text-gray-800 mb-3 flex items-center gap-2">
              <Info className="w-5 h-5 text-blue-600" />
              Methodology
            </h4>
            <div className="text-sm text-gray-600 space-y-2">
              <p><strong>Method:</strong> {result.method}</p>
              <p className="text-xs text-gray-500">
                This analysis uses DoWhy (Microsoft Research) for rigorous causal inference. 
                Traditional analysis shows <em>correlation</em> (things happen together), but causal inference shows 
                <em>causation</em> (one thing causes another).
              </p>
            </div>
          </div>
        </div>
      )}

      {!result && !loading && (
        <div className="bg-white rounded-lg shadow-md p-12 text-center">
          <FlaskConical className="w-16 h-16 text-gray-300 mx-auto mb-4" />
          <p className="text-gray-500">Select a causal question and click "Run Causal Analysis" to see insights</p>
        </div>
      )}
    </div>
  )
}

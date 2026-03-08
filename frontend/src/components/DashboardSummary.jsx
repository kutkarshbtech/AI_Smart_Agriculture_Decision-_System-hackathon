import { useState, useEffect } from 'react'
import axios from 'axios'
import { LayoutDashboard, Package, AlertTriangle, TrendingUp, CheckCircle, RefreshCw } from 'lucide-react'

export default function DashboardSummary({ produceData }) {
  const [loading, setLoading] = useState(false)
  const [summary, setSummary] = useState(null)
  const [actions, setActions] = useState(null)
  const [farmerId, setFarmerId] = useState(1)

  const fetchDashboard = async () => {
    setLoading(true)
    try {
      const [summaryRes, actionsRes] = await Promise.all([
        axios.get(`/api/v1/dashboard/summary/${farmerId}`),
        axios.get(`/api/v1/dashboard/actions/${farmerId}`),
      ])
      setSummary(summaryRes.data)
      setActions(actionsRes.data)
    } catch (error) {
      console.error('Dashboard fetch failed:', error)
      alert('Failed to load dashboard. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchDashboard()
  }, [farmerId])

  const riskColor = (risk) => {
    const colors = {
      critical: 'bg-red-100 text-red-800 border-red-300',
      high: 'bg-orange-100 text-orange-800 border-orange-300',
      medium: 'bg-yellow-100 text-yellow-800 border-yellow-300',
      low: 'bg-green-100 text-green-800 border-green-300',
      unknown: 'bg-gray-100 text-gray-600 border-gray-300',
    }
    return colors[risk] || colors.unknown
  }

  const actionIcon = (action) => {
    if (action?.includes('sell')) return '💰'
    if (action?.includes('store') || action?.includes('wait')) return '🧊'
    if (action?.includes('process')) return '🏭'
    return '📋'
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            <LayoutDashboard className="w-8 h-8 text-teal-600" />
            <div>
              <h2 className="text-2xl font-bold text-gray-800">Farmer Dashboard</h2>
              <p className="text-gray-600 text-sm">Aggregated overview of your batches, risks, and recommendations</p>
            </div>
          </div>
          <button
            onClick={fetchDashboard}
            disabled={loading}
            className="btn-secondary flex items-center gap-2"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </button>
        </div>

        {/* Farmer ID Selector (for demo) */}
        <div className="bg-teal-50 border border-teal-200 rounded-lg p-3 text-sm text-teal-800">
          <label className="font-medium mr-2">Farmer ID (demo):</label>
          <select
            className="input-field w-auto text-sm py-1 inline-block"
            value={farmerId}
            onChange={(e) => setFarmerId(parseInt(e.target.value))}
          >
            {[1, 2, 3, 4, 5].map((id) => (
              <option key={id} value={id}>Farmer #{id}</option>
            ))}
          </select>
        </div>
      </div>

      {loading && (
        <div className="card text-center py-12">
          <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-teal-600 mx-auto mb-4"></div>
          <p className="text-gray-500">Loading dashboard...</p>
        </div>
      )}

      {summary && !loading && (
        <>
          {/* Summary Cards */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="card text-center">
              <Package className="w-8 h-8 text-blue-600 mx-auto mb-2" />
              <p className="text-3xl font-bold text-gray-800">{summary.active_batches}</p>
              <p className="text-sm text-gray-600">Active Batches</p>
            </div>
            <div className="card text-center">
              <TrendingUp className="w-8 h-8 text-green-600 mx-auto mb-2" />
              <p className="text-3xl font-bold text-gray-800">{summary.total_quantity_kg?.toLocaleString('en-IN') || 0}</p>
              <p className="text-sm text-gray-600">Total Quantity (kg)</p>
            </div>
            <div className="card text-center">
              <AlertTriangle className={`w-8 h-8 mx-auto mb-2 ${summary.high_risk_batches > 0 ? 'text-red-600' : 'text-green-600'}`} />
              <p className={`text-3xl font-bold ${summary.high_risk_batches > 0 ? 'text-red-600' : 'text-green-600'}`}>
                {summary.high_risk_batches}
              </p>
              <p className="text-sm text-gray-600">High Risk</p>
            </div>
            <div className="card text-center">
              <CheckCircle className="w-8 h-8 text-purple-600 mx-auto mb-2" />
              <p className="text-3xl font-bold text-gray-800">{summary.sold_batches}</p>
              <p className="text-sm text-gray-600">Sold Batches</p>
            </div>
          </div>

          {/* Additional metrics row */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {summary.avg_quality_score && (
              <div className="card">
                <p className="text-sm text-gray-600 mb-1">Average Quality Score</p>
                <div className="flex items-baseline gap-2">
                  <p className="text-3xl font-bold text-blue-700">{summary.avg_quality_score}</p>
                  <p className="text-gray-500">/ 100</p>
                </div>
              </div>
            )}
            <div className="card">
              <p className="text-sm text-gray-600 mb-1">Pending Alerts</p>
              <p className={`text-3xl font-bold ${summary.pending_alerts > 0 ? 'text-orange-600' : 'text-gray-400'}`}>
                {summary.pending_alerts || 0}
              </p>
            </div>
            <div className="card">
              <p className="text-sm text-gray-600 mb-1">Total Batches</p>
              <p className="text-3xl font-bold text-gray-700">{summary.total_batches}</p>
            </div>
          </div>

          {/* Top Recommendation */}
          {summary.top_recommendation && (
            <div className={`card border-l-4 ${
              summary.high_risk_batches > 0 ? 'border-red-500 bg-red-50' : 'border-green-500 bg-green-50'
            }`}>
              <h3 className="font-semibold text-gray-800 mb-2">🎯 Top Recommendation</h3>
              <p className="text-gray-700">{summary.top_recommendation}</p>
            </div>
          )}
        </>
      )}

      {/* Recommended Actions */}
      {actions && actions.actions?.length > 0 && !loading && (
        <div className="card">
          <h3 className="text-xl font-bold text-gray-800 mb-4">📋 Recommended Actions</h3>
          <div className="space-y-3">
            {actions.actions.map((action, idx) => (
              <div
                key={idx}
                className="bg-gray-50 border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow"
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-lg">{actionIcon(action.action)}</span>
                      <h4 className="font-semibold text-gray-800">
                        {action.crop_name} — {action.quantity_kg} kg
                      </h4>
                      <span className={`badge border text-xs px-2 py-0.5 rounded-full ${riskColor(action.spoilage_risk)}`}>
                        {action.spoilage_risk?.toUpperCase()} RISK
                      </span>
                    </div>
                    <p className="text-sm text-gray-600 mt-1">{action.reason}</p>
                  </div>
                  <div className="text-right ml-4">
                    <p className="text-sm text-gray-500">Price Range</p>
                    <p className="text-lg font-bold text-green-700">
                      ₹{action.recommended_price_range?.min} – ₹{action.recommended_price_range?.max}
                    </p>
                    <p className="text-xs text-gray-500">per kg</p>
                  </div>
                </div>
                <div className="mt-2">
                  <span className="badge-info text-xs">{action.action?.replace(/_/g, ' ')?.toUpperCase()}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Empty State */}
      {actions && actions.actions?.length === 0 && !loading && (
        <div className="card text-center py-8">
          <Package className="w-12 h-12 text-gray-300 mx-auto mb-3" />
          <p className="text-gray-500">No active batches found for this farmer.</p>
          <p className="text-sm text-gray-400 mt-1">Register produce batches to see recommendations here.</p>
        </div>
      )}
    </div>
  )
}

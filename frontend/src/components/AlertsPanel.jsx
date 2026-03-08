import { useState, useEffect } from 'react'
import axios from 'axios'
import { Bell, BellOff, AlertTriangle, TrendingDown, Check, RefreshCw, Plus, Trash2 } from 'lucide-react'

export default function AlertsPanel({ produceData }) {
  const [loading, setLoading] = useState(false)
  const [alerts, setAlerts] = useState([])
  const [unreadCount, setUnreadCount] = useState(0)
  const [userId, setUserId] = useState(1)
  const [filterUnread, setFilterUnread] = useState(false)
  const [creatingAlert, setCreatingAlert] = useState(false)

  const fetchAlerts = async () => {
    setLoading(true)
    try {
      const response = await axios.get(`/api/v1/alerts/user/${userId}`, {
        params: { unread_only: filterUnread },
      })
      setAlerts(response.data.alerts || [])
      setUnreadCount(response.data.unread_count || 0)
    } catch (error) {
      console.error('Failed to fetch alerts:', error)
      alert('Failed to load alerts.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchAlerts()
  }, [userId, filterUnread])

  const markRead = async (alertId) => {
    try {
      await axios.post(`/api/v1/alerts/${alertId}/read`)
      setAlerts((prev) =>
        prev.map((a) => (a.id === alertId ? { ...a, is_read: true } : a))
      )
      setUnreadCount((prev) => Math.max(0, prev - 1))
    } catch (error) {
      console.error('Failed to mark alert as read:', error)
    }
  }

  const createTestSpoilageAlert = async () => {
    setCreatingAlert(true)
    try {
      await axios.post('/api/v1/alerts/test/spoilage', null, {
        params: {
          user_id: userId,
          crop_name: produceData.cropName,
          risk_level: 'high',
          remaining_days: 2,
          batch_id: 1,
        },
      })
      fetchAlerts()
    } catch (error) {
      console.error('Failed to create test alert:', error)
    } finally {
      setCreatingAlert(false)
    }
  }

  const createTestPriceAlert = async () => {
    setCreatingAlert(true)
    try {
      await axios.post('/api/v1/alerts/test/price', null, {
        params: {
          user_id: userId,
          crop_name: produceData.cropName,
          trend: 'falling',
          current_price: 18.5,
          change_pct: -8.5,
        },
      })
      fetchAlerts()
    } catch (error) {
      console.error('Failed to create test alert:', error)
    } finally {
      setCreatingAlert(false)
    }
  }

  const alertTypeConfig = {
    spoilage_warning: {
      icon: <AlertTriangle className="w-5 h-5 text-orange-600" />,
      bg: 'bg-orange-50 border-orange-200',
      badge: 'badge-warning',
    },
    price_drop: {
      icon: <TrendingDown className="w-5 h-5 text-red-600" />,
      bg: 'bg-red-50 border-red-200',
      badge: 'badge-danger',
    },
    price_surge: {
      icon: <TrendingDown className="w-5 h-5 text-green-600" />,
      bg: 'bg-green-50 border-green-200',
      badge: 'badge-success',
    },
    buyer_match: {
      icon: <Bell className="w-5 h-5 text-blue-600" />,
      bg: 'bg-blue-50 border-blue-200',
      badge: 'badge-info',
    },
  }

  const getAlertConfig = (alert) => {
    return alertTypeConfig[alert.alert_type] || alertTypeConfig.buyer_match
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            <div className="relative">
              <Bell className="w-8 h-8 text-amber-600" />
              {unreadCount > 0 && (
                <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs w-5 h-5 rounded-full flex items-center justify-center font-bold">
                  {unreadCount}
                </span>
              )}
            </div>
            <div>
              <h2 className="text-2xl font-bold text-gray-800">Alerts & Notifications</h2>
              <p className="text-gray-600 text-sm">Spoilage warnings, price drops, and buyer matches</p>
            </div>
          </div>
          <button
            onClick={fetchAlerts}
            disabled={loading}
            className="btn-secondary flex items-center gap-2"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </button>
        </div>

        {/* Controls */}
        <div className="flex flex-wrap items-center gap-4 mb-4">
          <div>
            <label className="text-sm font-medium text-gray-600 mr-2">User ID:</label>
            <select
              className="input-field w-auto text-sm py-1 inline-block"
              value={userId}
              onChange={(e) => setUserId(parseInt(e.target.value))}
            >
              {[1, 2, 3, 4, 5].map((id) => (
                <option key={id} value={id}>User #{id}</option>
              ))}
            </select>
          </div>

          <button
            onClick={() => setFilterUnread(!filterUnread)}
            className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-sm font-medium transition-colors ${
              filterUnread
                ? 'bg-amber-100 text-amber-800 border border-amber-300'
                : 'bg-gray-100 text-gray-600 border border-gray-200'
            }`}
          >
            {filterUnread ? <BellOff className="w-4 h-4" /> : <Bell className="w-4 h-4" />}
            {filterUnread ? 'Unread Only' : 'All Alerts'}
          </button>
        </div>

        {/* Create Test Alerts */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
          <p className="text-sm text-blue-800 font-medium mb-2">
            <Plus className="w-4 h-4 inline mr-1" />
            Create Test Alerts (Demo)
          </p>
          <div className="flex flex-wrap gap-2">
            <button
              onClick={createTestSpoilageAlert}
              disabled={creatingAlert}
              className="text-xs bg-orange-100 text-orange-800 border border-orange-300 px-3 py-1.5 rounded-lg hover:bg-orange-200 font-medium"
            >
              ⚠️ Spoilage Alert
            </button>
            <button
              onClick={createTestPriceAlert}
              disabled={creatingAlert}
              className="text-xs bg-red-100 text-red-800 border border-red-300 px-3 py-1.5 rounded-lg hover:bg-red-200 font-medium"
            >
              📉 Price Alert
            </button>
          </div>
        </div>
      </div>

      {/* Loading State */}
      {loading && (
        <div className="card text-center py-8">
          <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-amber-600 mx-auto mb-4"></div>
          <p className="text-gray-500">Loading alerts...</p>
        </div>
      )}

      {/* Alerts List */}
      {!loading && alerts.length > 0 && (
        <div className="space-y-3">
          {alerts.map((alert) => {
            const config = getAlertConfig(alert)
            return (
              <div
                key={alert.id}
                className={`card border ${config.bg} ${!alert.is_read ? 'ring-2 ring-amber-300' : 'opacity-80'}`}
              >
                <div className="flex items-start gap-3">
                  <div className="mt-1">{config.icon}</div>
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <h4 className="font-semibold text-gray-800">{alert.title || alert.alert_type?.toUpperCase()}</h4>
                      <span className={`${config.badge} text-xs`}>
                        {alert.alert_type}
                      </span>
                      {!alert.is_read && (
                        <span className="bg-amber-500 text-white text-xs px-2 py-0.5 rounded-full font-bold">NEW</span>
                      )}
                    </div>
                    <p className="text-sm text-gray-700">{alert.message}</p>
                    {alert.metadata && (
                      <div className="mt-2 flex flex-wrap gap-2 text-xs text-gray-500">
                        {alert.metadata.crop_name && <span>Crop: {alert.metadata.crop_name}</span>}
                        {alert.metadata.risk_level && <span>• Risk: {alert.metadata.risk_level}</span>}
                        {alert.metadata.remaining_days && <span>• {alert.metadata.remaining_days} days left</span>}
                        {alert.metadata.price && <span>• ₹{alert.metadata.price}/kg</span>}
                        {alert.metadata.change_pct && <span>• {alert.metadata.change_pct}%</span>}
                      </div>
                    )}
                    <p className="text-xs text-gray-400 mt-1">
                      {alert.created_at ? new Date(alert.created_at).toLocaleString() : ''}
                    </p>
                  </div>
                  {!alert.is_read && (
                    <button
                      onClick={() => markRead(alert.id)}
                      className="text-sm text-green-600 hover:text-green-800 flex items-center gap-1 px-2 py-1 rounded hover:bg-green-50"
                      title="Mark as read"
                    >
                      <Check className="w-4 h-4" />
                    </button>
                  )}
                </div>
              </div>
            )
          })}
        </div>
      )}

      {/* Empty State */}
      {!loading && alerts.length === 0 && (
        <div className="card text-center py-12">
          <BellOff className="w-16 h-16 text-gray-300 mx-auto mb-4" />
          <p className="text-gray-500 text-lg mb-2">No alerts yet</p>
          <p className="text-sm text-gray-400">
            Create test alerts above or wait for system-generated notifications
          </p>
        </div>
      )}
    </div>
  )
}

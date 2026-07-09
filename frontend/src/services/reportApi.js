import { mockDashboardStats, mockReportsData, mockActivities } from '../utils/mockData'
import { sleep } from '../utils/helpers'

let _backendAvailable = null

async function isBackendUp() {
  if (_backendAvailable !== null) return _backendAvailable
  try {
    const res = await fetch('/api/health', { signal: AbortSignal.timeout(2000) })
    _backendAvailable = res.ok
  } catch {
    _backendAvailable = false
  }
  setTimeout(() => { _backendAvailable = null }, 30000)
  return _backendAvailable
}

export const reportApi = {
  getDashboardStats: async () => {
    const up = await isBackendUp()
    if (up) {
      try {
        const res = await fetch('/api/stats')
        if (res.ok) {
          const data = await res.json()
          // Only use real data if sheet is connected (totalCandidates > 0 means sheet was read)
          if (data.totalCandidates > 0 || data.shortlisted > 0) return data
        }
      } catch { /* fall through */ }
    }
    await sleep(400)
    return mockDashboardStats
  },

  getReportsData: async (range = 'monthly') => {
    await sleep(500)
    return mockReportsData
  },

  getActivityLog: async () => {
    const up = await isBackendUp()
    if (up) {
      try {
        const res = await fetch('/api/activities')
        if (res.ok) {
          const data = await res.json()
          if (data.length > 0) return data
        }
      } catch { /* fall through */ }
    }
    await sleep(300)
    return mockActivities
  },

  generateSummary: async () => {
    await sleep(2000)
    return { success: true, message: 'Pipeline report generated' }
  },
}

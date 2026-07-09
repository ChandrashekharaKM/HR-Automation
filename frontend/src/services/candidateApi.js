import { mockCandidates } from '../utils/mockData'
import { sleep } from '../utils/helpers'

// ─── Determine if backend is available ───────────────────────────────────────
let _backendAvailable = null

async function isBackendUp() {
  if (_backendAvailable !== null) return _backendAvailable
  try {
    const res = await fetch('/api/health', { signal: AbortSignal.timeout(2000) })
    _backendAvailable = res.ok
  } catch {
    _backendAvailable = false
  }
  // Re-check every 30 seconds
  setTimeout(() => { _backendAvailable = null }, 30000)
  return _backendAvailable
}

// ─── Simulated in-memory store (fallback when no backend) ────────────────────
let candidates = [...mockCandidates]

// ─── Candidate API (real backend → mock fallback) ─────────────────────────────
export const candidateApi = {
  getAll: async (filters = {}) => {
    const up = await isBackendUp()
    if (up) {
      try {
        const params = new URLSearchParams()
        if (filters.status && filters.status !== 'all') params.set('status', filters.status)
        if (filters.search) params.set('search', filters.search)
        const res = await fetch(`/api/candidates?${params}`)
        if (res.ok) {
          const data = await res.json()
          // If sheet not configured yet, fall through to mock
          if (data.length > 0 || params.toString()) return data
        }
      } catch (e) { /* fall through to mock */ }
    }
    // ─ Mock fallback ─
    await sleep(300)
    let result = [...candidates]
    if (filters.status && filters.status !== 'all') result = result.filter(c => c.status === filters.status)
    if (filters.search) {
      const q = filters.search.toLowerCase()
      result = result.filter(c => c.name.toLowerCase().includes(q) || c.email.toLowerCase().includes(q) || c.college.toLowerCase().includes(q))
    }
    return result
  },

  getById: async (id) => {
    const up = await isBackendUp()
    if (up) {
      try {
        const numericId = parseInt(id)
        if (!isNaN(numericId) && numericId > 1) {
          const res = await fetch(`/api/candidates/${numericId}`)
          if (res.ok) return await res.json()
        }
      } catch { /* fall through */ }
    }
    await sleep(200)
    const c = candidates.find(c => c.id === id)
    if (!c) throw new Error('Candidate not found')
    return c
  },

  create: async (data) => {
    await sleep(400)
    const newC = { ...data, id: String(Date.now()), status: 'applied', appliedDate: new Date().toISOString() }
    candidates = [newC, ...candidates]
    return newC
  },

  update: async (id, data) => {
    await sleep(300)
    candidates = candidates.map(c => c.id === id ? { ...c, ...data } : c)
    return candidates.find(c => c.id === id)
  },

  updateStatus: async (id, status) => {
    const up = await isBackendUp()
    const numericId = parseInt(id)

    // Status values for real backend (Google Sheet values)
    const SHEET_STATUS = {
      shortlisted: 'Resume Shortlisted',
      rejected:    'Rejected',
      interview:   'Invited for Interview',
      hired:       'Hired',
      offer:       'Offer Letter Generated',
      completed:   'Internship Completed',
    }

    if (up && !isNaN(numericId) && numericId > 1) {
      try {
        const sheetStatus = SHEET_STATUS[status] || status
        const res = await fetch(`/api/candidates/${numericId}/status`, {
          method:  'PUT',
          headers: { 'Content-Type': 'application/json' },
          body:    JSON.stringify({ status: sheetStatus }),
        })
        if (res.ok) {
          candidates = candidates.map(c => c.id === id ? { ...c, status } : c)
          return { ...candidates.find(c => c.id === id), status }
        }
      } catch { /* fall through to mock */ }
    }
    await sleep(500)
    candidates = candidates.map(c => c.id === id ? { ...c, status } : c)
    return candidates.find(c => c.id === id)
  },

  delete: async (id) => {
    await sleep(300)
    candidates = candidates.filter(c => c.id !== id)
    return { success: true }
  },

  shortlist:      async (id) => candidateApi.updateStatus(id, 'shortlisted'),
  reject:         async (id) => candidateApi.updateStatus(id, 'rejected'),
  hire:           async (id) => candidateApi.updateStatus(id, 'hired'),
  markOffer:      async (id) => candidateApi.updateStatus(id, 'offer'),
  markCompleted:  async (id) => candidateApi.updateStatus(id, 'completed'),

  generateOffer: async (id) => {
    const up = await isBackendUp()
    const numericId = parseInt(id)
    if (up && !isNaN(numericId) && numericId > 1) {
      const res = await fetch(`/api/offers/generate/${numericId}`, { method: 'POST' })
      if (res.ok) return await res.json()
      const err = await res.json()
      throw new Error(err.detail || 'Failed to generate offer')
    }
    await sleep(1500)
    return { success: true, message: 'Offer letter PDF generated (Mock)', pdfUrl: `/api/offers/${id}.pdf` }
  },

  sendOffer: async (id) => {
    const up = await isBackendUp()
    const numericId = parseInt(id)
    if (up && !isNaN(numericId) && numericId > 1) {
      const res = await fetch(`/api/offers/send/${numericId}`, { method: 'POST' })
      if (res.ok) {
        await candidateApi.updateStatus(id, 'Internship Ongoing')
        return await res.json()
      }
      const err = await res.json()
      throw new Error(err.detail || 'Failed to send offer')
    }
    await sleep(1200)
    await candidateApi.markOffer(id)
    return { success: true, message: 'Offer letter sent via email (Mock)' }
  },

  generateCertificate: async (id) => {
    const up = await isBackendUp()
    const numericId = parseInt(id)
    if (up && !isNaN(numericId) && numericId > 1) {
      const res = await fetch(`/api/certs/generate/${numericId}`, { method: 'POST' })
      if (res.ok) return await res.json()
      const err = await res.json()
      throw new Error(err.detail || 'Failed to generate certificate')
    }
    await sleep(2000)
    return { success: true, message: 'Certificate generated successfully (Mock)', pdfUrl: `/api/certs/${id}.pdf` }
  },

  sendCertificate: async (id) => {
    const up = await isBackendUp()
    const numericId = parseInt(id)
    if (up && !isNaN(numericId) && numericId > 1) {
      const res = await fetch(`/api/certs/send/${numericId}`, { method: 'POST' })
      if (res.ok) {
        await candidateApi.updateStatus(id, 'Internship Completed')
        return await res.json()
      }
      const err = await res.json()
      throw new Error(err.detail || 'Failed to send certificate')
    }
    await sleep(1500)
    await candidateApi.markCompleted(id)
    return { success: true, message: 'Completion email sent (Mock)' }
  },

  sendDetailsRequest: async (id) => {
    await sleep(1000)
    return { success: true, message: 'Details collection email sent' }
  },

  sendInterviewInvite: async (id) => {
    const up = await isBackendUp()
    const numericId = parseInt(id)
    if (up && !isNaN(numericId) && numericId > 1) {
      const res = await fetch(`/api/interviews/send-invite/${numericId}`, { method: 'POST' })
      if (res.ok) return await res.json()
      const err = await res.json()
      throw new Error(err.detail || 'Failed to send invite')
    }
    await sleep(1200)
    return { success: true, message: 'Interview invite sent via email' }
  },
}

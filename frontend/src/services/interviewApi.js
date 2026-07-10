import { mockInterviews } from '../utils/mockData'
import { sleep } from '../utils/helpers'

// Load initial interviews from localStorage, fallback to mockInterviews if none exist
const LOCAL_STORAGE_KEY = 'hr_portal_interviews'
let interviews = []
try {
  const stored = localStorage.getItem(LOCAL_STORAGE_KEY)
  interviews = stored ? JSON.parse(stored) : [...mockInterviews]
} catch {
  interviews = [...mockInterviews]
}

function saveToStorage() {
  try {
    localStorage.setItem(LOCAL_STORAGE_KEY, JSON.stringify(interviews))
  } catch (e) {
    console.error('Failed to save interviews to localStorage', e)
  }
}

// Determine if backend is available
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

export const interviewApi = {
  getAll: async () => {
    const up = await isBackendUp()
    if (up) {
      try {
        const res = await fetch('/api/candidates')
        if (res.ok) {
          const candidatesList = await res.json()
          // Filter for candidates in shortlisted or interview phase
          const activeCandidates = candidatesList.filter(c => 
            c.status === 'shortlisted' || c.status === 'interview'
          )

          // Map candidates and merge with any schedule details in localStorage
          const realInterviews = activeCandidates.map(c => {
            const storedIv = interviews.find(iv => iv.candidateId === String(c.id) || iv.email === c.email)
            
            return {
              id: String(c.id),
              candidateId: String(c.id),
              candidateName: c.name,
              email: c.email,
              college: c.college || 'N/A',
              role: c.role || 'N/A',
              interviewer: storedIv?.interviewer || '',
              date: storedIv?.date || (c.appliedDate ? c.appliedDate.split(' ')[0] : 'N/A'),
              time: storedIv?.time || '',
              meetLink: storedIv?.meetLink || '',
              status: storedIv?.status || 'scheduled',
              inviteSent: c.status === 'interview' || !!storedIv?.inviteSent,
            }
          })
          
          return realInterviews
        }
      } catch (e) {
        console.error('Error fetching candidates for interviews:', e)
      }
    }
    
    // Fallback to local interviews
    await sleep(300)
    return [...interviews]
  },

  schedule: async (data) => {
    await sleep(500)
    // Remove duplicate entry for the candidate if it exists
    interviews = interviews.filter(iv => iv.candidateId !== String(data.candidateId))
    const newI = { ...data, id: String(data.candidateId), status: 'scheduled' }
    interviews = [newI, ...interviews]
    saveToStorage()
    return newI
  },

  sendInvite: async (id) => {
    const up = await isBackendUp()
    const numericId = parseInt(id)
    if (up && !isNaN(numericId) && numericId > 1) {
      try {
        const res = await fetch(`/api/interviews/send-invite/${numericId}`, { method: 'POST' })
        if (res.ok) {
          interviews = interviews.map(i => i.id === String(id) ? { ...i, inviteSent: true } : i)
          saveToStorage()
          return await res.json()
        }
        const err = await res.json()
        throw new Error(err.detail || 'Failed to send invite')
      } catch (e) {
        if (!e.message.includes('Failed to fetch')) throw e
      }
    }
    await sleep(1200)
    interviews = interviews.map(i => i.id === String(id) ? { ...i, inviteSent: true } : i)
    saveToStorage()
    return { success: true, message: 'Interview invite sent via email' }
  },

  sendInviteBulk: async (ids) => {
    const up = await isBackendUp()
    const numericIds = ids.map(id => parseInt(id)).filter(id => !isNaN(id) && id > 1)
    if (up && numericIds.length > 0) {
      const res = await fetch('/api/interviews/send-invite/bulk', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ row_ids: numericIds })
      })
      if (res.ok) {
        interviews = interviews.map(i => ids.includes(i.id) ? { ...i, inviteSent: true } : i)
        saveToStorage()
        return await res.json()
      }
      const err = await res.json()
      throw new Error(err.detail || 'Failed to send bulk invites')
    }
    await sleep(1500)
    interviews = interviews.map(i => ids.includes(i.id) ? { ...i, inviteSent: true } : i)
    saveToStorage()
    return { success: true, count: ids.length }
  },

  complete: async (id) => {
    const up = await isBackendUp()
    const numericId = parseInt(id)
    if (up && !isNaN(numericId) && numericId > 1) {
      try {
        const res = await fetch(`/api/candidates/${numericId}/status`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ status: 'Hired' })
        })
        if (res.ok) {
          interviews = interviews.map(i => i.id === String(id) ? { ...i, status: 'completed' } : i)
          saveToStorage()
          return await res.json()
        }
      } catch (e) {
        // Fall back
      }
    }
    await sleep(400)
    interviews = interviews.map(i => i.id === String(id) ? { ...i, status: 'completed' } : i)
    saveToStorage()
    return { success: true }
  },

  cancel: async (id) => {
    const up = await isBackendUp()
    const numericId = parseInt(id)
    if (up && !isNaN(numericId) && numericId > 1) {
      try {
        const res = await fetch(`/api/candidates/${numericId}/status`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ status: 'Rejected' })
        })
        if (res.ok) {
          interviews = interviews.filter(i => i.id !== String(id))
          saveToStorage()
          return await res.json()
        }
      } catch (e) {
        // Fall back
      }
    }
    await sleep(300)
    interviews = interviews.filter(i => i.id !== String(id))
    saveToStorage()
    return { success: true }
  },

  reschedule: async (id, newDate, newTime) => {
    await sleep(500)
    interviews = interviews.map(i => i.id === String(id) ? { ...i, date: newDate, time: newTime, status: 'rescheduled' } : i)
    saveToStorage()
    return { success: true }
  },
}

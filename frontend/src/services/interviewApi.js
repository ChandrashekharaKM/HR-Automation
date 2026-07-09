import { mockInterviews } from '../utils/mockData'
import { sleep } from '../utils/helpers'

let interviews = [...mockInterviews]

export const interviewApi = {
  getAll: async () => { await sleep(300); return [...interviews] },

  schedule: async (data) => {
    await sleep(500)
    const newI = { ...data, id: `i${Date.now()}`, status: 'scheduled' }
    interviews = [newI, ...interviews]
    return newI
  },

  sendInvite: async (id) => {
    await sleep(1200)
    interviews = interviews.map(i => i.id === id ? { ...i, inviteSent: true } : i)
    return { success: true, message: 'Interview invite sent via email' }
  },

  complete: async (id) => {
    await sleep(400)
    interviews = interviews.map(i => i.id === id ? { ...i, status: 'completed' } : i)
    return { success: true }
  },

  cancel: async (id) => {
    await sleep(300)
    interviews = interviews.filter(i => i.id !== id)
    return { success: true }
  },

  reschedule: async (id, newDate, newTime) => {
    await sleep(500)
    interviews = interviews.map(i => i.id === id ? { ...i, date: newDate, time: newTime, status: 'rescheduled' } : i)
    return { success: true }
  },
}

import { useState, useEffect } from 'react'
import {
  Calendar as CalIcon, List, Send, Clock, CheckCircle, XCircle,
  Video, Plus, RefreshCw, AlertCircle, CalendarRange
} from 'lucide-react'
import { interviewApi } from '../services/interviewApi'
import Avatar from '../components/Avatar'
import toast from 'react-hot-toast'

const STATUS_STYLES = {
  scheduled:   'text-blue-300 bg-blue-500/15 border-blue-500/25',
  completed:   'text-green-300 bg-green-500/15 border-green-500/25',
  rescheduled: 'text-yellow-300 bg-yellow-500/15 border-yellow-500/25',
  cancelled:   'text-red-300 bg-red-500/15 border-red-500/25',
}

export default function Interviews() {
  const [interviews, setInterviews] = useState([])
  const [loading, setLoading] = useState(true)
  const [view, setView] = useState('list') // 'list' | 'calendar'
  const [acting, setActing] = useState(null)
  
  // Date range filters and selection
  const [startDate, setStartDate] = useState('')
  const [endDate, setEndDate] = useState('')
  const [selectedIds, setSelectedIds] = useState([])

  const load = () => {
    interviewApi.getAll().then(d => { setInterviews(d); setLoading(false) })
  }
  useEffect(() => { load() }, [])

  const act = async (id, fn, msg) => {
    setActing(id)
    try { await fn(); toast.success(msg); load() }
    catch (e) { toast.error(e.message) }
    setActing(null)
  }

  // Safe date range check
  const isDateInRange = (dateStr) => {
    if (!startDate && !endDate) return true
    if (!dateStr || dateStr === 'N/A') return false
    try {
      const d = new Date(dateStr)
      if (isNaN(d.getTime())) return false
      d.setHours(0,0,0,0)
      
      if (startDate) {
        const start = new Date(startDate)
        start.setHours(0,0,0,0)
        if (d < start) return false
      }
      if (endDate) {
        const end = new Date(endDate)
        end.setHours(0,0,0,0)
        if (d > end) return false
      }
      return true
    } catch {
      return false
    }
  }

  const filteredInterviews = interviews.filter(iv => isDateInRange(iv.date))

  const handleSendAllInRange = async () => {
    const targets = filteredInterviews.filter(iv => iv.status === 'scheduled')
    if (targets.length === 0) {
      toast.error('No scheduled interviews in this range')
      return
    }
    setActing('bulk')
    const toastId = toast.loading(`Sending ${targets.length} invites...`)
    try {
      const ids = targets.map(t => t.id)
      await interviewApi.sendInviteBulk(ids)
      toast.success(`📧 Successfully sent ${targets.length} invites!`, { id: toastId })
      setSelectedIds([])
      load()
    } catch (e) {
      toast.error(e.message || 'Bulk invite sending failed', { id: toastId })
    }
    setActing(null)
  }

  const handleSendSelected = async () => {
    const targets = interviews.filter(iv => selectedIds.includes(iv.id) && iv.status === 'scheduled')
    if (targets.length === 0) {
      toast.error('No scheduled interviews selected')
      return
    }
    setActing('bulk')
    const toastId = toast.loading(`Sending ${targets.length} selected invites...`)
    try {
      const ids = targets.map(t => t.id)
      await interviewApi.sendInviteBulk(ids)
      toast.success(`📧 Successfully sent ${targets.length} invites!`, { id: toastId })
      setSelectedIds([])
      load()
    } catch (e) {
      toast.error(e.message || 'Bulk invite sending failed', { id: toastId })
    }
    setActing(null)
  }

  const toggleSelectAll = () => {
    const checkable = filteredInterviews.filter(iv => iv.status === 'scheduled')
    if (selectedIds.length === checkable.length) {
      setSelectedIds([])
    } else {
      setSelectedIds(checkable.map(iv => iv.id))
    }
  }

  const toggleSelectOne = (id) => {
    setSelectedIds(prev => 
      prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id]
    )
  }

  // Calendar setup
  const now = new Date()
  const daysInMonth = new Date(now.getFullYear(), now.getMonth() + 1, 0).getDate()
  const firstDay = new Date(now.getFullYear(), now.getMonth(), 1).getDay()
  const monthName = now.toLocaleString('default', { month: 'long', year: 'numeric' })

  const interviewsByDate = interviews.reduce((acc, iv) => {
    const d = iv.date
    if (!acc[d]) acc[d] = []
    acc[d].push(iv)
    return acc
  }, {})

  return (
    <div className="space-y-5 animate-fade-in">
      {/* Toolbar */}
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div className="flex items-center gap-2 p-1 rounded-xl bg-white/5 border border-white/10">
          <button onClick={() => setView('list')}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm transition-all ${view === 'list' ? 'bg-primary-500 text-white shadow-glow-sm' : 'text-slate-400 hover:text-white'}`}>
            <List size={14} /> List
          </button>
          <button onClick={() => setView('calendar')}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm transition-all ${view === 'calendar' ? 'bg-primary-500 text-white shadow-glow-sm' : 'text-slate-400 hover:text-white'}`}>
            <CalIcon size={14} /> Calendar
          </button>
        </div>
        <div className="flex items-center gap-2 text-sm text-slate-400">
          <AlertCircle size={14} className="text-yellow-400" />
          {interviews.filter(i => i.status === 'scheduled').length} upcoming
        </div>
      </div>

      {/* Date Range & Bulk Action Toolbar */}
      {view === 'list' && interviews.length > 0 && (
        <div className="glass-card p-4 flex flex-col md:flex-row items-stretch md:items-center justify-between gap-4">
          <div className="flex items-center gap-3 flex-wrap flex-1">
            <div className="flex items-center gap-1.5">
              <CalendarRange size={14} className="text-indigo-400" />
              <label className="text-xs text-slate-400 font-semibold">From</label>
              <input 
                type="date" 
                value={startDate} 
                onChange={(e) => setStartDate(e.target.value)} 
                className="input-field py-1 px-2.5 text-xs font-mono" 
              />
            </div>
            <div className="flex items-center gap-1.5">
              <label className="text-xs text-slate-400 font-semibold">To</label>
              <input 
                type="date" 
                value={endDate} 
                onChange={(e) => setEndDate(e.target.value)} 
                className="input-field py-1 px-2.5 text-xs font-mono" 
              />
            </div>
            {(startDate || endDate) && (
              <button 
                onClick={() => { setStartDate(''); setEndDate('') }} 
                className="text-xs text-slate-400 hover:text-white px-2 py-1 rounded bg-white/5 border border-white/10 transition-colors"
              >
                Clear Filter
              </button>
            )}
          </div>

          <div className="flex items-center gap-2 flex-wrap">
            {selectedIds.length > 0 && (
              <button 
                onClick={handleSendSelected} 
                disabled={acting === 'bulk'}
                className="bg-indigo-500 hover:bg-indigo-600 text-white text-xs px-3.5 py-2.5 rounded-xl font-bold flex items-center gap-1.5 shadow-md shadow-indigo-500/25 transition-all"
              >
                <Send size={13} /> Send Selected ({selectedIds.length})
              </button>
            )}
            
            <button 
              onClick={handleSendAllInRange} 
              disabled={acting === 'bulk' || filteredInterviews.filter(iv => iv.status === 'scheduled').length === 0}
              className={`text-xs px-3.5 py-2.5 rounded-xl font-bold flex items-center gap-1.5 transition-all ${
                filteredInterviews.filter(iv => iv.status === 'scheduled').length > 0
                  ? 'bg-gradient-to-r from-indigo-500 to-violet-600 hover:from-indigo-600 hover:to-violet-700 text-white shadow-lg shadow-indigo-500/25'
                  : 'bg-white/5 border border-white/5 text-slate-500 cursor-not-allowed'
              }`}
            >
              <Send size={13} /> Send All in Range ({filteredInterviews.filter(iv => iv.status === 'scheduled').length})
            </button>
          </div>
        </div>
      )}

      {/* List View */}
      {view === 'list' && (
        <div className="glass-card overflow-hidden">
          <div className="px-5 py-3 border-b border-white/5 flex items-center justify-between">
            <h2 className="text-sm font-semibold text-white">Interview Queue</h2>
            {filteredInterviews.filter(iv => iv.status === 'scheduled').length > 0 && (
              <label className="flex items-center gap-1.5 text-xs text-slate-400 cursor-pointer select-none">
                <input 
                  type="checkbox" 
                  checked={selectedIds.length > 0 && selectedIds.length === filteredInterviews.filter(iv => iv.status === 'scheduled').length} 
                  onChange={toggleSelectAll}
                  className="rounded border-white/10 bg-white/5 text-indigo-500 focus:ring-indigo-500/30"
                />
                Select All Scheduled
              </label>
            )}
          </div>
          {loading ? (
            <div className="p-6 text-center text-slate-500">Loading...</div>
          ) : filteredInterviews.length === 0 ? (
            <div className="py-16 text-center">
              <p className="text-4xl mb-3">📅</p>
              <p className="text-slate-400 text-sm">No interviews schedule matches filter</p>
            </div>
          ) : (
            <div className="divide-y divide-white/[0.04]">
              {filteredInterviews.map(iv => {
                const isChecked = selectedIds.includes(iv.id);
                return (
                  <div key={iv.id} className={`px-5 py-4 hover:bg-white/[0.02] transition-colors flex items-center gap-4 ${isChecked ? 'bg-indigo-500/5' : ''}`}>
                    {iv.status === 'scheduled' && (
                      <input 
                        type="checkbox" 
                        checked={isChecked} 
                        onChange={() => toggleSelectOne(iv.id)}
                        className="rounded border-white/10 bg-white/5 text-indigo-500 focus:ring-indigo-500/30 flex-shrink-0"
                      />
                    )}
                    <div className="flex-1 min-w-0 flex items-center gap-4 flex-wrap">
                      <Avatar name={iv.candidateName} size="sm" />
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 flex-wrap">
                          <p className="text-sm font-semibold text-white">{iv.candidateName}</p>
                          <span className={`text-xs px-2 py-0.5 rounded-full border capitalize ${STATUS_STYLES[iv.status] || ''}`}>
                            {iv.status}
                          </span>
                        </div>
                        <p className="text-xs text-slate-400 mt-0.5">{iv.college} · {iv.role}</p>
                      </div>
                      <div className="flex items-center gap-4 text-xs text-slate-400">
                        <span className="flex items-center gap-1.5">
                          <Clock size={12} /> {iv.date} · {iv.time}
                        </span>
                        {iv.meetLink && (
                          <a href={iv.meetLink} target="_blank" rel="noopener noreferrer"
                            className="flex items-center gap-1.5 text-primary-400 hover:text-primary-300">
                            <Video size={12} /> Join Meet
                          </a>
                        )}
                      </div>
                      <div className="flex items-center gap-2">
                        {iv.status === 'scheduled' && (
                          <>
                            <button onClick={() => act(iv.id, () => interviewApi.sendInvite(iv.id), '📧 Invite sent!')}
                              disabled={acting === iv.id} className="btn-primary text-xs px-3 py-1.5">
                              {acting === iv.id ? <RefreshCw size={12} className="animate-spin" /> : <Send size={12} />}
                              Send Invite
                            </button>
                            <button onClick={() => act(iv.id, () => interviewApi.complete(iv.id), '✅ Marked complete')}
                              disabled={acting === iv.id} className="btn-secondary text-xs px-3 py-1.5">
                              <CheckCircle size={12} /> Complete
                            </button>
                            <button onClick={() => act(iv.id, () => interviewApi.cancel(iv.id), 'Interview cancelled')}
                              disabled={acting === iv.id} className="btn-danger text-xs px-3 py-1.5">
                              <XCircle size={12} /> Cancel
                            </button>
                          </>
                        )}
                        {iv.status === 'completed' && (
                          <span className="text-xs text-green-400 flex items-center gap-1">
                            <CheckCircle size={12} /> Completed
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                )
              })}
            </div>
          )}
        </div>
      )}

      {/* Calendar View */}
      {view === 'calendar' && (
        <div className="glass-card p-5">
          <h2 className="text-sm font-semibold text-white mb-5 text-center">{monthName}</h2>
          <div className="grid grid-cols-7 gap-1 mb-2">
            {['Sun','Mon','Tue','Wed','Thu','Fri','Sat'].map(d => (
              <div key={d} className="text-xs text-center text-slate-500 py-1 font-medium">{d}</div>
            ))}
          </div>
          <div className="grid grid-cols-7 gap-1">
            {Array.from({ length: firstDay }).map((_, i) => <div key={`e-${i}`} />)}
            {Array.from({ length: daysInMonth }).map((_, i) => {
              const day = i + 1
              const dateStr = `${now.getFullYear()}-${String(now.getMonth()+1).padStart(2,'0')}-${String(day).padStart(2,'0')}`
              const dayInterviews = interviewsByDate[dateStr] || []
              const isToday = day === now.getDate()
              return (
                <div key={day} className={`calendar-cell ${isToday ? 'today' : ''}`}>
                  <p className={`text-xs font-medium mb-1 ${isToday ? 'text-primary-400' : 'text-slate-400'}`}>{day}</p>
                  {dayInterviews.map(iv => (
                    <div key={iv.id} className="text-xs bg-primary-500/20 text-primary-300 rounded px-1 py-0.5 truncate mb-0.5" title={iv.candidateName}>
                      {iv.candidateName}
                    </div>
                  ))}
                </div>
              )
            })}
          </div>
        </div>
      )}
    </div>
  )
}

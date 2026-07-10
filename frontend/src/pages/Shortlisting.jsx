import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Star, X, Eye, Sparkles, Sliders } from 'lucide-react'
import { candidateApi } from '../services/candidateApi'
import Avatar from '../components/Avatar'
import { TableSkeleton } from '../components/Loader'
import toast from 'react-hot-toast'

export default function Shortlisting() {
  const [candidates, setCandidates] = useState([])
  const [loading, setLoading] = useState(true)
  const [selectedIds, setSelectedIds] = useState([])
  const [scoreThreshold, setScoreThreshold] = useState(85)
  const [bulkActing, setBulkActing] = useState(false)
  const navigate = useNavigate()

  const load = () => {
    candidateApi.getAll({ status: 'applied' }).then(d => { 
      setCandidates(d)
      setLoading(false) 
    })
  }
  useEffect(() => { load() }, [])

  const handle = async (id, action) => {
    if (action === 'shortlist') {
      await candidateApi.shortlist(id)
      toast.success('✅ Candidate shortlisted!')
    } else {
      await candidateApi.reject(id)
      toast.success('Candidate rejected')
    }
    load()
  }

  const handleBulkShortlistByThreshold = async () => {
    setBulkActing(true)
    const toastId = toast.loading(`Shortlisting candidates with score >= ${scoreThreshold}%...`)
    try {
      const res = await candidateApi.bulkShortlist({ threshold: scoreThreshold })
      toast.success(`🎉 Successfully shortlisted ${res.count} candidates!`, { id: toastId })
      setSelectedIds([])
      load()
    } catch (e) {
      toast.error(e.message || 'Bulk shortlist failed', { id: toastId })
    }
    setBulkActing(false)
  }

  const handleBulkShortlistSelected = async () => {
    if (selectedIds.length === 0) return
    setBulkActing(true)
    const toastId = toast.loading(`Shortlisting ${selectedIds.length} selected candidates...`)
    try {
      const rowIds = selectedIds.map(id => {
        const c = candidates.find(cand => cand.id === id)
        return c ? parseInt(c.row) : parseInt(id)
      })
      const res = await candidateApi.bulkShortlist({ row_ids: rowIds })
      toast.success(`🎉 Successfully shortlisted ${res.count} candidates!`, { id: toastId })
      setSelectedIds([])
      load()
    } catch (e) {
      toast.error(e.message || 'Bulk shortlist failed', { id: toastId })
    }
    setBulkActing(false)
  }

  const toggleSelectAll = () => {
    if (selectedIds.length === candidates.length) {
      setSelectedIds([])
    } else {
      setSelectedIds(candidates.map(c => c.id))
    }
  }

  const toggleSelectOne = (id) => {
    setSelectedIds(prev => 
      prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id]
    )
  }

  return (
    <div className="space-y-5 animate-fade-in">
      <div className="glass-card p-4 flex items-center gap-3 border-l-4" style={{ borderLeftColor: '#6366f1' }}>
        <Star size={18} className="text-primary-400" />
        <p className="text-sm text-slate-300">
          Review new applications and shortlist candidates. <strong className="text-white">{candidates.length}</strong> pending.
        </p>
      </div>

      {/* Bulk Actions Panel */}
      {!loading && candidates.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Threshold bulk shortlist */}
          <div className="glass-card p-5 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
            <div className="space-y-1 flex-1 w-full">
              <div className="flex justify-between text-xs font-semibold text-slate-400">
                <span className="flex items-center gap-1.5"><Sliders size={13} className="text-indigo-400" /> Score Threshold</span>
                <span className="text-primary-400 font-bold text-sm bg-indigo-500/10 px-2 py-0.5 rounded-lg border border-indigo-500/20">{scoreThreshold}%</span>
              </div>
              <input 
                type="range" 
                min="60" 
                max="98" 
                value={scoreThreshold} 
                onChange={(e) => setScoreThreshold(parseInt(e.target.value))}
                className="w-full h-1.5 rounded-lg bg-white/10 accent-indigo-500 cursor-pointer mt-2"
              />
              <p className="text-[10px] text-slate-500 mt-1.5">
                {candidates.filter(c => c.resumeScore >= scoreThreshold).length} of {candidates.length} candidates match
              </p>
            </div>
            <button 
              onClick={handleBulkShortlistByThreshold} 
              disabled={bulkActing}
              className="btn-primary w-full sm:w-auto text-xs px-4 py-2.5 flex items-center justify-center gap-1.5 flex-shrink-0 self-end sm:self-center"
            >
              <Sparkles size={14} /> Shortlist Matching
            </button>
          </div>

          {/* Selected bulk shortlist */}
          <div className="glass-card p-5 flex items-center justify-between gap-4">
            <div className="space-y-1">
              <h3 className="text-sm font-semibold text-white">Manual Selection</h3>
              <p className="text-xs text-slate-400">
                {selectedIds.length} candidate(s) selected
              </p>
            </div>
            <button 
              onClick={handleBulkShortlistSelected} 
              disabled={selectedIds.length === 0 || bulkActing}
              className={`text-xs px-4 py-2.5 rounded-xl font-bold flex items-center gap-1.5 transition-all ${
                selectedIds.length > 0 
                  ? 'bg-gradient-to-r from-indigo-500 to-violet-600 hover:from-indigo-600 hover:to-violet-700 text-white shadow-lg shadow-indigo-500/20' 
                  : 'bg-white/5 border border-white/5 text-slate-500 cursor-not-allowed'
              }`}
            >
              <Star size={14} /> Shortlist Selected ({selectedIds.length})
            </button>
          </div>
        </div>
      )}

      <div className="glass-card overflow-hidden">
        <div className="px-5 py-3 border-b border-white/5">
          <h2 className="text-sm font-semibold text-white">Pending Applications</h2>
        </div>

        {loading ? (
          <div className="p-4"><TableSkeleton rows={4} /></div>
        ) : candidates.length === 0 ? (
          <div className="py-16 text-center">
            <p className="text-4xl mb-3">🎉</p>
            <p className="text-slate-400 text-sm">All applications reviewed!</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="data-table">
              <thead>
                <tr>
                  <th className="w-10 text-center">
                    <input 
                      type="checkbox" 
                      checked={candidates.length > 0 && selectedIds.length === candidates.length} 
                      onChange={toggleSelectAll}
                      className="rounded border-white/10 bg-white/5 text-indigo-500 focus:ring-indigo-500/30"
                    />
                  </th>
                  <th>Candidate</th>
                  <th>College</th>
                  <th>Role</th>
                  <th>Resume Score</th>
                  <th>Skills</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {candidates.map(c => {
                  const isChecked = selectedIds.includes(c.id);
                  return (
                    <tr key={c.id} className={isChecked ? 'bg-indigo-500/5 transition-colors' : 'transition-colors'}>
                      <td className="text-center">
                        <input 
                          type="checkbox" 
                          checked={isChecked} 
                          onChange={() => toggleSelectOne(c.id)}
                          className="rounded border-white/10 bg-white/5 text-indigo-500 focus:ring-indigo-500/30"
                        />
                      </td>
                      <td>
                        <div className="flex items-center gap-3">
                          <Avatar name={c.name} size="sm" />
                          <div>
                            <p className="text-sm font-medium text-white">{c.name}</p>
                            <p className="text-xs text-slate-500">{c.email}</p>
                          </div>
                        </div>
                      </td>
                      <td className="text-slate-400 text-xs">{c.college}</td>
                      <td className="text-slate-300 text-xs">{c.role}</td>
                      <td>
                        <div className="flex items-center gap-2">
                          <div className="w-20 h-1.5 rounded-full bg-white/10 overflow-hidden">
                            <div className="h-full rounded-full"
                              style={{ width: `${c.resumeScore}%`, background: c.resumeScore >= 90 ? '#22c55e' : c.resumeScore >= 75 ? '#f59e0b' : '#ef4444' }} />
                          </div>
                          <span className={`text-xs font-semibold ${c.resumeScore >= 90 ? 'text-green-400' : c.resumeScore >= 75 ? 'text-yellow-400' : 'text-red-400'}`}>
                            {c.resumeScore}%
                          </span>
                        </div>
                      </td>
                      <td>
                        <div className="flex flex-wrap gap-1">
                          {c.skills?.slice(0,2).map(s => (
                            <span key={s} className="px-2 py-0.5 rounded-full text-xs bg-primary-500/10 text-primary-300 border border-primary-500/20">{s}</span>
                          ))}
                          {c.skills?.length > 2 && <span className="text-xs text-slate-500">+{c.skills.length - 2}</span>}
                        </div>
                      </td>
                      <td>
                        <div className="flex items-center gap-2">
                          <button onClick={() => navigate(`/candidates/${c.id}`)} className="btn-ghost text-xs px-2 py-1.5">
                            <Eye size={13} /> View
                          </button>
                          <button onClick={() => handle(c.id, 'shortlist')} className="btn-primary text-xs px-3 py-1.5">
                            <Star size={13} /> Shortlist
                          </button>
                          <button onClick={() => handle(c.id, 'reject')} className="btn-danger text-xs px-3 py-1.5">
                            <X size={13} /> Reject
                          </button>
                        </div>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}

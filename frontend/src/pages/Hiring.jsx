import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { UserCheck, X, Eye, RefreshCw } from 'lucide-react'
import { candidateApi } from '../services/candidateApi'
import Avatar from '../components/Avatar'
import StatusBadge from '../components/StatusBadge'
import { TableSkeleton } from '../components/Loader'
import toast from 'react-hot-toast'

export default function Hiring() {
  const [candidates, setCandidates] = useState([])
  const [loading, setLoading] = useState(true)
  const [acting, setActing] = useState(null)
  const navigate = useNavigate()

  const load = () => {
    Promise.all([
      candidateApi.getAll({ status: 'interview' }),
      candidateApi.getAll({ status: 'accepted' }),
    ]).then(([a, b]) => { setCandidates([...a, ...b]); setLoading(false) })
  }
  useEffect(() => { load() }, [])

  const act = async (id, fn, msg) => {
    setActing(id)
    try { await fn(); toast.success(msg); load() }
    catch (e) { toast.error(e.message) }
    setActing(null)
  }

  return (
    <div className="space-y-5 animate-fade-in">
      <div className="glass-card p-4 flex items-center gap-3 border-l-4" style={{ borderLeftColor: '#22c55e' }}>
        <UserCheck size={18} className="text-green-400" />
        <p className="text-sm text-slate-300">
          Candidates who completed interviews. Make hiring decisions here.
          <strong className="text-white"> {candidates.length}</strong> pending.
        </p>
      </div>

      <div className="glass-card overflow-hidden">
        <div className="px-5 py-3 border-b border-white/5">
          <h2 className="text-sm font-semibold text-white">Pending Hiring Decisions</h2>
        </div>

        {loading ? (
          <div className="p-4"><TableSkeleton rows={4} /></div>
        ) : candidates.length === 0 ? (
          <div className="py-16 text-center">
            <p className="text-4xl mb-3">✅</p>
            <p className="text-slate-400 text-sm">No pending hiring decisions</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Candidate</th>
                  <th>College</th>
                  <th>Role</th>
                  <th>Interview Date</th>
                  <th>Status</th>
                  <th>Decision</th>
                </tr>
              </thead>
              <tbody>
                {candidates.map(c => (
                  <tr key={c.id}>
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
                    <td className="text-slate-400 text-xs">{c.interviewDate || '—'}</td>
                    <td><StatusBadge status={c.status} /></td>
                    <td>
                      <div className="flex items-center gap-2">
                        <button onClick={() => navigate(`/candidates/${c.id}`)} className="btn-ghost text-xs px-2 py-1.5">
                          <Eye size={13} /> View
                        </button>
                        <button
                          onClick={() => act(c.id, () => candidateApi.hire(c.id), `🎉 ${c.name} hired!`)}
                          disabled={acting === c.id}
                          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold text-white bg-green-500/20 border border-green-500/30 hover:bg-green-500/30 transition-all"
                        >
                          {acting === c.id ? <RefreshCw size={12} className="animate-spin" /> : <UserCheck size={13} />}
                          Hire
                        </button>
                        <button
                          onClick={() => act(c.id, () => candidateApi.reject(c.id), 'Candidate rejected')}
                          disabled={acting === c.id}
                          className="btn-danger text-xs px-3 py-1.5"
                        >
                          <X size={13} /> Reject
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}

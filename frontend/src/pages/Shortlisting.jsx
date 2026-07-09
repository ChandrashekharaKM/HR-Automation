import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Star, X, Eye } from 'lucide-react'
import { candidateApi } from '../services/candidateApi'
import Avatar from '../components/Avatar'
import { TableSkeleton } from '../components/Loader'
import toast from 'react-hot-toast'

export default function Shortlisting() {
  const [candidates, setCandidates] = useState([])
  const [loading, setLoading] = useState(true)
  const navigate = useNavigate()

  const load = () => {
    candidateApi.getAll({ status: 'applied' }).then(d => { setCandidates(d); setLoading(false) })
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

  return (
    <div className="space-y-5 animate-fade-in">
      <div className="glass-card p-4 flex items-center gap-3 border-l-4" style={{ borderLeftColor: '#6366f1' }}>
        <Star size={18} className="text-primary-400" />
        <p className="text-sm text-slate-300">
          Review new applications and shortlist candidates. <strong className="text-white">{candidates.length}</strong> pending.
        </p>
      </div>

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
                  <th>Candidate</th>
                  <th>College</th>
                  <th>Role</th>
                  <th>Resume Score</th>
                  <th>Skills</th>
                  <th>Actions</th>
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
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}

import { useState, useEffect } from 'react'
import { Award, Eye, Download, Send, RefreshCw, CheckCircle } from 'lucide-react'
import { candidateApi } from '../services/candidateApi'
import Avatar from '../components/Avatar'
import { TableSkeleton } from '../components/Loader'
import toast from 'react-hot-toast'

function CertPreviewModal({ candidate, onClose }) {
  return (
    <div className="modal-overlay" onClick={e => e.target === e.currentTarget && onClose()}>
      <div className="modal-content" style={{ maxWidth: '680px' }}>
        <div className="flex items-center justify-between p-6 border-b border-white/5">
          <h2 className="text-lg font-bold text-white">Certificate Preview</h2>
          <button onClick={onClose} className="btn-ghost p-2">✕</button>
        </div>
        <div className="p-8">
          {/* Certificate mock */}
          <div className="rounded-xl p-10 text-center space-y-4 relative overflow-hidden"
            style={{ background: 'linear-gradient(135deg, #1e3a5f, #0f2027)', border: '3px solid #f59e0b' }}>
            {/* Corner decorations */}
            <div className="absolute top-3 left-3 w-8 h-8 border-t-2 border-l-2 border-yellow-400 rounded-tl-lg" />
            <div className="absolute top-3 right-3 w-8 h-8 border-t-2 border-r-2 border-yellow-400 rounded-tr-lg" />
            <div className="absolute bottom-3 left-3 w-8 h-8 border-b-2 border-l-2 border-yellow-400 rounded-bl-lg" />
            <div className="absolute bottom-3 right-3 w-8 h-8 border-b-2 border-r-2 border-yellow-400 rounded-br-lg" />
            <p className="text-yellow-400 text-xs font-semibold tracking-widest uppercase">SwipeGen Technologies</p>
            <p className="text-white/60 text-xs">Certificate of Completion</p>
            <p className="text-white/70 text-sm">This is to certify that</p>
            <p className="text-2xl font-bold text-yellow-300">{candidate?.name}</p>
            <p className="text-white/70 text-sm leading-relaxed max-w-sm mx-auto">
              has successfully completed the internship program as <br />
              <strong className="text-white">{candidate?.role}</strong><br />
              from <strong className="text-white">February 2024</strong> to <strong className="text-white">July 2024</strong>
            </p>
            <div className="pt-6 flex justify-around">
              <div className="text-center">
                <div className="w-24 h-px bg-white/30 mb-1" />
                <p className="text-white/60 text-xs">HR Manager</p>
              </div>
              <div className="text-center">
                <div className="w-24 h-px bg-white/30 mb-1" />
                <p className="text-white/60 text-xs">Director</p>
              </div>
            </div>
            <p className="text-white/30 text-xs mt-2">Verification ID: SWG-2024-{candidate?.id?.padStart(6,'0')}</p>
          </div>
          <div className="flex gap-3 mt-5">
            <button className="btn-primary flex-1 justify-center"><Download size={15} /> Download PDF</button>
            <button className="btn-secondary flex-1 justify-center"><Send size={15} /> Send Certificate</button>
          </div>
        </div>
      </div>
    </div>
  )
}

export default function Certificates() {
  const [candidates, setCandidates] = useState([])
  const [loading, setLoading] = useState(true)
  const [acting, setActing] = useState(null)
  const [preview, setPreview] = useState(null)

  const load = () => {
    Promise.all([
      candidateApi.getAll({ status: 'offer' }),
      candidateApi.getAll({ status: 'completed' }),
    ]).then(([a, b]) => { setCandidates([...a, ...b]); setLoading(false) })
  }
  useEffect(() => { load() }, [])

  const act = async (c, fn, msg) => {
    setActing(c.id)
    try { await fn(); toast.success(msg) }
    catch (e) { toast.error(e.message) }
    setActing(null)
    load()
  }

  return (
    <div className="space-y-5 animate-fade-in">
      <div className="glass-card p-4 flex items-center gap-3 border-l-4" style={{ borderLeftColor: '#22c55e' }}>
        <Award size={18} className="text-green-400" />
        <p className="text-sm text-slate-300">
          Generate and send internship completion certificates.
          <strong className="text-white"> {candidates.length}</strong> candidates.
        </p>
      </div>

      <div className="glass-card overflow-hidden">
        <div className="px-5 py-3 border-b border-white/5">
          <h2 className="text-sm font-semibold text-white">Completed Interns</h2>
        </div>

        {loading ? (
          <div className="p-4"><TableSkeleton rows={3} /></div>
        ) : candidates.length === 0 ? (
          <div className="py-16 text-center">
            <p className="text-4xl mb-3">🎓</p>
            <p className="text-slate-400 text-sm">No certificates to generate</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Candidate</th>
                  <th>Role</th>
                  <th>Duration</th>
                  <th>Status</th>
                  <th>Certificate</th>
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
                          <p className="text-xs text-slate-500">{c.college}</p>
                        </div>
                      </div>
                    </td>
                    <td className="text-slate-300 text-xs">{c.role}</td>
                    <td className="text-slate-400 text-xs">6 months</td>
                    <td>
                      {c.status === 'completed'
                        ? <span className="text-xs text-green-400 flex items-center gap-1"><CheckCircle size={12} /> Completed</span>
                        : <span className="text-xs text-yellow-400">Offer Sent</span>
                      }
                    </td>
                    <td>
                      <div className="flex items-center gap-1.5 flex-wrap">
                        <button onClick={() => setPreview(c)} className="btn-ghost text-xs px-2 py-1.5">
                          <Eye size={13} /> Preview
                        </button>
                        <button onClick={() => act(c, () => candidateApi.generateCertificate(c.id), '🎓 Certificate generated!')}
                          disabled={acting === c.id} className="btn-secondary text-xs px-2 py-1.5">
                          {acting === c.id ? <RefreshCw size={12} className="animate-spin" /> : <Award size={12} />}
                          Generate
                        </button>
                        <button onClick={() => act(c, () => candidateApi.sendCertificate(c.id), '🏁 Sent via email!')}
                          disabled={acting === c.id} className="btn-primary text-xs px-2 py-1.5">
                          <Send size={12} /> Send
                        </button>
                        <button className="btn-ghost text-xs px-2 py-1.5">
                          <Download size={12} /> PDF
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

      {preview && <CertPreviewModal candidate={preview} onClose={() => setPreview(null)} />}
    </div>
  )
}

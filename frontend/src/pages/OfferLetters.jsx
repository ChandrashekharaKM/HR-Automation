import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { FileText, Eye, Download, Send, RefreshCw, Building2 } from 'lucide-react'
import { candidateApi } from '../services/candidateApi'
import Avatar from '../components/Avatar'
import StatusBadge from '../components/StatusBadge'
import { TableSkeleton } from '../components/Loader'
import toast from 'react-hot-toast'

function OfferPreviewModal({ candidate, onClose }) {
  return (
    <div className="modal-overlay" onClick={e => e.target === e.currentTarget && onClose()}>
      <div className="modal-content" style={{ maxWidth: '680px' }}>
        <div className="flex items-center justify-between p-6 border-b border-white/5">
          <h2 className="text-lg font-bold text-white">Offer Letter Preview</h2>
          <button onClick={onClose} className="btn-ghost p-2">✕</button>
        </div>
        <div className="p-8">
          {/* Mock offer letter */}
          <div className="bg-white text-gray-900 rounded-xl p-8 space-y-5 text-sm">
            <div className="flex items-center justify-between border-b border-gray-200 pb-4">
              <div>
                <p className="text-xl font-bold text-indigo-700">SwipeGen Technologies</p>
                <p className="text-gray-500 text-xs">HR Department</p>
              </div>
              <p className="text-gray-400 text-xs">{new Date().toLocaleDateString('en-IN', { day: '2-digit', month: 'long', year: 'numeric' })}</p>
            </div>
            <div>
              <p className="font-semibold text-gray-700">To,</p>
              <p className="font-bold text-gray-900 mt-1">{candidate?.name}</p>
              <p className="text-gray-500">{candidate?.email}</p>
            </div>
            <p className="text-gray-700">Dear <strong>{candidate?.name?.split(' ')[0]}</strong>,</p>
            <p className="text-gray-700 leading-relaxed">
              We are pleased to offer you the position of <strong>{candidate?.role}</strong> at SwipeGen Technologies.
              After reviewing your application and interview performance, we are confident that you will be a valuable addition to our team.
            </p>
            <div className="bg-indigo-50 rounded-lg p-4 border border-indigo-100">
              <p className="font-semibold text-indigo-800 mb-2">Offer Details</p>
              <div className="grid grid-cols-2 gap-2 text-xs text-gray-700">
                <span>Position:</span><span className="font-medium">{candidate?.role}</span>
                <span>Stipend:</span><span className="font-medium text-green-700">{candidate?.salary || '₹20,000/month'}</span>
                <span>Joining Date:</span><span className="font-medium">{candidate?.joiningDate || 'To be confirmed'}</span>
                <span>Duration:</span><span className="font-medium">6 months internship</span>
              </div>
            </div>
            <p className="text-gray-700 text-xs leading-relaxed">
              Please sign and return this letter by the indicated deadline. We look forward to welcoming you to the SwipeGen family!
            </p>
            <div className="pt-4 border-t border-gray-200">
              <p className="font-semibold text-gray-800">HR Team</p>
              <p className="text-xs text-gray-500">SwipeGen Technologies</p>
            </div>
          </div>
          <div className="flex gap-3 mt-5">
            <button className="btn-primary flex-1 justify-center"><Download size={15} /> Download PDF</button>
            <button className="btn-secondary flex-1 justify-center"><Send size={15} /> Send to Candidate</button>
          </div>
        </div>
      </div>
    </div>
  )
}

export default function OfferLetters() {
  const [candidates, setCandidates] = useState([])
  const [loading, setLoading] = useState(true)
  const [acting, setActing] = useState(null)
  const [preview, setPreview] = useState(null)
  const navigate = useNavigate()

  const load = () => {
    candidateApi.getAll({ status: 'hired' }).then(d => { setCandidates(d); setLoading(false) })
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
      <div className="glass-card p-4 flex items-center gap-3 border-l-4" style={{ borderLeftColor: '#f59e0b' }}>
        <FileText size={18} className="text-yellow-400" />
        <p className="text-sm text-slate-300">
          Generate and send offer letters to hired candidates.
          <strong className="text-white"> {candidates.length}</strong> pending.
        </p>
      </div>

      <div className="glass-card overflow-hidden">
        <div className="px-5 py-3 border-b border-white/5">
          <h2 className="text-sm font-semibold text-white">Offer Queue</h2>
        </div>

        {loading ? (
          <div className="p-4"><TableSkeleton rows={3} /></div>
        ) : candidates.length === 0 ? (
          <div className="py-16 text-center">
            <p className="text-4xl mb-3">📬</p>
            <p className="text-slate-400 text-sm">No pending offer letters</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Candidate</th>
                  <th>Role</th>
                  <th>Salary</th>
                  <th>Joining Date</th>
                  <th>Status</th>
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
                          <p className="text-xs text-slate-500">{c.college}</p>
                        </div>
                      </div>
                    </td>
                    <td className="text-slate-300 text-xs">{c.role}</td>
                    <td className="text-green-400 text-sm font-semibold">{c.salary || '—'}</td>
                    <td className="text-slate-400 text-xs">{c.joiningDate || '—'}</td>
                    <td><StatusBadge status={c.status} /></td>
                    <td>
                      <div className="flex items-center gap-1.5 flex-wrap">
                        <button onClick={() => setPreview(c)} className="btn-ghost text-xs px-2 py-1.5">
                          <Eye size={13} /> Preview
                        </button>
                        <button onClick={() => act(c, () => candidateApi.generateOffer(c.id), '📄 Offer PDF generated!')}
                          disabled={acting === c.id} className="btn-secondary text-xs px-2 py-1.5">
                          {acting === c.id ? <RefreshCw size={12} className="animate-spin" /> : <FileText size={12} />}
                          Generate
                        </button>
                        <button onClick={() => act(c, () => candidateApi.sendOffer(c.id), '✉️ Offer sent via email!')}
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

      {preview && <OfferPreviewModal candidate={preview} onClose={() => setPreview(null)} />}
    </div>
  )
}

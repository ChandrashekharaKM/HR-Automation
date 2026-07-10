import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { FileText, Eye, Download, Send, RefreshCw, Building2, Upload } from 'lucide-react'
import { candidateApi } from '../services/candidateApi'
import Avatar from '../components/Avatar'
import StatusBadge from '../components/StatusBadge'
import { TableSkeleton } from '../components/Loader'
import toast from 'react-hot-toast'

function OfferPreviewModal({ candidate, onClose }) {
  const name = candidate?.name || 'Candidate'
  const email = candidate?.email || 'no_email'
  const email_prefix = email.split('@')[0]
  const safe_name = name.replace(/[^a-zA-Z0-9_]/g, '_')
  const filename = `Offer_${safe_name}_${email_prefix}.pdf`
  const pdfUrl = `/api/offers/${filename}`
  const [showRealPdf, setShowRealPdf] = useState(false)
  const [pdfExists, setPdfExists] = useState(false)

  useEffect(() => {
    fetch(pdfUrl, { method: 'HEAD' })
      .then(res => {
        if (res.ok) {
          setPdfExists(true)
          setShowRealPdf(true)
        }
      })
      .catch(() => {})
  }, [pdfUrl])

  return (
    <div className="modal-overlay" onClick={e => e.target === e.currentTarget && onClose()}>
      <div className="modal-content" style={{ maxWidth: '800px', width: '90%' }}>
        <div className="flex items-center justify-between p-6 border-b border-white/5">
          <h2 className="text-lg font-bold text-white">Offer Letter Review</h2>
          <div className="flex items-center gap-2">
            {pdfExists && (
              <button onClick={() => setShowRealPdf(!showRealPdf)} className="btn-secondary text-xs px-2.5 py-1">
                {showRealPdf ? "Show Template Preview" : "Show Uploaded/Generated PDF"}
              </button>
            )}
            <button onClick={onClose} className="btn-ghost p-2">✕</button>
          </div>
        </div>
        <div className="p-6">
          {showRealPdf && pdfExists ? (
            <div className="rounded-xl overflow-hidden bg-slate-900 border border-white/10 h-[500px]">
              <iframe 
                src={pdfUrl} 
                className="w-full h-full border-none"
                title="Offer Letter PDF"
              />
            </div>
          ) : (
            <div className="rounded-xl overflow-hidden bg-slate-900 border border-white/10 h-[500px]">
              <iframe 
                src={`/api/offers/preview/${candidate.row || candidate.id}`} 
                className="w-full h-full border-none bg-white"
                title="Offer Email Template Preview"
              />
            </div>
          )}
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
    Promise.all([
      candidateApi.getAll({ status: 'hired' }),
      candidateApi.getAll({ status: 'offer' }),
    ]).then(([hiredList, offerList]) => {
      setCandidates([...hiredList, ...offerList])
      setLoading(false)
    })
  }
  useEffect(() => { load() }, [])

  const act = async (c, fn, msg) => {
    setActing(c.id)
    try { await fn(); toast.success(msg) }
    catch (e) { toast.error(e.message) }
    setActing(null)
    load()
  }

  const handleFileUpload = async (c, file) => {
    if (!file) return
    const toastId = toast.loading('Uploading document...')
    try {
      await candidateApi.uploadOffer(c.id, file)
      toast.success('📄 Document uploaded successfully!', { id: toastId })
      load()
    } catch (e) {
      toast.error(e.message || 'Upload failed', { id: toastId })
    }
  }

  const handleDownloadPdf = (c) => {
    const name = c.name || 'Candidate'
    const email = c.email || 'no_email'
    const email_prefix = email.split('@')[0]
    const safe_name = name.replace(/[^a-zA-Z0-9_]/g, '_')
    const filename = `Offer_${safe_name}_${email_prefix}.pdf`
    const url = `/api/offers/${filename}`
    window.open(url, '_blank')
  }

  return (
    <div className="space-y-5 animate-fade-in">
      <div className="glass-card p-4 flex items-center gap-3 border-l-4" style={{ borderLeftColor: '#f59e0b' }}>
        <FileText size={18} className="text-yellow-400" />
        <p className="text-sm text-slate-300">
          Generate, upload and send offer letters to hired candidates.
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
                        <button onClick={() => setPreview(c)} className="btn-ghost text-xs px-2 py-1.5" title="Preview Letter">
                          <Eye size={13} /> Preview
                        </button>
                        <button onClick={() => act(c, () => candidateApi.generateOffer(c.id), '📄 Offer PDF generated!')}
                          disabled={acting === c.id} className="btn-secondary text-xs px-2 py-1.5">
                          {acting === c.id ? <RefreshCw size={12} className="animate-spin" /> : <FileText size={12} />}
                          Generate
                        </button>
                        <label className="btn-secondary text-xs px-2 py-1.5 cursor-pointer inline-flex items-center gap-1">
                          <Upload size={12} /> Upload
                          <input
                            type="file"
                            accept=".pdf,.docx"
                            className="hidden"
                            onChange={(e) => handleFileUpload(c, e.target.files[0])}
                          />
                        </label>
                        <button onClick={() => act(c, () => candidateApi.sendOffer(c.id), '✉️ Offer sent via email!')}
                          disabled={acting === c.id} className="btn-primary text-xs px-2 py-1.5">
                          <Send size={12} /> Send
                        </button>
                        <button onClick={() => handleDownloadPdf(c)} className="btn-ghost text-xs px-2 py-1.5" title="Download PDF">
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

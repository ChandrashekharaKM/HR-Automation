import { X, Download, Eye, FileText } from 'lucide-react'
import Avatar from './Avatar'

export default function ResumeModal({ candidate, onClose }) {
  if (!candidate) return null

  return (
    <div className="modal-overlay" onClick={e => e.target === e.currentTarget && onClose()}>
      <div className="modal-content" style={{ maxWidth: '700px' }}>
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-white/5">
          <div className="flex items-center gap-3">
            <FileText size={20} className="text-primary-400" />
            <div>
              <h2 className="text-lg font-bold text-white">Resume Preview</h2>
              <p className="text-xs text-slate-400">{candidate.name}</p>
            </div>
          </div>
          <button onClick={onClose} className="btn-ghost p-2 rounded-xl">
            <X size={18} />
          </button>
        </div>

        {/* Body */}
        <div className="p-6 space-y-6">
          {/* Candidate summary */}
          <div className="flex items-center gap-4 p-4 rounded-xl bg-white/[0.03] border border-white/5">
            <Avatar name={candidate.name} size="lg" />
            <div>
              <h3 className="text-white font-semibold text-base">{candidate.name}</h3>
              <p className="text-slate-400 text-sm">{candidate.email}</p>
              <p className="text-slate-500 text-xs mt-1">{candidate.college} · {candidate.role}</p>
            </div>
            <div className="ml-auto text-right">
              <div className="text-2xl font-bold text-primary-400">{candidate.resumeScore}%</div>
              <p className="text-xs text-slate-500">Resume Score</p>
            </div>
          </div>

          {/* Skills */}
          <div>
            <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">Skills</p>
            <div className="flex flex-wrap gap-2">
              {(candidate.skills || []).map(skill => (
                <span key={skill} className="px-3 py-1 rounded-full text-xs font-medium bg-primary-500/15 text-primary-300 border border-primary-500/20">
                  {skill}
                </span>
              ))}
            </div>
          </div>

          {/* Resume mock preview */}
          <div className="rounded-xl bg-white/[0.02] border border-white/5 p-8 min-h-[280px] flex flex-col items-center justify-center text-center space-y-3">
            <FileText size={48} className="text-slate-600" />
            <p className="text-slate-500 text-sm">Resume PDF Preview</p>
            <p className="text-slate-600 text-xs max-w-xs">
              Connect Google Drive or upload endpoint to render the actual resume here. 
              The backend can serve the file via <code className="text-primary-400">/api/candidates/{'{id}'}/resume</code>
            </p>
            <div className="flex items-center gap-2 mt-4">
              <button className="btn-primary text-xs px-3 py-1.5">
                <Eye size={14} /> View Full Resume
              </button>
              <button className="btn-secondary text-xs px-3 py-1.5">
                <Download size={14} /> Download PDF
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

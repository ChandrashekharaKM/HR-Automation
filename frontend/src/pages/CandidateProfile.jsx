import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import {
  ArrowLeft, Mail, Phone, Building2, BookOpen, FileText,
  Star, X, Calendar, UserCheck, Award, Send, RefreshCw
} from 'lucide-react'
import { candidateApi } from '../services/candidateApi'
import { interviewApi } from '../services/interviewApi'
import StatusBadge from '../components/StatusBadge'
import Avatar from '../components/Avatar'
import Timeline from '../components/Timeline'
import ResumeModal from '../components/ResumeModal'
import { Loader } from '../components/Loader'
import toast from 'react-hot-toast'

function ActionButton({ label, icon: Icon, onClick, variant = 'primary', disabled = false }) {
  const cls = {
    primary: 'btn-primary',
    secondary: 'btn-secondary',
    danger: 'btn-danger',
    success: 'inline-flex items-center gap-2 px-4 py-2 rounded-xl font-semibold text-sm text-white bg-green-500/20 border border-green-500/30 hover:bg-green-500/30 transition-all duration-200 cursor-pointer',
  }[variant]

  return (
    <button onClick={onClick} disabled={disabled} className={`${cls} w-full justify-center`}>
      <Icon size={15} /> {label}
    </button>
  )
}

function InfoRow({ icon: Icon, label, value }) {
  return (
    <div className="flex items-start gap-3">
      <Icon size={15} className="text-slate-500 mt-0.5 flex-shrink-0" />
      <div>
        <p className="text-xs text-slate-500">{label}</p>
        <p className="text-sm text-white font-medium">{value || '—'}</p>
      </div>
    </div>
  )
}

export default function CandidateProfile() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [candidate, setCandidate] = useState(null)
  const [loading, setLoading] = useState(true)
  const [acting, setActing] = useState(false)
  const [showResume, setShowResume] = useState(false)
  const [showSchedule, setShowSchedule] = useState(false)
  const [scheduleForm, setScheduleForm] = useState({ date: '', time: '10:00', interviewer: '', meetLink: '' })

  const load = () => {
    candidateApi.getById(id).then(c => { setCandidate(c); setLoading(false) }).catch(() => navigate('/candidates'))
  }
  useEffect(() => { load() }, [id])

  const act = async (fn, successMsg) => {
    setActing(true)
    try {
      await fn()
      toast.success(successMsg)
      load()
    } catch (e) { toast.error(e.message) }
    setActing(false)
  }

  const handleScheduleInterview = async () => {
    if (!scheduleForm.date) return toast.error('Please select a date')
    setActing(true)
    try {
      await interviewApi.schedule({
        candidateId: id, candidateName: candidate.name,
        college: candidate.college, role: candidate.role,
        ...scheduleForm, status: 'scheduled'
      })
      await candidateApi.updateStatus(id, 'interview')
      toast.success('Interview scheduled successfully!')
      setShowSchedule(false)
      load()
    } catch (e) { toast.error(e.message) }
    setActing(false)
  }

  if (loading) return <div className="flex items-center justify-center h-64"><Loader /></div>
  if (!candidate) return null

  const status = candidate.status
  const canShortlist   = status === 'applied'
  const canInterview   = status === 'shortlisted'
  const canHire        = status === 'interview' || status === 'accepted'
  const canOffer       = status === 'hired'
  const canCertificate = status === 'offer' || status === 'completed'
  const canReject      = !['rejected','completed'].includes(status)
  const canSendDocs    = status === 'hired'

  return (
    <div className="animate-fade-in">
      {/* Back */}
      <button onClick={() => navigate('/candidates')} className="btn-ghost mb-4 -ml-2">
        <ArrowLeft size={16} /> Back to Candidates
      </button>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left: Profile info */}
        <div className="lg:col-span-2 space-y-5">
          {/* Hero card */}
          <div className="glass-card p-6">
            <div className="flex items-start gap-5">
              <Avatar name={candidate.name} size="xl" />
              <div className="flex-1 min-w-0">
                <div className="flex items-start justify-between flex-wrap gap-2">
                  <div>
                    <h2 className="text-2xl font-bold text-white">{candidate.name}</h2>
                    <p className="text-slate-400 text-sm mt-0.5">{candidate.role}</p>
                  </div>
                  <StatusBadge status={candidate.status} size="lg" />
                </div>
                <div className="grid grid-cols-2 gap-4 mt-4">
                  <InfoRow icon={Mail}     label="Email"   value={candidate.email} />
                  <InfoRow icon={Phone}    label="Phone"   value={candidate.phone} />
                  <InfoRow icon={Building2}label="College" value={candidate.college} />
                  <InfoRow icon={BookOpen} label="CGPA"    value={candidate.cgpa} />
                </div>
              </div>
            </div>

            {/* Skills */}
            {candidate.skills?.length > 0 && (
              <div className="mt-4 pt-4 border-t border-white/5">
                <p className="text-xs text-slate-500 mb-2">Skills</p>
                <div className="flex flex-wrap gap-2">
                  {candidate.skills.map(s => (
                    <span key={s} className="px-3 py-1 rounded-full text-xs font-medium bg-primary-500/15 text-primary-300 border border-primary-500/20">{s}</span>
                  ))}
                </div>
              </div>
            )}

            {/* Resume button */}
            <button onClick={() => setShowResume(true)} className="btn-secondary mt-4 text-xs">
              <FileText size={14} /> View Resume
            </button>
          </div>

          {/* Details if hired */}
          {(status === 'hired' || status === 'offer' || status === 'completed') && (
            <div className="glass-card p-5">
              <h3 className="text-sm font-semibold text-white mb-4">Candidate Details</h3>
              <div className="grid grid-cols-2 gap-4 text-sm">
                {[
                  ['Address', candidate.address],
                  ['Bank Account', candidate.bank],
                  ['PAN', candidate.pan],
                  ['Aadhaar', candidate.aadhaar],
                  ['Salary', candidate.salary],
                  ['Joining Date', candidate.joiningDate],
                ].map(([label, val]) => (
                  <div key={label}>
                    <p className="text-xs text-slate-500 mb-0.5">{label}</p>
                    <p className="text-white text-sm">{val || <span className="text-slate-600">Not provided</span>}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Interview details */}
          {candidate.interviewDate && (
            <div className="glass-card p-5">
              <h3 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
                <Calendar size={15} className="text-primary-400" /> Interview Details
              </h3>
              <div className="grid grid-cols-2 gap-3 text-sm">
                <div>
                  <p className="text-xs text-slate-500">Date</p>
                  <p className="text-white">{candidate.interviewDate}</p>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Right: Timeline + Actions */}
        <div className="space-y-5">
          {/* Timeline */}
          <div className="glass-card p-5">
            <h3 className="text-sm font-semibold text-white mb-4">Pipeline Progress</h3>
            <Timeline status={candidate.status} />
          </div>

          {/* Actions */}
          <div className="glass-card p-5 space-y-3">
            <h3 className="text-sm font-semibold text-white mb-1">Actions</h3>

            {canShortlist && (
              <ActionButton label="Shortlist" icon={Star} variant="primary"
                onClick={() => act(() => candidateApi.shortlist(id), '✅ Shortlisted successfully')} disabled={acting} />
            )}
            {canInterview && (
              <ActionButton label="Schedule Interview" icon={Calendar} variant="primary"
                onClick={() => setShowSchedule(true)} disabled={acting} />
            )}
            {canHire && (
              <ActionButton label="Mark as Hired" icon={UserCheck} variant="success"
                onClick={() => act(() => candidateApi.hire(id), '🎉 Marked as Hired')} disabled={acting} />
            )}
            {canSendDocs && (
              <ActionButton label="Request Documents" icon={Send} variant="secondary"
                onClick={() => act(() => candidateApi.sendDetailsRequest(id), '📩 Details request sent')} disabled={acting} />
            )}
            {canOffer && (<>
              <ActionButton label="Generate Offer Letter" icon={FileText} variant="primary"
                onClick={() => act(() => candidateApi.generateOffer(id), '📄 Offer PDF generated')} disabled={acting} />
              <ActionButton label="Send Offer Email" icon={Send} variant="secondary"
                onClick={() => act(() => candidateApi.sendOffer(id), '✉️ Offer sent via email')} disabled={acting} />
            </>)}
            {canCertificate && (<>
              <ActionButton label="Generate Certificate" icon={Award} variant="primary"
                onClick={() => act(() => candidateApi.generateCertificate(id), '🎓 Certificate generated')} disabled={acting} />
              <ActionButton label="Send Certificate" icon={Send} variant="secondary"
                onClick={() => act(() => candidateApi.sendCertificate(id), '🏁 Completion email sent')} disabled={acting} />
            </>)}
            {canReject && (
              <ActionButton label="Reject" icon={X} variant="danger"
                onClick={() => act(() => candidateApi.reject(id), 'Candidate rejected')} disabled={acting} />
            )}

            {acting && (
              <div className="flex items-center gap-2 text-xs text-primary-400 justify-center pt-1">
                <RefreshCw size={12} className="animate-spin" /> Processing...
              </div>
            )}
          </div>
        </div>
      </div>

      {showResume && <ResumeModal candidate={candidate} onClose={() => setShowResume(false)} />}

      {/* Schedule Interview Modal */}
      {showSchedule && (
        <div className="modal-overlay" onClick={e => e.target === e.currentTarget && setShowSchedule(false)}>
          <div className="modal-content">
            <div className="flex items-center justify-between p-6 border-b border-white/5">
              <h2 className="text-lg font-bold text-white">Schedule Interview</h2>
              <button onClick={() => setShowSchedule(false)} className="btn-ghost p-2"><X size={18} /></button>
            </div>
            <div className="p-6 space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-400 mb-1.5">Interview Date *</label>
                  <input type="date" value={scheduleForm.date} onChange={e => setScheduleForm(f => ({...f, date: e.target.value}))}
                    className="input-field" min={new Date().toISOString().split('T')[0]} />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-400 mb-1.5">Time</label>
                  <input type="time" value={scheduleForm.time} onChange={e => setScheduleForm(f => ({...f, time: e.target.value}))}
                    className="input-field" />
                </div>
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-400 mb-1.5">Interviewer</label>
                <input value={scheduleForm.interviewer} onChange={e => setScheduleForm(f => ({...f, interviewer: e.target.value}))}
                  className="input-field" placeholder="Rakesh Kumar" />
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-400 mb-1.5">Google Meet Link</label>
                <input value={scheduleForm.meetLink} onChange={e => setScheduleForm(f => ({...f, meetLink: e.target.value}))}
                  className="input-field" placeholder="https://meet.google.com/..." />
              </div>
              <div className="flex gap-3 pt-2">
                <button onClick={() => setShowSchedule(false)} className="btn-secondary flex-1 justify-center">Cancel</button>
                <button onClick={handleScheduleInterview} disabled={acting} className="btn-primary flex-1 justify-center">
                  {acting ? 'Scheduling...' : 'Schedule Interview'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

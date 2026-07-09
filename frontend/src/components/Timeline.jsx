import { CheckCircle, Clock, Circle } from 'lucide-react'

const STAGES = [
  { key: 'applied',     label: 'Applied' },
  { key: 'shortlisted', label: 'Shortlisted' },
  { key: 'interview',   label: 'Interview' },
  { key: 'accepted',    label: 'Accepted' },
  { key: 'hired',       label: 'Hired' },
  { key: 'offer',       label: 'Offer Sent' },
  { key: 'completed',   label: 'Completed' },
]

const ORDER = ['applied','shortlisted','interview','accepted','hired','offer','completed']

function getStageIndex(status) {
  if (status === 'rejected') return -1
  return ORDER.indexOf(status)
}

export default function Timeline({ status }) {
  const currentIdx = getStageIndex(status)

  return (
    <div className="space-y-1">
      {STAGES.map((stage, idx) => {
        const isDone    = currentIdx > idx
        const isCurrent = currentIdx === idx
        const isPending = currentIdx < idx

        return (
          <div key={stage.key} className="timeline-item">
            {/* Dot */}
            <div className={`timeline-dot ${isDone ? 'done' : isCurrent ? 'current' : 'pending'}`}>
              {isDone
                ? <CheckCircle size={16} className="text-white" />
                : isCurrent
                  ? <Clock size={14} className="text-primary-400" />
                  : <Circle size={14} className="text-slate-600" />
              }
            </div>
            {/* Label */}
            <div className="pt-1">
              <p className={`text-sm font-medium ${isDone ? 'text-slate-300' : isCurrent ? 'text-white' : 'text-slate-600'}`}>
                {stage.label}
              </p>
              {isCurrent && (
                <p className="text-xs text-primary-400 mt-0.5">Current stage</p>
              )}
            </div>
          </div>
        )
      })}

      {status === 'rejected' && (
        <div className="flex items-center gap-3 mt-2 px-3 py-2 rounded-xl bg-red-500/10 border border-red-500/20">
          <span className="text-red-400 text-sm font-medium">❌ Application Rejected</span>
        </div>
      )}
    </div>
  )
}

import { useEffect, useState } from 'react'
import { reportApi } from '../services/reportApi'
import { Activity, Clock } from 'lucide-react'

const TYPE_COLORS = {
  certificate: 'bg-indigo-500/20 text-indigo-300 border-indigo-500/30',
  offer:       'bg-yellow-500/20 text-yellow-300 border-yellow-500/30',
  interview:   'bg-purple-500/20 text-purple-300 border-purple-500/30',
  hired:       'bg-green-500/20  text-green-300  border-green-500/30',
  shortlist:   'bg-blue-500/20   text-blue-300   border-blue-500/30',
}

export default function ActivityLog() {
  const [activities, setActivities] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    reportApi.getActivityLog().then(d => { setActivities(d); setLoading(false) })
  }, [])

  return (
    <div className="space-y-5 animate-fade-in">
      <div className="glass-card p-4 flex items-center gap-3">
        <Activity size={18} className="text-primary-400" />
        <p className="text-sm text-slate-300">Every automation action is recorded here in real-time.</p>
      </div>

      <div className="glass-card overflow-hidden">
        <div className="px-5 py-3 border-b border-white/5 flex items-center justify-between">
          <h2 className="text-sm font-semibold text-white">Activity Log</h2>
          <span className="text-xs text-slate-500">{new Date().toLocaleDateString('en-IN', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}</span>
        </div>

        {loading ? (
          <div className="p-6 text-center text-slate-400">Loading...</div>
        ) : (
          <div className="divide-y divide-white/[0.04]">
            {activities.map(a => (
              <div key={a.id} className="px-5 py-4 flex items-start gap-4 hover:bg-white/[0.02] transition-colors">
                <div className="flex items-center gap-2 flex-shrink-0 w-20">
                  <Clock size={12} className="text-slate-600" />
                  <span className="text-xs text-slate-500">{a.time}</span>
                </div>
                <span className="text-xl">{a.icon}</span>
                <div className="flex-1">
                  <p className="text-sm text-slate-300">{a.message}</p>
                  <span className={`inline-flex mt-1 text-xs px-2 py-0.5 rounded-full border capitalize ${TYPE_COLORS[a.type] || ''}`}>
                    {a.type}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

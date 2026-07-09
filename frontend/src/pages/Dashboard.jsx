import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Users, Star, Calendar, UserCheck, FileText, Award,
  TrendingUp, Clock, AlertCircle, ChevronRight, ArrowUpRight
} from 'lucide-react'
import { reportApi } from '../services/reportApi'
import StatusBadge from '../components/StatusBadge'
import Avatar from '../components/Avatar'
import { Skeleton } from '../components/Loader'
import { formatDate } from '../utils/helpers'

function StatCard({ label, value, icon: Icon, color, gradient, trend }) {
  return (
    <div className="stat-card p-5 animate-slide-up">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs font-medium text-slate-400 uppercase tracking-wider">{label}</p>
          <p className="text-3xl font-bold text-white mt-1">{value}</p>
          {trend && (
            <p className="text-xs text-green-400 flex items-center gap-1 mt-1">
              <TrendingUp size={11} /> {trend}
            </p>
          )}
        </div>
        <div className="w-11 h-11 rounded-xl flex items-center justify-center flex-shrink-0"
          style={{ background: gradient }}>
          <Icon size={20} className="text-white" />
        </div>
      </div>
    </div>
  )
}

const STAT_CONFIG = [
  { key: 'totalCandidates',    label: 'Total Candidates',   icon: Users,     gradient: 'linear-gradient(135deg,#6366f1,#8b5cf6)', trend: '+18 this week' },
  { key: 'shortlisted',        label: 'Shortlisted',        icon: Star,      gradient: 'linear-gradient(135deg,#3b82f6,#06b6d4)' },
  { key: 'interviewScheduled', label: 'Interview Scheduled',icon: Calendar,  gradient: 'linear-gradient(135deg,#8b5cf6,#d946ef)' },
  { key: 'interviewAccepted',  label: 'Interview Accepted', icon: UserCheck, gradient: 'linear-gradient(135deg,#14b8a6,#22c55e)' },
  { key: 'hired',              label: 'Hired',              icon: UserCheck, gradient: 'linear-gradient(135deg,#22c55e,#16a34a)', trend: '+4 this month' },
  { key: 'offerSent',          label: 'Offer Pending',      icon: FileText,  gradient: 'linear-gradient(135deg,#f59e0b,#ef4444)' },
  { key: 'completed',          label: 'Completed',          icon: Award,     gradient: 'linear-gradient(135deg,#6366f1,#a855f7)', trend: '+12 total' },
  { key: 'newApplications',    label: 'New Applications',   icon: TrendingUp,gradient: 'linear-gradient(135deg,#f97316,#f59e0b)' },
]

export default function Dashboard() {
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)
  const navigate = useNavigate()

  useEffect(() => {
    reportApi.getDashboardStats().then(data => {
      setStats(data)
      setLoading(false)
    })
  }, [])

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Stat Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {STAT_CONFIG.map(cfg => (
          <StatCard
            key={cfg.key}
            label={cfg.label}
            value={loading ? '—' : stats?.[cfg.key] ?? 0}
            icon={cfg.icon}
            gradient={cfg.gradient}
            trend={cfg.trend}
          />
        ))}
      </div>

      {/* Main content grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Today's Interviews */}
        <div className="glass-card p-5">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-semibold text-white flex items-center gap-2">
              <Calendar size={16} className="text-primary-400" /> Today's Interviews
            </h2>
            <button onClick={() => navigate('/interviews')} className="btn-ghost text-xs py-1 px-2">
              View all <ChevronRight size={12} />
            </button>
          </div>
          <div className="space-y-3">
            {loading ? (
              [1,2].map(i => <Skeleton key={i} className="h-14" />)
            ) : stats?.todayInterviews?.length ? (
              stats.todayInterviews.map((iv, i) => (
                <div key={i} className="flex items-center gap-3 p-3 rounded-xl bg-white/[0.03] border border-white/5">
                  <Avatar name={iv.name} size="sm" />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-white truncate">{iv.name}</p>
                    <p className="text-xs text-slate-400 truncate">{iv.role}</p>
                  </div>
                  <div className="flex items-center gap-1 text-xs text-primary-400 flex-shrink-0">
                    <Clock size={11} /> {iv.time}
                  </div>
                </div>
              ))
            ) : (
              <p className="text-slate-500 text-sm text-center py-4">No interviews today</p>
            )}
          </div>
        </div>

        {/* Recent Activities */}
        <div className="glass-card p-5">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-semibold text-white flex items-center gap-2">
              <Clock size={16} className="text-accent-400" /> Recent Activity
            </h2>
            <button onClick={() => navigate('/activity')} className="btn-ghost text-xs py-1 px-2">
              View all <ChevronRight size={12} />
            </button>
          </div>
          <div className="space-y-2">
            {loading ? (
              [1,2,3,4].map(i => <Skeleton key={i} className="h-10" />)
            ) : (
              stats?.recentActivities?.map(a => (
                <div key={a.id} className="flex items-start gap-3 py-2 border-b border-white/[0.04]">
                  <span className="text-lg leading-none mt-0.5">{a.icon}</span>
                  <div className="flex-1 min-w-0">
                    <p className="text-xs text-slate-300 leading-relaxed">{a.message}</p>
                    <p className="text-xs text-slate-600 mt-0.5">{a.time}</p>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Pending Actions */}
        <div className="glass-card p-5">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-semibold text-white flex items-center gap-2">
              <AlertCircle size={16} className="text-warning" /> Pending Actions
            </h2>
          </div>
          <div className="space-y-3">
            {loading ? (
              [1,2,3].map(i => <Skeleton key={i} className="h-12" />)
            ) : (
              stats?.pendingActions?.map(a => (
                <div key={a.id} className={`flex items-center gap-3 p-3 rounded-xl border ${a.urgent ? 'border-red-500/20 bg-red-500/5' : 'border-white/5 bg-white/[0.02]'}`}>
                  <div className={`w-2 h-2 rounded-full flex-shrink-0 ${a.urgent ? 'bg-red-400' : 'bg-yellow-400'}`} />
                  <p className="text-xs text-slate-300 flex-1">{a.message}</p>
                  <ArrowUpRight size={13} className="text-slate-500 flex-shrink-0" />
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      {/* Quick nav cards */}
      <div>
        <h2 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-3">Quick Actions</h2>
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-3">
          {[
            { label: 'Add Candidate', icon: '👤', path: '/candidates', color: '#6366f1' },
            { label: 'Schedule Interview', icon: '📅', path: '/interviews', color: '#8b5cf6' },
            { label: 'Shortlist Review', icon: '⭐', path: '/shortlisting', color: '#3b82f6' },
            { label: 'Generate Offer', icon: '📄', path: '/offers', color: '#f59e0b' },
            { label: 'Generate Certificate', icon: '🎓', path: '/certificates', color: '#22c55e' },
            { label: 'View Reports', icon: '📊', path: '/reports', color: '#a855f7' },
          ].map(item => (
            <button
              key={item.path}
              onClick={() => navigate(item.path)}
              className="glass-card-hover p-4 text-center cursor-pointer"
            >
              <div className="text-2xl mb-2">{item.icon}</div>
              <p className="text-xs font-medium text-slate-300">{item.label}</p>
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}

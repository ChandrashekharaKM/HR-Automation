import { Bell, Search, LogOut, ChevronDown } from 'lucide-react'
import { useState } from 'react'
import { useAuth } from '../contexts/AuthContext'
import Avatar from './Avatar'

const NOTIFICATIONS = [
  { id: 1, msg: '3 interviews scheduled today', time: '9m ago', type: 'info' },
  { id: 2, msg: '2 offer letters pending', time: '1h ago', type: 'warn' },
  { id: 3, msg: 'Rahul Sharma completed internship', time: '2h ago', type: 'success' },
  { id: 4, msg: '5 new applications received', time: '3h ago', type: 'info' },
]

export default function Navbar({ title = 'Dashboard', subtitle = '' }) {
  const { user, logout } = useAuth()
  const [showNotif, setShowNotif] = useState(false)
  const [showProfile, setShowProfile] = useState(false)

  return (
    <header className="relative z-30 flex items-center justify-between px-6 py-4"
      style={{ borderBottom: '1px solid rgba(255,255,255,0.05)', background: 'rgba(15,15,26,0.8)', backdropFilter: 'blur(12px)' }}>

      {/* Left: Page title */}
      <div>
        <h1 className="page-title">{title}</h1>
        {subtitle && <p className="page-subtitle">{subtitle}</p>}
      </div>

      {/* Right: actions */}
      <div className="flex items-center gap-3">
        {/* Search */}
        <div className="relative hidden md:block">
          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
          <input
            type="text"
            placeholder="Quick search..."
            className="input-field pl-8 w-52 py-2 text-xs"
          />
        </div>

        {/* Notifications */}
        <div className="relative">
          <button
            onClick={() => { setShowNotif(!showNotif); setShowProfile(false) }}
            className="btn-ghost p-2 relative"
          >
            <Bell size={18} />
            <span className="notif-dot" />
          </button>

          {showNotif && (
            <div className="absolute right-0 top-12 w-80 glass-card border border-white/10 rounded-2xl overflow-hidden z-50 animate-slide-up shadow-elevated">
              <div className="px-4 py-3 border-b border-white/5 flex items-center justify-between">
                <p className="text-sm font-semibold text-white">Notifications</p>
                <span className="text-xs text-primary-400 bg-primary-500/15 px-2 py-0.5 rounded-full">
                  {NOTIFICATIONS.length} new
                </span>
              </div>
              <div className="max-h-72 overflow-y-auto">
                {NOTIFICATIONS.map(n => (
                  <div key={n.id} className="px-4 py-3 border-b border-white/[0.03] hover:bg-white/[0.02] transition-colors cursor-pointer">
                    <p className="text-sm text-slate-300">{n.msg}</p>
                    <p className="text-xs text-slate-500 mt-0.5">{n.time}</p>
                  </div>
                ))}
              </div>
              <div className="px-4 py-2.5 text-center">
                <button className="text-xs text-primary-400 hover:text-primary-300">View all</button>
              </div>
            </div>
          )}
        </div>

        {/* Profile */}
        <div className="relative">
          <button
            onClick={() => { setShowProfile(!showProfile); setShowNotif(false) }}
            className="flex items-center gap-2 px-3 py-1.5 rounded-xl hover:bg-white/5 transition-colors"
          >
            <Avatar name={user?.name || 'Admin'} size="sm" />
            <div className="hidden md:block text-left">
              <p className="text-xs font-semibold text-white leading-none">{user?.name}</p>
              <p className="text-xs text-slate-500">{user?.role?.replace('_', ' ')}</p>
            </div>
            <ChevronDown size={14} className="text-slate-400 hidden md:block" />
          </button>

          {showProfile && (
            <div className="absolute right-0 top-12 w-52 glass-card border border-white/10 rounded-2xl overflow-hidden z-50 animate-slide-up shadow-elevated">
              <div className="px-4 py-3 border-b border-white/5">
                <p className="text-sm font-semibold text-white">{user?.name}</p>
                <p className="text-xs text-slate-400">{user?.email}</p>
              </div>
              <button
                onClick={logout}
                className="w-full flex items-center gap-2 px-4 py-3 text-sm text-red-400 hover:bg-red-500/10 transition-colors"
              >
                <LogOut size={14} /> Sign out
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Click-away to close dropdowns */}
      {(showNotif || showProfile) && (
        <div className="fixed inset-0 z-40" onClick={() => { setShowNotif(false); setShowProfile(false) }} />
      )}
    </header>
  )
}

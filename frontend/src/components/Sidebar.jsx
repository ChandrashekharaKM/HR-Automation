import { NavLink, useLocation } from 'react-router-dom'
import {
  LayoutDashboard, Users, Calendar, Briefcase, FileText,
  Award, BarChart3, Settings, Activity, ChevronLeft, ChevronRight,
  Zap, UserCheck, ClipboardList
} from 'lucide-react'
import { useState } from 'react'

const NAV_ITEMS = [
  { label: 'Dashboard',    icon: LayoutDashboard, path: '/' },
  { label: 'Candidates',   icon: Users,           path: '/candidates' },
  { label: 'Shortlisting', icon: ClipboardList,   path: '/shortlisting' },
  { label: 'Interviews',   icon: Calendar,        path: '/interviews' },
  { label: 'Hiring',       icon: UserCheck,       path: '/hiring' },
  { label: 'Offer Letters',icon: FileText,        path: '/offers' },
  { label: 'Certificates', icon: Award,           path: '/certificates' },
  { label: 'Reports',      icon: BarChart3,       path: '/reports' },
  { label: 'Activity Log', icon: Activity,        path: '/activity' },
  { label: 'Settings',     icon: Settings,        path: '/settings' },
]

export default function Sidebar() {
  const [collapsed, setCollapsed] = useState(false)
  const location = useLocation()

  return (
    <aside
      className="flex flex-col h-full transition-all duration-300 ease-in-out flex-shrink-0"
      style={{
        width: collapsed ? 72 : 240,
        background: 'linear-gradient(180deg, #1a1a2e 0%, #16213e 100%)',
        borderRight: '1px solid rgba(99,102,241,0.1)',
      }}
    >
      {/* Logo */}
      <div className="flex items-center gap-3 px-4 py-5 border-b border-white/[0.06]">
        <div className="w-9 h-9 rounded-xl flex items-center justify-center flex-shrink-0"
          style={{ background: 'linear-gradient(135deg, #6366f1, #8b5cf6)', boxShadow: '0 4px 15px rgba(99,102,241,0.4)' }}>
          <Zap size={18} className="text-white" />
        </div>
        {!collapsed && (
          <div className="animate-fade-in overflow-hidden">
            <p className="text-white font-bold text-sm leading-none">SwipeGen</p>
            <p className="text-primary-400 text-xs mt-0.5">HR Portal</p>
          </div>
        )}
      </div>

      {/* Nav */}
      <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
        {NAV_ITEMS.map(({ label, icon: Icon, path }) => {
          const isActive = path === '/'
            ? location.pathname === '/'
            : location.pathname.startsWith(path)

          return (
            <NavLink
              key={path}
              to={path}
              className={`sidebar-item ${isActive ? 'active' : ''}`}
              title={collapsed ? label : undefined}
            >
              <Icon size={18} className="flex-shrink-0" />
              {!collapsed && (
                <span className="truncate">{label}</span>
              )}
            </NavLink>
          )
        })}
      </nav>

      {/* Collapse toggle */}
      <div className="px-3 pb-4">
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="sidebar-item w-full justify-center"
          title={collapsed ? 'Expand' : 'Collapse'}
        >
          {collapsed
            ? <ChevronRight size={16} />
            : <><ChevronLeft size={16} /><span className="text-xs">Collapse</span></>
          }
        </button>
      </div>
    </aside>
  )
}

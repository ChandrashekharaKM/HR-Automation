import Sidebar from '../components/Sidebar'
import Navbar from '../components/Navbar'
import { useLocation } from 'react-router-dom'

const PAGE_META = {
  '/':            { title: 'Dashboard',     subtitle: 'Welcome back, HR Admin' },
  '/candidates':  { title: 'Candidates',    subtitle: 'Manage all applicants' },
  '/shortlisting':{ title: 'Shortlisting',  subtitle: 'Review new applications' },
  '/interviews':  { title: 'Interviews',    subtitle: 'Schedule and manage interviews' },
  '/hiring':      { title: 'Hiring',        subtitle: 'Post-interview decisions' },
  '/offers':      { title: 'Offer Letters', subtitle: 'Generate and send offer packages' },
  '/certificates':{ title: 'Certificates',  subtitle: 'Internship completion certificates' },
  '/reports':     { title: 'Reports',       subtitle: 'Analytics and pipeline insights' },
  '/activity':    { title: 'Activity Log',  subtitle: 'Complete automation history' },
  '/settings':    { title: 'Settings',      subtitle: 'Configure portal and templates' },
}

export default function DashboardLayout({ children }) {
  const location = useLocation()
  const base = '/' + location.pathname.split('/')[1]
  const meta = PAGE_META[base] || { title: 'HR Portal', subtitle: '' }

  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar />
      <div className="flex flex-col flex-1 min-w-0 overflow-hidden">
        <Navbar title={meta.title} subtitle={meta.subtitle} />
        <main className="flex-1 overflow-y-auto p-6">
          {children}
        </main>
      </div>
    </div>
  )
}

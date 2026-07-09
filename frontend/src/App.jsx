import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { Toaster } from 'react-hot-toast'
import { AuthProvider, useAuth } from './contexts/AuthContext'
import DashboardLayout from './layouts/DashboardLayout'

// Pages
import Login          from './pages/Login'
import Dashboard      from './pages/Dashboard'
import Candidates     from './pages/Candidates'
import CandidateProfile from './pages/CandidateProfile'
import Shortlisting   from './pages/Shortlisting'
import Interviews     from './pages/Interviews'
import Hiring         from './pages/Hiring'
import OfferLetters   from './pages/OfferLetters'
import Certificates   from './pages/Certificates'
import Reports        from './pages/Reports'
import ActivityLog    from './pages/ActivityLog'
import Settings       from './pages/Settings'

const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: 1, refetchOnWindowFocus: false } }
})

function ProtectedRoute({ children }) {
  const { isAuthenticated } = useAuth()
  return isAuthenticated ? children : <Navigate to="/login" replace />
}

function AppRoutes() {
  const { isAuthenticated } = useAuth()

  return (
    <Routes>
      <Route path="/login" element={isAuthenticated ? <Navigate to="/" replace /> : <Login />} />
      <Route path="/*" element={
        <ProtectedRoute>
          <DashboardLayout>
            <Routes>
              <Route index                      element={<Dashboard />} />
              <Route path="candidates"          element={<Candidates />} />
              <Route path="candidates/:id"      element={<CandidateProfile />} />
              <Route path="shortlisting"        element={<Shortlisting />} />
              <Route path="interviews"          element={<Interviews />} />
              <Route path="hiring"              element={<Hiring />} />
              <Route path="offers"              element={<OfferLetters />} />
              <Route path="certificates"        element={<Certificates />} />
              <Route path="reports"             element={<Reports />} />
              <Route path="activity"            element={<ActivityLog />} />
              <Route path="settings"            element={<Settings />} />
              <Route path="*"                   element={<Navigate to="/" replace />} />
            </Routes>
          </DashboardLayout>
        </ProtectedRoute>
      } />
    </Routes>
  )
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <BrowserRouter>
          <AppRoutes />
          <Toaster
            position="top-right"
            toastOptions={{
              style: {
                background: '#1a1a2e',
                color: '#f1f5f9',
                border: '1px solid rgba(99,102,241,0.3)',
                borderRadius: '12px',
                fontSize: '13px',
                boxShadow: '0 8px 24px rgba(0,0,0,0.5)',
              },
              success: { iconTheme: { primary: '#22c55e', secondary: '#fff' } },
              error:   { iconTheme: { primary: '#ef4444', secondary: '#fff' } },
            }}
          />
        </BrowserRouter>
      </AuthProvider>
    </QueryClientProvider>
  )
}

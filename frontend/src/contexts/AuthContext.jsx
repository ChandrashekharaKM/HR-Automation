import { createContext, useContext, useState, useCallback } from 'react'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    const stored = localStorage.getItem('hr_user')
    return stored ? JSON.parse(stored) : null
  })

  const login = useCallback(async ({ email, password }) => {
    // Demo credentials — replace with real API call when backend is ready
    if (email === 'admin@swipegen.com' && password === 'admin123') {
      const userData = {
        id: '1',
        name: 'Admin HR',
        email,
        role: 'hr_admin',
        avatar: null,
        company: 'SwipeGen Technologies',
      }
      localStorage.setItem('hr_user', JSON.stringify(userData))
      setUser(userData)
      return { success: true }
    }
    return { success: false, error: 'Invalid email or password' }
  }, [])

  const logout = useCallback(() => {
    localStorage.removeItem('hr_user')
    setUser(null)
  }, [])

  return (
    <AuthContext.Provider value={{ user, login, logout, isAuthenticated: !!user }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}

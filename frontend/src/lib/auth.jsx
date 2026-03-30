/* eslint-disable react-refresh/only-export-components */
import { createContext, useContext, useCallback, useEffect, useState } from 'react'
import { apiFetch, apiPatch, apiPost } from './api'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  const hydrateUser = useCallback((data) => ({
    id: data.id_usuario,
    nome: data.usuario,
    email: data.email,
    admin: data.admin,
    fotoUrl: data.foto_url || null,
  }), [])

  const refresh = useCallback(async () => {
    try {
      const data = await apiFetch('/api/auth/me')
      if (data.logado) {
        setUser(hydrateUser(data))
      } else {
        setUser(null)
      }
    } catch {
      setUser(null)
    } finally {
      setLoading(false)
    }
  }, [hydrateUser])

  useEffect(() => {
    refresh()
  }, [refresh])

  const login = useCallback(async (email, senha) => {
    const data = await apiPost('/api/auth/login', { email, senha })
    if (data.ok) {
      await refresh()
    }
    return data
  }, [refresh])

  const register = useCallback(async (nome, email, senha) => {
    const data = await apiPost('/api/auth/register', { nome, email, senha })
    if (data.ok) {
      await refresh()
    }
    return data
  }, [refresh])

  const logout = useCallback(async () => {
    await apiPost('/api/auth/logout', {})
    setUser(null)
  }, [])

  const updateProfile = useCallback(async ({ nome, fotoUrl }) => {
    const data = await apiPatch('/api/auth/profile', {
      nome,
      foto_url: fotoUrl,
    })

    if (data.ok) {
      setUser(hydrateUser(data))
    }

    return data
  }, [hydrateUser])

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout, refresh, updateProfile }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}

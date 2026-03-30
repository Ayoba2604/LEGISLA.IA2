import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../lib/auth'

export default function LoginPage() {
  const { login } = useAuth()
  const navigate = useNavigate()

  const [email, setEmail] = useState('')
  const [senha, setSenha] = useState('')
  const [msg, setMsg] = useState(null)
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setMsg(null)
    setLoading(true)

    try {
      const data = await login(email.trim(), senha)
      if (data.ok) {
        setMsg({ text: 'Login realizado! Redirecionando...', error: false })
        setTimeout(() => navigate('/'), 600)
      } else {
        setMsg({ text: data.erro || 'Email ou senha invalidos.', error: true })
      }
    } catch {
      setMsg({ text: 'Erro de conexao. Tente novamente.', error: true })
    } finally {
      setLoading(false)
    }
  }

  return (
    <section className="section-shell" style={{ maxWidth: 460, margin: '40px auto' }}>
      <h1 style={{ fontFamily: 'var(--heading-font)', letterSpacing: '-0.04em', marginBottom: 24 }}>
        Login
      </h1>

      {msg && (
        <div
          style={{
            padding: '10px 14px',
            marginBottom: 16,
            borderRadius: 8,
            background: msg.error ? '#fee2e2' : '#d1fae5',
            color: msg.error ? '#991b1b' : '#065f46',
            fontWeight: 600,
          }}
        >
          {msg.text}
        </div>
      )}

      <form onSubmit={handleSubmit} style={{ display: 'grid', gap: 16 }}>
        <div>
          <label htmlFor="login-email" style={{ fontWeight: 700, display: 'block', marginBottom: 6 }}>
            Email
          </label>
          <input
            id="login-email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            placeholder="seu@email.com"
            style={{
              width: '100%',
              padding: '12px 14px',
              border: '1px solid var(--border-strong)',
              borderRadius: 12,
              background: 'var(--bg-surface-strong)',
              color: 'var(--text-primary)',
              fontSize: '1rem',
            }}
          />
        </div>

        <div>
          <label htmlFor="login-senha" style={{ fontWeight: 700, display: 'block', marginBottom: 6 }}>
            Senha
          </label>
          <input
            id="login-senha"
            type="password"
            value={senha}
            onChange={(e) => setSenha(e.target.value)}
            required
            placeholder="Sua senha"
            style={{
              width: '100%',
              padding: '12px 14px',
              border: '1px solid var(--border-strong)',
              borderRadius: 12,
              background: 'var(--bg-surface-strong)',
              color: 'var(--text-primary)',
              fontSize: '1rem',
            }}
          />
        </div>

        <button
          type="submit"
          disabled={loading}
          className="action-link primary"
          style={{ justifyContent: 'center', border: 0, cursor: 'pointer', fontSize: '1rem' }}
        >
          {loading ? 'Entrando...' : 'Login'}
        </button>
      </form>

      <p style={{ marginTop: 20, textAlign: 'center', color: 'var(--text-secondary)' }}>
        Nao tem conta?{' '}
        <Link to="/cadastro" style={{ color: 'var(--bg-accent)', fontWeight: 700 }}>
          Cadastre-se
        </Link>
      </p>
    </section>
  )
}

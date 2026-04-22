import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../lib/auth'

export default function RegisterPage() {
  const { register } = useAuth()
  const navigate = useNavigate()

  const [nome, setNome] = useState('')
  const [email, setEmail] = useState('')
  const [senha, setSenha] = useState('')
  const [msg, setMsg] = useState(null)
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setMsg(null)

    if (senha.length < 6) {
      setMsg({ text: 'A senha deve ter pelo menos 6 caracteres.', error: true })
      return
    }

    setLoading(true)

    try {
      const data = await register(nome.trim(), email.trim(), senha)
      if (data.ok) {
        setMsg({ text: 'Conta criada com sucesso! Redirecionando...', error: false })
        setTimeout(() => navigate('/'), 800)
      } else {
        setMsg({ text: data.erro || 'Erro ao cadastrar.', error: true })
      }
    } catch {
      setMsg({ text: 'Erro de conexao. Tente novamente.', error: true })
    } finally {
      setLoading(false)
    }
  }

  const inputStyle = {
    width: '100%',
    padding: '12px 14px',
    border: '1px solid var(--border-strong)',
    borderRadius: 12,
    background: 'var(--bg-surface-strong)',
    color: 'var(--text-primary)',
    fontSize: '1rem',
  }

  return (
    <section className="section-shell" style={{ maxWidth: 460, margin: '40px auto' }}>
      <h1 style={{ fontFamily: 'var(--heading-font)', letterSpacing: '-0.04em', marginBottom: 24 }}>
        Cadastro
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
          <label htmlFor="cadastro-nome" style={{ fontWeight: 700, display: 'block', marginBottom: 6 }}>
            Nome completo
          </label>
          <input
            id="cadastro-nome"
            type="text"
            value={nome}
            onChange={(e) => setNome(e.target.value)}
            required
            placeholder="Seu nome"
            style={inputStyle}
          />
        </div>

        <div>
          <label htmlFor="cadastro-email" style={{ fontWeight: 700, display: 'block', marginBottom: 6 }}>
            Email
          </label>
          <input
            id="cadastro-email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            placeholder="seu@email.com"
            style={inputStyle}
          />
        </div>

        <div>
          <label htmlFor="cadastro-senha" style={{ fontWeight: 700, display: 'block', marginBottom: 6 }}>
            Senha
          </label>
          <input
            id="cadastro-senha"
            type="password"
            value={senha}
            onChange={(e) => setSenha(e.target.value)}
            required
            placeholder="Minimo 6 caracteres"
            style={inputStyle}
          />
        </div>

        <button
          type="submit"
          disabled={loading}
          className="action-link primary"
          style={{ justifyContent: 'center', border: 0, cursor: 'pointer', fontSize: '1rem' }}
        >
          {loading ? 'Cadastrando...' : 'Cadastrar'}
        </button>
      </form>

      <p style={{ marginTop: 20, textAlign: 'center', color: 'var(--text-secondary)' }}>
        Ja tem conta?{' '}
        <Link to="/login" style={{ color: 'var(--bg-accent)', fontWeight: 700 }}>
          Fazer login
        </Link>
      </p>
    </section>
  )
}

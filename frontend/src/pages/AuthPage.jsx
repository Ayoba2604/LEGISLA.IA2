import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../lib/auth'

export default function AuthPage() {
  const { login, register } = useAuth()
  const navigate = useNavigate()

  const [isLogin, setIsLogin] = useState(true)
  const [nome, setNome] = useState('')
  const [email, setEmail] = useState('')
  const [senha, setSenha] = useState('')
  const [msg, setMsg] = useState(null)
  const [loading, setLoading] = useState(false)

  const reset = () => {
    setMsg(null)
    setNome('')
    setEmail('')
    setSenha('')
  }

  const toggle = () => {
    reset()
    setIsLogin((v) => !v)
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setMsg(null)

    if (!isLogin && senha.length < 6) {
      setMsg({ text: 'A senha deve ter pelo menos 6 caracteres.', error: true })
      return
    }

    setLoading(true)

    try {
      const data = isLogin
        ? await login(email.trim(), senha)
        : await register(nome.trim(), email.trim(), senha)

      if (data.ok) {
        setMsg({
          text: isLogin ? 'Login realizado! Redirecionando...' : 'Conta criada com sucesso! Redirecionando...',
          error: false,
        })
        setTimeout(() => navigate(data.admin ? '/admin' : '/'), 600)
      } else {
        setMsg({ text: data.erro || (isLogin ? 'Email ou senha invalidos.' : 'Erro ao cadastrar.'), error: true })
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
      <div style={{ display: 'flex', gap: 0, marginBottom: 24, borderRadius: 12, overflow: 'hidden', border: '1px solid var(--border-strong)' }}>
        <button
          type="button"
          onClick={() => !isLogin && toggle()}
          style={{
            flex: 1,
            padding: '12px 0',
            fontWeight: 700,
            fontSize: '1rem',
            border: 'none',
            cursor: 'pointer',
            background: isLogin ? 'var(--bg-accent)' : 'var(--bg-surface-strong)',
            color: isLogin ? '#fff' : 'var(--text-secondary)',
            transition: 'all 0.2s',
          }}
        >
          Login
        </button>
        <button
          type="button"
          onClick={() => isLogin && toggle()}
          style={{
            flex: 1,
            padding: '12px 0',
            fontWeight: 700,
            fontSize: '1rem',
            border: 'none',
            cursor: 'pointer',
            background: !isLogin ? 'var(--bg-accent)' : 'var(--bg-surface-strong)',
            color: !isLogin ? '#fff' : 'var(--text-secondary)',
            transition: 'all 0.2s',
          }}
        >
          Cadastro
        </button>
      </div>

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
        {!isLogin && (
          <div>
            <label htmlFor="auth-nome" style={{ fontWeight: 700, display: 'block', marginBottom: 6 }}>
              Nome completo
            </label>
            <input
              id="auth-nome"
              type="text"
              value={nome}
              onChange={(e) => setNome(e.target.value)}
              required
              placeholder="Seu nome"
              style={inputStyle}
            />
          </div>
        )}

        <div>
          <label htmlFor="auth-email" style={{ fontWeight: 700, display: 'block', marginBottom: 6 }}>
            Email
          </label>
          <input
            id="auth-email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            placeholder="seu@email.com"
            style={inputStyle}
          />
        </div>

        <div>
          <label htmlFor="auth-senha" style={{ fontWeight: 700, display: 'block', marginBottom: 6 }}>
            Senha
          </label>
          <input
            id="auth-senha"
            type="password"
            value={senha}
            onChange={(e) => setSenha(e.target.value)}
            required
            placeholder={isLogin ? 'Sua senha' : 'Minimo 6 caracteres'}
            style={inputStyle}
          />
        </div>

        <button
          type="submit"
          disabled={loading}
          className="action-link primary"
          style={{ justifyContent: 'center', border: 0, cursor: 'pointer', fontSize: '1rem' }}
        >
          {loading
            ? (isLogin ? 'Entrando...' : 'Cadastrando...')
            : (isLogin ? 'Entrar' : 'Cadastrar')}
        </button>
      </form>

      <p style={{ marginTop: 20, textAlign: 'center', color: 'var(--text-secondary)' }}>
        {isLogin ? 'Nao tem conta? ' : 'Ja tem conta? '}
        <span
          onClick={toggle}
          style={{ color: 'var(--bg-accent)', fontWeight: 700, cursor: 'pointer' }}
        >
          {isLogin ? 'Cadastre-se' : 'Fazer login'}
        </span>
      </p>
    </section>
  )
}

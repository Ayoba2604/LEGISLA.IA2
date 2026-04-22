import { useEffect, useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../lib/auth'

const GOOGLE_ICON_URL = 'https://unpkg.com/devicon/icons/google/google-original.svg'
const DISCORD_ICON_URL = 'https://cdn.jsdelivr.net/npm/simple-icons@16.7.0/icons/discord.svg'

export default function AuthPage() {
  const { login, register } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()

  const [nome, setNome] = useState('')
  const [email, setEmail] = useState('')
  const [senha, setSenha] = useState('')
  const [msg, setMsg] = useState(null)
  const [loading, setLoading] = useState(false)

  const isLogin = location.pathname !== '/cadastro'

  useEffect(() => {
    setMsg(null)
  }, [isLogin])

  const switchMode = (nextIsLogin) => {
    setMsg(null)
    navigate(nextIsLogin ? '/login' : '/cadastro')
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

  return (
    <section className="auth-route-shell">
      <div className="auth-route-card">
        <div className="auth-route-toggle" aria-label="Selecionar tela">
          <button
            type="button"
            className={isLogin ? 'active' : ''}
            onClick={() => switchMode(true)}
          >
            Login
          </button>
          <button
            type="button"
            className={!isLogin ? 'active' : ''}
            onClick={() => switchMode(false)}
          >
            Cadastro
          </button>
        </div>

        <span className="auth-route-kicker">{isLogin ? 'Acesso a conta' : 'Criacao de conta'}</span>
        <h1 className="auth-route-title">{isLogin ? 'Entrar na sua conta' : 'Criar sua conta'}</h1>
        <p className="auth-route-lead">
          {isLogin
            ? 'Acesse com seu email para continuar de onde parou e manter suas preferencias prontas.'
            : 'Comece pelo cadastro com email e deixe as outras formas de entrada prontas para o proximo passo.'}
        </p>

        <div className="auth-social-stack" aria-hidden="true">
          <button type="button" className="auth-social-btn auth-social-btn--google">
            <img src={GOOGLE_ICON_URL} alt="" loading="lazy" className="auth-social-icon auth-social-icon--google" />
            <span>Continuar com Google</span>
          </button>
          <button type="button" className="auth-social-btn auth-social-btn--discord">
            <img src={DISCORD_ICON_URL} alt="" loading="lazy" className="auth-social-icon auth-social-icon--discord" />
            <span>Continuar com Discord</span>
          </button>
        </div>

        <div className="auth-route-divider">
          <span>{isLogin ? 'Ou entre com email' : 'Ou cadastre com email'}</span>
        </div>

        {msg && (
          <div className={`auth-inline-message ${msg.error ? 'error' : 'success'}`}>
            {msg.text}
          </div>
        )}

        <form onSubmit={handleSubmit} className="auth-route-form">
          {!isLogin && (
            <div className="auth-route-field">
              <label htmlFor="auth-nome">
                <span>Nome completo</span>
              </label>
              <input
                id="auth-nome"
                type="text"
                value={nome}
                onChange={(e) => setNome(e.target.value)}
                required
                placeholder="Seu nome"
                autoComplete="name"
              />
            </div>
          )}

          <div className="auth-route-field">
            <label htmlFor="auth-email">
              <span>Email</span>
            </label>
            <input
              id="auth-email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              placeholder="seu@email.com"
              autoComplete="email"
            />
          </div>

          <div className="auth-route-field">
            <label htmlFor="auth-senha">
              <span>Senha</span>
            </label>
            <input
              id="auth-senha"
              type="password"
              value={senha}
              onChange={(e) => setSenha(e.target.value)}
              required
              placeholder={isLogin ? 'Sua senha' : 'Minimo 6 caracteres'}
              autoComplete={isLogin ? 'current-password' : 'new-password'}
            />
          </div>

          <button type="submit" disabled={loading} className="auth-route-submit">
            {loading
              ? (isLogin ? 'Entrando...' : 'Cadastrando...')
              : (isLogin ? 'Entrar' : 'Cadastrar')}
          </button>
        </form>

        <p className="auth-route-switch">
          {isLogin ? 'Nao tem conta? ' : 'Ja tem conta? '}
          <button type="button" onClick={() => switchMode(!isLogin)}>
            {isLogin ? 'Criar conta' : 'Fazer login'}
          </button>
        </p>
      </div>
    </section>
  )
}

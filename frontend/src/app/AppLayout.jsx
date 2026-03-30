import { useEffect, useMemo, useRef, useState } from 'react'
import { Link, Outlet, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../lib/auth'
import { apiPost } from '../lib/api'
import { getUserInitials } from '../lib/profile'
import { useThemePreference } from '../lib/theme'

function buildPageLabel(pathname) {
  if (pathname.startsWith('/admin')) return 'Central de Controle'
  if (pathname.startsWith('/chat')) return 'Assistente IA'
  if (pathname.startsWith('/configuracoes')) return 'Configuracoes'
  if (pathname.startsWith('/sobre')) return 'Sobre'
  if (pathname.startsWith('/login')) return 'Acesso'
  return 'Inicio'
}

export default function AppLayout() {
  const [theme, setTheme] = useThemePreference()
  const { user, loading, logout } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const [menuOpen, setMenuOpen] = useState(false)
  const menuRef = useRef(null)
  const lastTrackedPath = useRef('')

  useEffect(() => {
    if (!menuOpen) return undefined

    const handlePointerDown = (event) => {
      if (menuRef.current && !menuRef.current.contains(event.target)) {
        setMenuOpen(false)
      }
    }

    window.addEventListener('pointerdown', handlePointerDown)
    return () => window.removeEventListener('pointerdown', handlePointerDown)
  }, [menuOpen])

  useEffect(() => {
    const currentPath = `${location.pathname}${location.search}`
    if (lastTrackedPath.current === currentPath) return

    lastTrackedPath.current = currentPath
    apiPost('/api/analytics/events', {
      tipo: 'page_view',
      rota: location.pathname,
      detalhe: buildPageLabel(location.pathname),
    })
      .then(() => {
        window.dispatchEvent(new CustomEvent('legisla-analytics-recorded', {
          detail: { tipo: 'page_view', rota: location.pathname },
        }))
      })
      .catch(() => {})
  }, [location.pathname, location.search])

  const handleLogout = async () => {
    setMenuOpen(false)
    await logout()
    navigate('/')
  }

  const userLabel = useMemo(() => {
    if (loading) {
      return {
        name: 'Carregando sessao',
        subtitle: 'Sincronizando conta',
        initials: '...',
      }
    }

    if (!user) {
      return {
        name: 'Visitante',
        subtitle: 'Acesse para continuar',
        initials: 'V',
      }
    }

    return {
      name: user.nome,
      subtitle: user.admin ? 'Administrador' : user.email,
      initials: getUserInitials(user.nome),
    }
  }, [loading, user])

  return (
    <div className="app-shell">
      <header className="site-header">
        <div className="nav-shell">
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <Link className="nav-brand" to="/">
              <img className="nav-brand-logo" src="/favicon.svg" alt="" />
              <span>Legisla.IA</span>
            </Link>
            <Link className="nav-link" to="/sobre" style={{ marginLeft: 8 }}>Sobre Nos</Link>
          </div>

          <nav className="nav-list" aria-label="Principal">
            {!loading && user ? (
              <>
                <Link className="nav-link" to="/chat">IA</Link>
                {user.admin ? (
                  <Link className="nav-link" to="/admin">Central de Controle</Link>
                ) : null}
              </>
            ) : null}
          </nav>

          <div className="nav-end">
            <button
              type="button"
              className="nav-theme-chip"
              onClick={() => setTheme((current) => (current === 'dark' ? 'light' : 'dark'))}
            >
              <i className={`bi ${theme === 'dark' ? 'bi-sun' : 'bi-moon-stars'}`} aria-hidden="true"></i>
              <span>Tema</span>
            </button>

            <div className="account-menu" ref={menuRef}>
              <button
                type="button"
                className="account-trigger"
                onClick={() => setMenuOpen((current) => !current)}
                aria-expanded={menuOpen}
                aria-haspopup="menu"
              >
                {user?.fotoUrl ? (
                  <img className="account-avatar-image" src={user.fotoUrl} alt="" />
                ) : (
                  <span className="account-avatar">{userLabel.initials}</span>
                )}
                <span className="account-copy">
                  <strong>{userLabel.name}</strong>
                  <span>{userLabel.subtitle}</span>
                </span>
                <i className={`bi ${menuOpen ? 'bi-chevron-up' : 'bi-chevron-down'}`} aria-hidden="true"></i>
              </button>

              {menuOpen ? (
                <div className="account-popover" role="menu">
                  <div className="account-popover-head">
                    {user?.fotoUrl ? (
                      <img className="account-avatar-image large" src={user.fotoUrl} alt="" />
                    ) : (
                      <span className="account-avatar large">{userLabel.initials}</span>
                    )}
                    <div className="account-popover-copy">
                      <strong>{userLabel.name}</strong>
                      <span>{user?.email || userLabel.subtitle}</span>
                    </div>
                  </div>

                  <button
                    type="button"
                    className="account-menu-link"
                    onClick={() => {
                      setMenuOpen(false)
                      navigate('/configuracoes?tab=perfil')
                    }}
                  >
                    <i className="bi bi-person-circle" aria-hidden="true"></i>
                    <span>Perfil</span>
                  </button>

                  <button
                    type="button"
                    className="account-menu-link"
                    onClick={() => {
                      setMenuOpen(false)
                      navigate('/configuracoes?tab=preferencias')
                    }}
                  >
                    <i className="bi bi-sliders" aria-hidden="true"></i>
                    <span>Configuracoes</span>
                  </button>

                  <button type="button" className="account-menu-link danger" onClick={handleLogout}>
                    <i className="bi bi-box-arrow-right" aria-hidden="true"></i>
                    <span>Sair</span>
                  </button>
                </div>
              ) : null}
            </div>
          </div>
        </div>
      </header>

      <main className="page-content">
        <Outlet />
      </main>

      <footer className="site-credit">
        <small>tester proficional Luisa Sanches</small>
      </footer>
    </div>
  )
}

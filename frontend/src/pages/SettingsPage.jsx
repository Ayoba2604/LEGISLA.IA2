import { useEffect, useMemo, useState } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { useAuth } from '../lib/auth'
import { getUserInitials } from '../lib/profile'
import { useThemePreference } from '../lib/theme'

const SETTINGS_TABS = [
  { id: 'perfil', label: 'Perfil', icon: 'bi bi-person-circle' },
  { id: 'preferencias', label: 'Preferencias', icon: 'bi bi-sliders' },
]

function fileToDataUrl(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => resolve(String(reader.result || ''))
    reader.onerror = () => reject(new Error('Nao foi possivel carregar a imagem selecionada.'))
    reader.readAsDataURL(file)
  })
}

export default function SettingsPage() {
  const { user, loading, updateProfile } = useAuth()
  const [theme, setTheme] = useThemePreference()
  const navigate = useNavigate()
  const [searchParams, setSearchParams] = useSearchParams()
  const [name, setName] = useState('')
  const [photoPreview, setPhotoPreview] = useState('')
  const [saving, setSaving] = useState(false)
  const [notice, setNotice] = useState('')

  const activeTab = searchParams.get('tab') === 'preferencias' ? 'preferencias' : 'perfil'

  useEffect(() => {
    if (!loading && !user) {
      navigate('/login')
    }
  }, [user, loading, navigate])

  useEffect(() => {
    if (!user) return
    setName(user.nome || '')
    setPhotoPreview(user.fotoUrl || '')
  }, [user])

  const isDirty = useMemo(() => {
    if (!user) return false
    return name.trim() !== user.nome || (photoPreview || '') !== (user.fotoUrl || '')
  }, [name, photoPreview, user])

  const handleTabChange = (nextTab) => {
    setSearchParams({ tab: nextTab })
    setNotice('')
  }

  const handleFileChange = async (event) => {
    const file = event.target.files?.[0]
    if (!file) return

    try {
      const dataUrl = await fileToDataUrl(file)
      setPhotoPreview(dataUrl)
      setNotice('Nova foto pronta para salvar.')
    } catch (err) {
      setNotice(err.message)
    }
  }

  const handleProfileSave = async (event) => {
    event.preventDefault()

    if (!user) return

    try {
      setSaving(true)
      const data = await updateProfile({
        nome: name.trim(),
        fotoUrl: photoPreview || null,
      })

      if (!data.ok) {
        setNotice(data.erro || 'Nao foi possivel atualizar o perfil.')
        return
      }

      setNotice('Perfil atualizado com sucesso.')
    } catch (err) {
      setNotice(err.message)
    } finally {
      setSaving(false)
    }
  }

  if (loading) {
    return (
      <section className="section-shell admin-loading-shell">
        <div className="admin-loading-state">
          <span className="admin-loading-pulse"></span>
          <p>Carregando suas configuracoes...</p>
        </div>
      </section>
    )
  }

  if (!user) return null

  return (
    <section className="settings-page">
      <header className="settings-hero">
        <div>
          <span className="section-kicker">Conta e preferencias</span>
          <h1 className="settings-title">Configurar seu ambiente</h1>
          <p className="settings-subtitle">
            Ajuste seu perfil, mantenha a conta identificada com clareza e deixe algumas preferencias prontas para evoluir no futuro.
          </p>
        </div>

        <div className="settings-hero-card">
          {photoPreview ? (
            <img className="settings-avatar-image large" src={photoPreview} alt="" />
          ) : (
            <div className="settings-avatar large">{getUserInitials(name || user.nome)}</div>
          )}
          <div>
            <strong>{user.nome}</strong>
            <span>{user.email}</span>
            <small>{user.admin ? 'Conta administrativa ativa' : 'Conta autenticada'}</small>
          </div>
        </div>
      </header>

      <div className="settings-tabs" role="tablist" aria-label="Abas de configuracao">
        {SETTINGS_TABS.map((tab) => (
          <button
            key={tab.id}
            type="button"
            className={`settings-tab${activeTab === tab.id ? ' active' : ''}`}
            onClick={() => handleTabChange(tab.id)}
          >
            <i className={tab.icon} aria-hidden="true"></i>
            <span>{tab.label}</span>
          </button>
        ))}
      </div>

      {notice ? <div className="admin-flash-message">{notice}</div> : null}

      {activeTab === 'perfil' ? (
        <div className="settings-grid">
          <section className="settings-panel">
            <div className="settings-panel-head">
              <div>
                <span className="admin-mini-label">Perfil</span>
                <h2>Conta em uso</h2>
                <p>Seu nome e sua foto aparecem para identificar melhor a sessao atual em toda a interface.</p>
              </div>
            </div>

            <form className="settings-form" onSubmit={handleProfileSave}>
              <div className="settings-avatar-row">
                {photoPreview ? (
                  <img className="settings-avatar-image" src={photoPreview} alt="" />
                ) : (
                  <div className="settings-avatar">{getUserInitials(name || user.nome)}</div>
                )}

                <div className="settings-avatar-copy">
                  <strong>Foto do perfil</strong>
                  <p>Use uma imagem leve para evitar upload demorado no navegador.</p>
                  <div className="settings-avatar-actions">
                    <label className="admin-ghost-button settings-file-button">
                      <i className="bi bi-image" aria-hidden="true"></i>
                      <span>Escolher foto</span>
                      <input type="file" accept="image/*" onChange={handleFileChange} />
                    </label>
                    {photoPreview ? (
                      <button type="button" className="admin-ghost-button" onClick={() => setPhotoPreview('')}>
                        <i className="bi bi-x-circle" aria-hidden="true"></i>
                        <span>Remover foto</span>
                      </button>
                    ) : null}
                  </div>
                </div>
              </div>

              <label className="admin-input-group">
                <span>Nome exibido</span>
                <input
                  type="text"
                  value={name}
                  onChange={(event) => setName(event.target.value)}
                  placeholder="Como voce quer aparecer no sistema"
                />
              </label>

              <div className="settings-readonly-grid">
                <div className="settings-readonly-card">
                  <span>Email</span>
                  <strong>{user.email}</strong>
                </div>
                <div className="settings-readonly-card">
                  <span>Perfil</span>
                  <strong>{user.admin ? 'Administrador' : 'Usuario'}</strong>
                </div>
              </div>

              <div className="settings-form-actions">
                <button type="submit" className="admin-table-button success" disabled={saving || !isDirty}>
                  <i className="bi bi-check2-circle" aria-hidden="true"></i>
                  <span>{saving ? 'Salvando...' : 'Salvar alteracoes'}</span>
                </button>
                <Link className="admin-ghost-button" to="/chat">
                  <i className="bi bi-stars" aria-hidden="true"></i>
                  <span>Ir para a IA</span>
                </Link>
              </div>
            </form>
          </section>

          <aside className="settings-panel settings-side-panel">
            <div className="settings-panel-head">
              <div>
                <span className="admin-mini-label">Resumo</span>
                <h2>Presenca da conta</h2>
              </div>
            </div>

            <div className="settings-summary-list">
              <div className="settings-summary-item">
                <strong>Conta atual</strong>
                <p>Voce esta navegando como {user.nome}, e esse resumo agora ajuda a enxergar rapidamente em qual conta a sessao esta aberta.</p>
              </div>
              <div className="settings-summary-item">
                <strong>Visibilidade</strong>
                <p>A foto e o nome passam a aparecer no menu de conta do canto superior direito para deixar a sessao sempre identificada.</p>
              </div>
              <div className="settings-summary-item">
                <strong>Seguranca</strong>
                <p>O email segue como referencia fixa da conta autenticada, mesmo quando o nome exibido mudar.</p>
              </div>
            </div>
          </aside>
        </div>
      ) : null}

      {activeTab === 'preferencias' ? (
        <div className="settings-grid">
          <section className="settings-panel">
            <div className="settings-panel-head">
              <div>
                <span className="admin-mini-label">Preferencias</span>
                <h2>Ambiente da plataforma</h2>
                <p>Essas configuracoes deixam o tema pronto agora e reservam espaco para futuras personalizacoes da IA.</p>
              </div>
            </div>

            <div className="settings-preferences-grid">
              <article className="settings-preference-card">
                <div>
                  <strong>Tema</strong>
                  <p>Escolha a aparencia principal do sistema.</p>
                </div>
                <div className="settings-choice-row">
                  <button
                    type="button"
                    className={`settings-choice-button${theme === 'light' ? ' active' : ''}`}
                    onClick={() => setTheme('light')}
                  >
                    <i className="bi bi-sun" aria-hidden="true"></i>
                    <span>Claro</span>
                  </button>
                  <button
                    type="button"
                    className={`settings-choice-button${theme === 'dark' ? ' active' : ''}`}
                    onClick={() => setTheme('dark')}
                  >
                    <i className="bi bi-moon-stars" aria-hidden="true"></i>
                    <span>Escuro</span>
                  </button>
                </div>
              </article>

              <article className="settings-preference-card">
                <div>
                  <strong>Personalidade da IA</strong>
                  <p>Ja deixei a estrutura preparada para futuras variacoes sem mexer no fluxo principal agora.</p>
                </div>
                <div className="settings-placeholder-pill">
                  <i className="bi bi-stars" aria-hidden="true"></i>
                  <span>Padrao</span>
                </div>
              </article>

              <article className="settings-preference-card">
                <div>
                  <strong>Outras opcoes futuras</strong>
                  <p>Esse bloco pode receber em breve estilo de resposta, memoria, notificacoes e preferencia de linguagem.</p>
                </div>
                <div className="settings-placeholder-list">
                  <span>Memoria da conversa</span>
                  <span>Tom de resposta</span>
                  <span>Notificacoes</span>
                </div>
              </article>
            </div>
          </section>

          <aside className="settings-panel settings-side-panel">
            <div className="settings-panel-head">
              <div>
                <span className="admin-mini-label">Estado atual</span>
                <h2>Preferencias ativas</h2>
              </div>
            </div>

            <div className="settings-summary-list">
              <div className="settings-summary-item">
                <strong>Tema do sistema</strong>
                <p>{theme === 'dark' ? 'Escuro' : 'Claro'}</p>
              </div>
              <div className="settings-summary-item">
                <strong>Personalidade da IA</strong>
                <p>Padrao</p>
              </div>
              <div className="settings-summary-item">
                <strong>Proximo passo</strong>
                <p>As configuracoes da IA tambem aparecem no botao de ajustes dentro do chat para facilitar o acesso rapido.</p>
              </div>
            </div>
          </aside>
        </div>
      ) : null}
    </section>
  )
}

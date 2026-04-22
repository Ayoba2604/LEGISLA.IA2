import { useCallback, useEffect, useMemo, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../lib/auth'
import { apiDelete, apiFetch, apiPatch } from '../lib/api'
import { getUserInitials } from '../lib/profile'

const TABS = [
  { id: 'overview', label: 'Visao geral', icon: 'bi bi-grid-1x2-fill' },
  { id: 'analytics', label: 'Graficos', icon: 'bi bi-bar-chart-line-fill' },
  { id: 'users', label: 'Usuarios', icon: 'bi bi-people-fill' },
  { id: 'permissions', label: 'Permissoes', icon: 'bi bi-shield-check' },
]

const EMPTY_METRICS = {
  summary: { page_views: 0, logins: 0, admin_actions: 0, registers: 0 },
  daily: [],
  top_routes: [],
}

const METRICS_REFRESH_MS = 1800000
const METRICS_RANGE_DAYS = 120
const LINE_CHART_WIDTH = 760
const LINE_CHART_HEIGHT = 320
const LINE_CHART_PADDING = { top: 16, right: 18, bottom: 38, left: 44 }

function formatCount(value) {
  return new Intl.NumberFormat('pt-BR').format(value || 0)
}

function formatStamp() {
  return new Intl.DateTimeFormat('pt-BR', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' }).format(new Date())
}

function formatClock(date = new Date()) {
  return new Intl.DateTimeFormat('pt-BR', { hour: '2-digit', minute: '2-digit', second: '2-digit' }).format(date)
}

function formatLongDate(entry) {
  return `${String(entry.day).padStart(2, '0')}/${String(entry.month).padStart(2, '0')}/${entry.year}`
}

function buildLinePoints(data, metricKey, maxValue) {
  if (!data.length) return ''

  const innerWidth = LINE_CHART_WIDTH - LINE_CHART_PADDING.left - LINE_CHART_PADDING.right
  const innerHeight = LINE_CHART_HEIGHT - LINE_CHART_PADDING.top - LINE_CHART_PADDING.bottom
  const safeMax = Math.max(1, maxValue)

  return data.map((entry, index) => {
    const x = LINE_CHART_PADDING.left + (data.length === 1 ? innerWidth / 2 : (index / (data.length - 1)) * innerWidth)
    const y = LINE_CHART_PADDING.top + innerHeight - ((entry[metricKey] || 0) / safeMax) * innerHeight
    return `${x},${y}`
  }).join(' ')
}

function buildYAxis(maxValue) {
  const safeMax = Math.max(1, maxValue)
  return [1, 0.75, 0.5, 0.25, 0].map((ratio) => ({
    label: Math.round(safeMax * ratio),
    y: LINE_CHART_PADDING.top + (LINE_CHART_HEIGHT - LINE_CHART_PADDING.top - LINE_CHART_PADDING.bottom) * (1 - ratio),
  }))
}

function userHint(entry, currentUserId) {
  if (entry.id_usuario === currentUserId) return 'Conta em uso nesta sessao'
  return entry.admin ? 'Administrador da plataforma' : 'Usuario cadastrado no sistema'
}

function Avatar({ user, large = false }) {
  if (user?.foto_url) {
    return <img className={`admin-avatar-image${large ? ' large' : ''}`} src={user.foto_url} alt="" />
  }

  return <div className={`admin-avatar-badge${large ? ' large' : ''}`}>{getUserInitials(user?.nome)}</div>
}

export default function AdminUsersPage() {
  const { user, loading: authLoading } = useAuth()
  const navigate = useNavigate()
  const [users, setUsers] = useState([])
  const [metrics, setMetrics] = useState(EMPTY_METRICS)
  const [loading, setLoading] = useState(true)
  const [msg, setMsg] = useState('')
  const [activeTab, setActiveTab] = useState('overview')
  const [searchTerm, setSearchTerm] = useState('')
  const [roleFilter, setRoleFilter] = useState('all')
  const [sortMode, setSortMode] = useState('recent')
  const [selectedUserId, setSelectedUserId] = useState(null)
  const [lastAction, setLastAction] = useState(null)
  const [metricsRefreshing, setMetricsRefreshing] = useState(false)
  const [metricsUpdatedAt, setMetricsUpdatedAt] = useState('')
  const [filterDay, setFilterDay] = useState('')
  const [filterMonth, setFilterMonth] = useState('')
  const [filterYear, setFilterYear] = useState('')
  const [selectedDate, setSelectedDate] = useState('')

  useEffect(() => {
    if (!authLoading && (!user || !user.admin)) navigate('/login')
  }, [authLoading, navigate, user])

  const syncUsers = (data) => {
    setUsers(data)
    setSelectedUserId((current) => current && data.some((entry) => entry.id_usuario === current) ? current : data[0]?.id_usuario ?? null)
  }

  const loadMetrics = useCallback(async () => {
    setMetricsRefreshing(true)
    try {
      const metricsData = await apiFetch(`/api/admin/metrics?days=${METRICS_RANGE_DAYS}`)
      setMetrics(metricsData || EMPTY_METRICS)
      setMetricsUpdatedAt(formatClock())
    } finally {
      setMetricsRefreshing(false)
    }
  }, [])

  const loadDashboard = useCallback(async () => {
    try {
      const [usersData, metricsData] = await Promise.all([apiFetch('/api/admin/users'), apiFetch(`/api/admin/metrics?days=${METRICS_RANGE_DAYS}`)])
      syncUsers(usersData)
      setMetrics(metricsData || EMPTY_METRICS)
      setMetricsUpdatedAt(formatClock())
    } catch (err) {
      setMsg('Erro ao carregar a central: ' + err.message)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    if (user?.admin) loadDashboard()
  }, [loadDashboard, user])

  useEffect(() => {
    if (!user?.admin) return undefined

    const delayedRefresh = window.setTimeout(() => {
      loadMetrics().catch(() => {})
    }, 1200)

    return () => window.clearTimeout(delayedRefresh)
  }, [loadMetrics, user])

  useEffect(() => {
    if (!user?.admin) return undefined

    const interval = window.setInterval(() => {
      loadMetrics().catch(() => {})
    }, METRICS_REFRESH_MS)

    return () => window.clearInterval(interval)
  }, [loadMetrics, user])

  useEffect(() => {
    if (!user?.admin) return undefined

    const refreshMetrics = () => {
      loadMetrics().catch(() => {})
    }

    window.addEventListener('legisla-analytics-recorded', refreshMetrics)
    return () => window.removeEventListener('legisla-analytics-recorded', refreshMetrics)
  }, [loadMetrics, user])

  const noteAction = (text) => {
    setMsg(text)
    setLastAction({ text, at: formatStamp() })
  }

  const refreshAfterMutation = async (text) => {
    noteAction(text)
    await loadDashboard()
  }

  const handleDelete = async (targetUser) => {
    if (targetUser.id_usuario === user?.id) return setMsg('Voce nao pode deletar a propria conta enquanto estiver logado.')
    if (!confirm(`Tem certeza que deseja deletar o usuario ${targetUser.nome}?`)) return

    try {
      await apiDelete(`/api/admin/users/${targetUser.id_usuario}`)
      await refreshAfterMutation(`Usuario ${targetUser.nome} deletado com sucesso.`)
    } catch (err) {
      setMsg('Erro ao deletar: ' + err.message)
    }
  }

  const handleToggleAdmin = async (targetUser) => {
    if (targetUser.id_usuario === user?.id && targetUser.admin) return setMsg('Voce nao pode remover o proprio acesso de administrador.')
    const nextAdmin = !targetUser.admin
    if (!confirm(`Tem certeza que deseja ${nextAdmin ? 'tornar admin' : 'revogar o admin de'} ${targetUser.nome}?`)) return

    try {
      await apiPatch(`/api/admin/users/${targetUser.id_usuario}/role?admin=${nextAdmin}`)
      await refreshAfterMutation(nextAdmin ? `${targetUser.nome} agora faz parte da equipe admin.` : `Privilegios de admin revogados para ${targetUser.nome}.`)
    } catch (err) {
      setMsg('Erro: ' + err.message)
    }
  }

  const handleCopyEmail = async (targetUser) => {
    try {
      await navigator.clipboard.writeText(targetUser.email)
      noteAction(`Email de ${targetUser.nome} copiado.`)
    } catch {
      setMsg('Nao foi possivel copiar o email.')
    }
  }

  const filteredUsers = useMemo(() => {
    const term = searchTerm.trim().toLowerCase()
    const nextUsers = users
      .filter((entry) => roleFilter === 'all' ? true : roleFilter === 'admins' ? entry.admin : !entry.admin)
      .filter((entry) => !term || `${entry.nome} ${entry.email} ${entry.id_usuario}`.toLowerCase().includes(term))

    if (sortMode === 'name') nextUsers.sort((a, b) => a.nome.localeCompare(b.nome, 'pt-BR'))
    else if (sortMode === 'admins-first') nextUsers.sort((a, b) => Number(b.admin) - Number(a.admin) || a.nome.localeCompare(b.nome, 'pt-BR'))
    else nextUsers.sort((a, b) => b.id_usuario - a.id_usuario)

    return nextUsers
  }, [roleFilter, searchTerm, sortMode, users])

  const adminUsers = users.filter((entry) => entry.admin)
  const totalUsers = users.length
  const regularUsers = totalUsers - adminUsers.length
  const adminCoverage = totalUsers ? Math.round((adminUsers.length / totalUsers) * 100) : 0
  const recentUsers = [...users].sort((a, b) => b.id_usuario - a.id_usuario).slice(0, 4)
  const selectedUser = users.find((entry) => entry.id_usuario === selectedUserId) || filteredUsers[0] || null
  const summary = metrics.summary || EMPTY_METRICS.summary
  const chartData = metrics.daily || []
  const topRoutes = metrics.top_routes || []
  const topRoute = topRoutes[0]
  const availableYears = [...new Set(chartData.map((entry) => String(entry.year)))].sort((a, b) => Number(b) - Number(a))
  const availableMonths = [...new Set(chartData
    .filter((entry) => !filterYear || String(entry.year) === filterYear)
    .map((entry) => String(entry.month).padStart(2, '0')))].sort((a, b) => Number(a) - Number(b))
  const availableDays = [...new Set(chartData
    .filter((entry) => (!filterYear || String(entry.year) === filterYear) && (!filterMonth || String(entry.month).padStart(2, '0') === filterMonth))
    .map((entry) => String(entry.day).padStart(2, '0')))].sort((a, b) => Number(a) - Number(b))
  const filteredChartData = chartData.filter((entry) =>
    (!filterYear || String(entry.year) === filterYear) &&
    (!filterMonth || String(entry.month).padStart(2, '0') === filterMonth) &&
    (!filterDay || String(entry.day).padStart(2, '0') === filterDay),
  )
  const selectedDayData =
    filteredChartData.find((entry) => entry.date === selectedDate) ||
    filteredChartData[filteredChartData.length - 1] ||
    null
  const hourlyData = selectedDayData?.hours || []
  const hourlyPeak = Math.max(1, ...hourlyData.map((entry) => entry.total_requests || 0))
  const yAxisTicks = buildYAxis(hourlyPeak)
  const stats = [
    ['bi bi-people-fill', 'Usuarios totais', formatCount(totalUsers), 'Base geral da plataforma'],
    ['bi bi-shield-lock-fill', 'Admins ativos', formatCount(adminUsers.length), 'Contas com acesso ao painel'],
    ['bi bi-bar-chart-line-fill', 'Acessos em 7 dias', formatCount(summary.page_views), 'Paginas vistas na aplicacao'],
    ['bi bi-box-arrow-in-right', 'Logins em 7 dias', formatCount(summary.logins), 'Entradas autenticadas registradas'],
  ]

  useEffect(() => {
    if (!filteredChartData.length) {
      setSelectedDate('')
      return
    }

    if (!filteredChartData.some((entry) => entry.date === selectedDate)) {
      setSelectedDate(filteredChartData[filteredChartData.length - 1].date)
    }
  }, [filteredChartData, selectedDate])

  if (authLoading || loading) {
    return <section className="section-shell admin-loading-shell"><div className="admin-loading-state"><span className="admin-loading-pulse"></span><p>Montando a dashboard administrativa...</p></div></section>
  }

  return (
    <section className="admin-dashboard">
      <aside className="admin-sidebar">
        <div className="admin-sidebar-brand">
          <div className="admin-sidebar-logo"><img src="/favicon.svg" alt="" /></div>
          <div><strong>Legisla.IA</strong><span>Painel administrativo</span></div>
        </div>

        <nav className="admin-sidebar-nav" aria-label="Secoes da dashboard">
          {TABS.map((tab) => (
            <button key={tab.id} type="button" className={`admin-side-link${activeTab === tab.id ? ' active' : ''}`} onClick={() => setActiveTab(tab.id)}>
              <i className={tab.icon} aria-hidden="true"></i><span>{tab.label}</span>
            </button>
          ))}
          <Link className="admin-side-link" to="/configuracoes?tab=perfil"><i className="bi bi-person-gear" aria-hidden="true"></i><span>Conta</span></Link>
          <Link className="admin-side-link" to="/chat"><i className="bi bi-stars" aria-hidden="true"></i><span>Assistente IA</span></Link>
        </nav>

        <div className="admin-sidebar-card">
          <span className="admin-mini-label">Conta atual</span>
          <strong>{user?.nome || 'Administrador'}</strong>
          <p>Agora a central separa analise, usuarios e permissoes para evitar uma tela longa demais.</p>
          <div className="admin-mini-chip"><i className="bi bi-patch-check-fill" aria-hidden="true"></i><span>Modo admin ativo</span></div>
        </div>

        <div className="admin-sidebar-card">
          <span className="admin-mini-label">Area analitica</span>
          <strong>Painel de graficos</strong>
          <p>Abra a area dedicada para acompanhar acessos, logins, cadastros e rotas mais ativas.</p>
          <button type="button" className="admin-sidebar-open-button" onClick={() => setActiveTab('analytics')}>
            <i className="bi bi-bar-chart-line-fill" aria-hidden="true"></i>
            <span>Abrir graficos</span>
          </button>
        </div>
      </aside>

      <div className="admin-mainboard">
        <header className="admin-topbar">
          <div>
            <span className="section-kicker">{activeTab === 'overview' ? 'Panorama' : activeTab === 'analytics' ? 'Graficos' : activeTab === 'users' ? 'Usuarios' : 'Permissoes'}</span>
            <h1 className="admin-page-title">{activeTab === 'overview' ? 'Visao operacional e analitica' : activeTab === 'analytics' ? 'Area detalhada de graficos' : activeTab === 'users' ? 'Gestao da base cadastrada' : 'Equipe admin e controles'}</h1>
            <p className="admin-page-subtitle">{activeTab === 'overview' ? 'Acessos, logins, rotas mais visitadas e um resumo limpo do movimento recente da plataforma.' : activeTab === 'analytics' ? 'Leitura detalhada dos eventos do sistema com atualizacao automatica a cada 10 segundos e recarga manual.' : activeTab === 'users' ? 'Busca, filtros e detalhe lateral para operar a base sem transformar a tela em um sumario longo.' : 'Visao focada no grupo administrativo, cobertura de acesso e acoes rapidas mais sensiveis.'}</p>
          </div>
          <div className="admin-topbar-actions">
            <button type="button" className="admin-ghost-button" onClick={loadDashboard}><i className="bi bi-arrow-repeat" aria-hidden="true"></i><span>Atualizar dados</span></button>
            <div className="admin-user-pill"><i className="bi bi-person-circle" aria-hidden="true"></i><span>{user?.nome || 'Admin'}</span></div>
          </div>
        </header>

        {msg ? <div className="admin-flash-message">{msg}</div> : null}

        {activeTab === 'overview' ? (
          <>
            <div className="admin-stats-grid">
              {stats.map(([icon, label, value, meta]) => (
                <article key={label} className="admin-stat-card">
                  <div className="admin-stat-icon"><i className={icon} aria-hidden="true"></i></div>
                  <div className="admin-stat-copy"><span>{label}</span><strong>{value}</strong><p>{meta}</p></div>
                </article>
              ))}
            </div>

            <div className="admin-highlights-grid">
              <article className="admin-panel">
                <div className="admin-panel-head"><div><span className="admin-mini-label">Resumo operacional</span><h2>Pontos de atencao</h2></div><span className="admin-period-pill">Painel ao vivo</span></div>
                <div className="admin-highlight-list">
                  <div className="admin-highlight-item"><strong>Distribuicao da base</strong><p>Hoje a plataforma tem {formatCount(adminUsers.length)} admins e {formatCount(regularUsers)} usuarios comuns.</p></div>
                  <div className="admin-highlight-item"><strong>Ultima acao executada</strong><p>{lastAction ? `${lastAction.text} as ${lastAction.at}.` : 'Nenhuma acao administrativa foi registrada nesta sessao ainda.'}</p></div>
                  <div className="admin-highlight-item"><strong>Leitura do painel</strong><p>A area analitica mostra uso real do sistema enquanto as outras abas ficam livres para gestao direta.</p></div>
                </div>
              </article>

              <article className="admin-panel">
                <div className="admin-panel-head"><div><span className="admin-mini-label">Entradas recentes</span><h2>Ultimos usuarios na base</h2></div></div>
                <div className="admin-recent-list">
                  {recentUsers.map((entry) => (
                    <button key={entry.id_usuario} type="button" className={`admin-recent-item${selectedUserId === entry.id_usuario ? ' active' : ''}`} onClick={() => { setSelectedUserId(entry.id_usuario); setActiveTab('users') }}>
                      <Avatar user={entry} />
                      <div className="admin-recent-copy"><strong>{entry.nome}</strong><span className="admin-recent-email" title={entry.email}>{entry.email}</span></div>
                      <span className={`admin-role-pill${entry.admin ? ' is-admin' : ''}`}>{entry.admin ? 'Admin' : 'Usuario'}</span>
                    </button>
                  ))}
                </div>
              </article>
            </div>
          </>
        ) : null}

        {activeTab === 'analytics' ? (
          <div className="admin-analytics-grid">
            <article className="admin-panel admin-chart-panel">
                <div className="admin-panel-head">
                <div>
                  <span className="admin-mini-label">Leitura ao vivo</span>
                  <h2>Requisicoes ao longo do dia</h2>
                  <p>O eixo X mostra o horario de 00:00 ate 23:59 e o eixo Y mostra a quantidade de requisicoes no dia selecionado.</p>
                </div>
                <div className="admin-topbar-actions">
                  <div className="admin-period-pill">Atualizado {metricsUpdatedAt || '--:--:--'}</div>
                  <button type="button" className="admin-ghost-button" onClick={() => loadMetrics().catch(() => {})} disabled={metricsRefreshing}>
                    <i className={`bi ${metricsRefreshing ? 'bi-arrow-repeat admin-spin-icon' : 'bi-arrow-repeat'}`} aria-hidden="true"></i>
                    <span>{metricsRefreshing ? 'Atualizando' : 'Atualizar agora'}</span>
                  </button>
                </div>
              </div>

              <div className="admin-chart-filters">
                <label className="admin-input-group">
                  <span>Ano</span>
                  <select value={filterYear} onChange={(event) => { setFilterYear(event.target.value); setFilterMonth(''); setFilterDay('') }}>
                    <option value="">Todos</option>
                    {availableYears.map((year) => <option key={year} value={year}>{year}</option>)}
                  </select>
                </label>
                <label className="admin-input-group">
                  <span>Mes</span>
                  <select value={filterMonth} onChange={(event) => { setFilterMonth(event.target.value); setFilterDay('') }}>
                    <option value="">Todos</option>
                    {availableMonths.map((month) => <option key={month} value={month}>{month}</option>)}
                  </select>
                </label>
                <label className="admin-input-group">
                  <span>Dia</span>
                  <select value={filterDay} onChange={(event) => setFilterDay(event.target.value)}>
                    <option value="">Todos</option>
                    {availableDays.map((day) => <option key={day} value={day}>{day}</option>)}
                  </select>
                </label>
                <label className="admin-input-group">
                  <span>Data especifica</span>
                  <select value={selectedDate} onChange={(event) => setSelectedDate(event.target.value)}>
                    {!filteredChartData.length ? <option value="">Sem dados</option> : null}
                    {filteredChartData.map((entry) => (
                      <option key={entry.date} value={entry.date}>{formatLongDate(entry)}</option>
                    ))}
                  </select>
                </label>
              </div>

              <div className="admin-chart-legend">
                <span><i className="admin-legend-dot total"></i>Requisicoes totais por horario</span>
              </div>

              {selectedDayData ? (
                <div className="admin-line-chart-shell">
                  <svg viewBox={`0 0 ${LINE_CHART_WIDTH} ${LINE_CHART_HEIGHT}`} className="admin-line-chart" role="img" aria-label="Grafico de requisicoes por horario">
                    {yAxisTicks.map((tick) => (
                      <g key={`${tick.label}-${tick.y}`}>
                        <line
                          x1={LINE_CHART_PADDING.left}
                          y1={tick.y}
                          x2={LINE_CHART_WIDTH - LINE_CHART_PADDING.right}
                          y2={tick.y}
                          className="admin-chart-grid-line"
                        />
                        <text x={LINE_CHART_PADDING.left - 12} y={tick.y + 4} className="admin-chart-axis-label is-y">
                          {tick.label}
                        </text>
                      </g>
                    ))}

                    <line
                      x1={LINE_CHART_PADDING.left}
                      y1={LINE_CHART_HEIGHT - LINE_CHART_PADDING.bottom}
                      x2={LINE_CHART_WIDTH - LINE_CHART_PADDING.right}
                      y2={LINE_CHART_HEIGHT - LINE_CHART_PADDING.bottom}
                      className="admin-chart-axis"
                    />
                    <line
                      x1={LINE_CHART_PADDING.left}
                      y1={LINE_CHART_PADDING.top}
                      x2={LINE_CHART_PADDING.left}
                      y2={LINE_CHART_HEIGHT - LINE_CHART_PADDING.bottom}
                      className="admin-chart-axis"
                    />

                    <polyline
                      fill="none"
                      points={buildLinePoints(hourlyData, 'total_requests', hourlyPeak)}
                      className="admin-line-path total"
                    />

                    {hourlyData.map((entry, index) => {
                      const innerWidth = LINE_CHART_WIDTH - LINE_CHART_PADDING.left - LINE_CHART_PADDING.right
                      const innerHeight = LINE_CHART_HEIGHT - LINE_CHART_PADDING.top - LINE_CHART_PADDING.bottom
                      const x = LINE_CHART_PADDING.left + (hourlyData.length === 1 ? innerWidth / 2 : (index / (hourlyData.length - 1)) * innerWidth)
                      const y = LINE_CHART_PADDING.top + innerHeight - ((entry.total_requests || 0) / Math.max(1, hourlyPeak)) * innerHeight

                      return (
                        <circle
                          key={`hour-${entry.hour}`}
                          cx={x}
                          cy={y}
                          r="3.5"
                          className="admin-line-point total"
                        />
                      )
                    })}

                    {hourlyData.map((entry, index) => {
                      const labelHours = [0, 4, 8, 12, 16, 20, 23]
                      if (!labelHours.includes(entry.hour)) {
                        return null
                      }

                      const innerWidth = LINE_CHART_WIDTH - LINE_CHART_PADDING.left - LINE_CHART_PADDING.right
                      const x = LINE_CHART_PADDING.left + (hourlyData.length === 1 ? innerWidth / 2 : (index / (hourlyData.length - 1)) * innerWidth)

                      return (
                        <text
                          key={`label-${entry.hour}`}
                          x={x}
                          y={LINE_CHART_HEIGHT - 12}
                          textAnchor="middle"
                          className="admin-chart-axis-label"
                        >
                          {entry.hour === 23 ? '23:59' : entry.label}
                        </text>
                      )
                    })}
                  </svg>
                </div>
              ) : (
                <div className="admin-empty-sidecard compact">
                  <i className="bi bi-bar-chart-line" aria-hidden="true"></i>
                  <span>Nenhum dado encontrado para esse filtro de dia, mes e ano.</span>
                </div>
              )}
            </article>

            <aside className="admin-panel admin-analytics-side">
              <div className="admin-panel-head">
                <div>
                  <span className="admin-mini-label">Indicadores</span>
                  <h2>Resumo do analytics</h2>
                </div>
              </div>

              <div className="admin-health-list">
                <div className="admin-health-item"><span>Acessos</span><strong>{formatCount(summary.page_views)}</strong><p>Total registrado de page views na janela atual.</p></div>
                <div className="admin-health-item"><span>Logins</span><strong>{formatCount(summary.logins)}</strong><p>Entradas autenticadas nos ultimos 7 dias.</p></div>
                <div className="admin-health-item"><span>Cadastros</span><strong>{formatCount(summary.registers)}</strong><p>Novas contas criadas nesse mesmo periodo.</p></div>
                <div className="admin-health-item"><span>Rota lider</span><strong>{topRoute?.route || '/admin'}</strong><p>{topRoute ? `${formatCount(topRoute.count)} visitas acumuladas.` : 'Sem trafego suficiente ainda.'}</p></div>
              </div>

              <div className="admin-panel-head">
                <div>
                  <span className="admin-mini-label">Dia selecionado</span>
                  <h2>{selectedDayData ? formatLongDate(selectedDayData) : 'Sem data ativa'}</h2>
                  <p>Leitura rapida do que aconteceu no dia escolhido no filtro logo abaixo do grafico.</p>
                </div>
              </div>

              {selectedDayData ? (
                <div className="admin-health-list">
                  <div className="admin-health-item"><span>Requisicoes no dia</span><strong>{formatCount(selectedDayData.total_events)}</strong><p>Total de eventos registrados ao longo do dia selecionado.</p></div>
                  <div className="admin-health-item"><span>Pico por hora</span><strong>{formatCount(Math.max(0, ...hourlyData.map((entry) => entry.total_requests || 0)))}</strong><p>Maior volume de requisicoes em uma unica hora do dia.</p></div>
                  <div className="admin-health-item"><span>Hora mais ativa</span><strong>{hourlyData.reduce((best, entry) => (entry.total_requests > (best?.total_requests || -1) ? entry : best), null)?.label || '--:--'}</strong><p>Horario com maior volume de requisicoes na data filtrada.</p></div>
                  <div className="admin-health-item"><span>Destaque do dia</span><strong>{selectedDayData.top_route?.route || 'Sem rota lider'}</strong><p>{selectedDayData.top_route ? `${formatCount(selectedDayData.top_route.count)} acessos nessa rota.` : 'Sem destaque de rota nesse dia.'}</p></div>
                </div>
              ) : null}

              <div className="admin-route-list">
                <div className="admin-route-head"><strong>Rotas mais vistas</strong><span>Top 5</span></div>
                {topRoutes.length ? topRoutes.map((entry) => <div key={entry.route} className="admin-route-row"><code>{entry.route}</code><strong>{formatCount(entry.count)}</strong></div>) : <div className="admin-route-row empty"><span>Sem rotas suficientes para listar ainda.</span></div>}
              </div>
            </aside>
          </div>
        ) : null}

        {activeTab === 'users' ? (
          <div className="admin-users-layout">
            <section className="admin-panel admin-table-panel">
              <div className="admin-panel-head admin-table-head">
                <div><span className="admin-mini-label">Diretorio</span><h2>Usuarios e filtros</h2><p>Busca por nome, email ou ID, filtro de perfil e ordenacao sob demanda.</p></div>
                <div className="admin-table-meta"><span>{formatCount(filteredUsers.length)} visiveis</span></div>
              </div>

              <div className="admin-toolbar">
                <label className="admin-input-group"><span>Buscar</span><input type="search" value={searchTerm} onChange={(event) => setSearchTerm(event.target.value)} placeholder="Nome, email ou ID" /></label>
                <label className="admin-input-group"><span>Perfil</span><select value={roleFilter} onChange={(event) => setRoleFilter(event.target.value)}><option value="all">Todos</option><option value="admins">Apenas admins</option><option value="regular">Apenas usuarios</option></select></label>
                <label className="admin-input-group"><span>Ordenar</span><select value={sortMode} onChange={(event) => setSortMode(event.target.value)}><option value="recent">Mais recentes</option><option value="name">Nome A-Z</option><option value="admins-first">Admins primeiro</option></select></label>
              </div>

              <div className="admin-table-wrap">
                <table className="admin-table">
                  <thead><tr><th>Usuario</th><th>ID</th><th>Email</th><th>Perfil</th><th>Acoes</th></tr></thead>
                  <tbody>
                    {filteredUsers.map((entry) => {
                      const isCurrentUser = entry.id_usuario === user?.id
                      return (
                        <tr key={entry.id_usuario} className={entry.admin ? 'is-admin-row' : ''} onClick={() => setSelectedUserId(entry.id_usuario)}>
                          <td><div className="admin-user-cell"><Avatar user={entry} /><div className="admin-user-copy"><strong>{entry.nome}</strong><span>{userHint(entry, user?.id)}</span></div></div></td>
                          <td>#{entry.id_usuario}</td>
                          <td className="admin-email-cell">{entry.email}</td>
                          <td><span className={`admin-role-pill${entry.admin ? ' is-admin' : ''}`}>{entry.admin ? 'Administrador' : 'Usuario'}</span></td>
                          <td><div className="admin-action-group">
                            <button type="button" className={`admin-table-button ${entry.admin ? 'warning' : 'success'}`} onClick={(event) => { event.stopPropagation(); handleToggleAdmin(entry) }} disabled={isCurrentUser && entry.admin}><i className={`bi ${entry.admin ? 'bi-arrow-down-circle' : 'bi-arrow-up-circle'}`} aria-hidden="true"></i><span>{entry.admin ? 'Revogar' : 'Promover'}</span></button>
                            <button type="button" className="admin-table-button danger" onClick={(event) => { event.stopPropagation(); handleDelete(entry) }} disabled={isCurrentUser}><i className="bi bi-trash3" aria-hidden="true"></i><span>Excluir</span></button>
                          </div></td>
                        </tr>
                      )
                    })}
                    {!filteredUsers.length ? <tr><td colSpan={5}><div className="admin-empty-state"><i className="bi bi-inboxes" aria-hidden="true"></i><span>Nenhum usuario encontrado para esse filtro.</span></div></td></tr> : null}
                  </tbody>
                </table>
              </div>
            </section>

            <aside className="admin-panel admin-detail-panel">
              <div className="admin-panel-head"><div><span className="admin-mini-label">Detalhe</span><h2>Usuario selecionado</h2></div></div>
              {selectedUser ? (
                <div className="admin-detail-card">
                  <div className="admin-detail-header"><Avatar user={selectedUser} large /><div className="admin-detail-copy"><strong>{selectedUser.nome}</strong><span>{selectedUser.email}</span></div></div>
                  <div className="admin-detail-grid">
                    <div><span>ID</span><strong>#{selectedUser.id_usuario}</strong></div>
                    <div><span>Perfil</span><strong>{selectedUser.admin ? 'Administrador' : 'Usuario'}</strong></div>
                    <div><span>Status</span><strong>{selectedUser.id_usuario === user?.id ? 'Conta atual' : 'Perfil externo'}</strong></div>
                    <div><span>Acesso</span><strong>{selectedUser.admin ? 'Completo' : 'Limitado'}</strong></div>
                  </div>
                  <div className="admin-detail-actions">
                    <button type="button" className="admin-ghost-button" onClick={() => handleCopyEmail(selectedUser)}><i className="bi bi-copy" aria-hidden="true"></i><span>Copiar email</span></button>
                    <button type="button" className={`admin-table-button ${selectedUser.admin ? 'warning' : 'success'}`} onClick={() => handleToggleAdmin(selectedUser)} disabled={selectedUser.id_usuario === user?.id && selectedUser.admin}><i className={`bi ${selectedUser.admin ? 'bi-arrow-down-circle' : 'bi-arrow-up-circle'}`} aria-hidden="true"></i><span>{selectedUser.admin ? 'Revogar admin' : 'Promover para admin'}</span></button>
                  </div>
                </div>
              ) : <div className="admin-empty-sidecard"><i className="bi bi-person-lines-fill" aria-hidden="true"></i><span>Selecione um usuario para ver mais detalhes e executar acoes rapidas.</span></div>}
            </aside>
          </div>
        ) : null}

        {activeTab === 'permissions' ? (
          <div className="admin-permissions-grid">
            <section className="admin-panel">
              <div className="admin-panel-head"><div><span className="admin-mini-label">Equipe admin</span><h2>Quem controla o painel hoje</h2><p>Visao dedicada aos administradores ativos e ao equilibrio da operacao.</p></div></div>
              <div className="admin-admin-list">
                {adminUsers.map((entry) => (
                  <div key={entry.id_usuario} className="admin-admin-card">
                    <div className="admin-user-cell"><Avatar user={entry} /><div className="admin-user-copy"><strong>{entry.nome}</strong><span>{entry.email}</span></div></div>
                    <div className="admin-admin-actions"><span className="admin-role-pill is-admin">Administrador</span><button type="button" className="admin-table-button warning" onClick={() => handleToggleAdmin(entry)} disabled={entry.id_usuario === user?.id}><i className="bi bi-arrow-down-circle" aria-hidden="true"></i><span>Revogar</span></button></div>
                  </div>
                ))}
                {!adminUsers.length ? <div className="admin-empty-sidecard"><i className="bi bi-shield-exclamation" aria-hidden="true"></i><span>Nenhum administrador encontrado.</span></div> : null}
              </div>
            </section>

            <aside className="admin-panel">
              <div className="admin-panel-head"><div><span className="admin-mini-label">Controles</span><h2>Saude do acesso</h2></div></div>
              <div className="admin-health-list">
                <div className="admin-health-item"><span>Cobertura admin</span><strong>{adminCoverage}%</strong><p>Proporcao atual de contas administrativas em relacao a base total.</p></div>
                <div className="admin-health-item"><span>Conta principal</span><strong>{user?.nome || 'Administrador'}</strong><p>Sua conta continua protegida contra auto-revogacao e auto-exclusao.</p></div>
                <div className="admin-health-item"><span>Acoes admin em 7 dias</span><strong>{formatCount(summary.admin_actions)}</strong><p>Volume recente de alteracoes sensiveis executadas pela equipe.</p></div>
                <div className="admin-health-item"><span>Ultima alteracao</span><strong>{lastAction ? lastAction.at : 'Sem registro'}</strong><p>{lastAction ? lastAction.text : 'Nenhuma alteracao nesta sessao ainda.'}</p></div>
              </div>
            </aside>
          </div>
        ) : null}
      </div>
    </section>
  )
}

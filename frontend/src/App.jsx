import { useEffect, useState } from 'react'
import './App.css'

const defaultData = {
  brand: 'Legisla.IA',
  logoSrc: '/favicon.svg',
  isLoggedIn: false,
  isAdmin: false,
  navLinks: [
    { href: '/public/index.php', label: 'Home' },
    { href: '/app/views/static/sobrenos.php', label: 'Sobre Nos' },
  ],
  heroActions: [
    {
      href: '/app/views/auth/formCadastro.php',
      label: 'Criar conta gratis',
      icon: 'bi bi-person-plus',
      variant: 'primary',
    },
    {
      href: '/app/views/auth/formLogin.php',
      label: 'Entrar',
      icon: 'bi bi-box-arrow-in-right',
      variant: 'secondary',
    },
  ],
  links: {
    chat: '/app/views/static/ia_chat.html',
    login: '/app/views/auth/formLogin.php',
    register: '/app/views/auth/formCadastro.php',
  },
  showcasePrompts: [
    {
      title: 'Trabalho',
      text: 'Posso faltar ao trabalho com atestado?',
      href: '/app/views/static/ia_chat.html?q=Posso%20faltar%20ao%20trabalho%20com%20atestado%3F',
      icon: 'bi bi-briefcase-fill',
    },
    {
      title: 'Consumidor',
      text: 'Quais sao meus direitos em uma compra com defeito?',
      href: '/app/views/static/ia_chat.html?q=Quais%20sao%20meus%20direitos%20em%20uma%20compra%20com%20defeito%3F',
      icon: 'bi bi-bag-check-fill',
    },
    {
      title: 'Familia',
      text: 'Como funciona pensao alimenticia no Brasil?',
      href: '/app/views/static/ia_chat.html?q=Como%20funciona%20pensao%20alimenticia%20no%20Brasil%3F',
      icon: 'bi bi-people-fill',
    },
  ],
}

const featureCards = [
  {
    icon: 'bi bi-chat-square-dots-fill',
    title: 'Tire duvidas rapido',
    text: 'Receba respostas iniciais em linguagem simples para situacoes do dia a dia.',
  },
  {
    icon: 'bi bi-journal-text',
    title: 'Entenda a base juridica',
    text: 'Transforme temas complexos em explicacoes objetivas e acessiveis.',
  },
  {
    icon: 'bi bi-file-earmark-pdf-fill',
    title: 'Resuma materiais',
    text: 'Envie PDFs ou links e use a IA para acelerar sua leitura inicial.',
  },
]

const audienceCards = [
  {
    icon: 'bi bi-people-fill',
    title: 'Cidadaos',
    text: 'Quem precisa de orientacao inicial antes de procurar apoio especializado.',
  },
  {
    icon: 'bi bi-mortarboard-fill',
    title: 'Estudantes',
    text: 'Quem quer revisar temas juridicos com exemplos mais proximos da pratica.',
  },
  {
    icon: 'bi bi-briefcase-fill',
    title: 'Times de projeto',
    text: 'Quem precisa explicar direitos e deveres de forma clara para outras pessoas.',
  },
  {
    icon: 'bi bi-shield-check',
    title: 'Uso responsavel',
    text: 'A plataforma ajuda na triagem inicial, sem substituir orientacao profissional.',
  },
]

const valuePillars = [
  'Direito explicado com menos friccao',
  'Fluxo pronto para duvidas, PDF e video',
  'Tema claro e escuro com persistencia local',
]

function readTheme() {
  if (typeof window === 'undefined') {
    return 'light'
  }

  return window.localStorage.getItem('theme') === 'dark' ? 'dark' : 'light'
}

function mergeData(appData) {
  return {
    ...defaultData,
    ...appData,
    links: {
      ...defaultData.links,
      ...(appData?.links ?? {}),
    },
    navLinks: appData?.navLinks?.length ? appData.navLinks : defaultData.navLinks,
    heroActions: appData?.heroActions?.length ? appData.heroActions : defaultData.heroActions,
    showcasePrompts: appData?.showcasePrompts?.length
      ? appData.showcasePrompts
      : defaultData.showcasePrompts,
  }
}

function ActionLink({ action }) {
  return (
    <a
      className={`action-link ${action.variant === 'secondary' ? 'secondary' : 'primary'}`}
      href={action.href}
    >
      <i className={action.icon} aria-hidden="true"></i>
      <span>{action.label}</span>
    </a>
  )
}

function PromptCard({ prompt, compact = false }) {
  return (
    <a className={`prompt-card${compact ? ' compact' : ''}`} href={prompt.href}>
      <span className="prompt-icon" aria-hidden="true">
        <i className={prompt.icon}></i>
      </span>
      <span className="prompt-copy">
        <strong>{prompt.title}</strong>
        <span>{prompt.text}</span>
      </span>
      <i className="bi bi-arrow-up-right-circle prompt-arrow" aria-hidden="true"></i>
    </a>
  )
}

function App() {
  const [theme, setTheme] = useState(readTheme)
  const data = mergeData(window.LEGISLA_HOME)

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme)
    window.localStorage.setItem('theme', theme)
  }, [theme])

  return (
    <div className="app-shell">
      <header className="site-header">
        <div className="nav-shell">
          <a className="nav-brand" href={data.navLinks[0]?.href ?? '#'}>
            <img className="nav-brand-logo" src={data.logoSrc} alt="" />
            <span>{data.brand}</span>
          </a>

          <nav className="nav-list" aria-label="Principal">
            {data.navLinks.map((link) => (
              <a
                key={`${link.label}-${link.href}`}
                className={`nav-link${link.cta ? ' nav-link-cta' : ''}`}
                href={link.href}
              >
                {link.label}
              </a>
            ))}
          </nav>

          <div className="theme-toggle" role="group" aria-label="Tema">
            <button
              type="button"
              className={theme === 'light' ? 'active' : ''}
              onClick={() => setTheme('light')}
            >
              Claro
            </button>
            <button
              type="button"
              className={theme === 'dark' ? 'active' : ''}
              onClick={() => setTheme('dark')}
            >
              Escuro
            </button>
          </div>
        </div>
      </header>

      <main className="page-content">
        <section className="hero-section">
          <div className="hero-copy">
            <span className="section-kicker">Educacao juridica acessivel</span>
            <h1>Entenda seus direitos com uma interface mais rapida e uma IA pronta para conversar.</h1>
            <p className="hero-text">
              A Legisla.IA foi reorganizada em React para deixar a navegacao mais fluida, sem perder o foco
              em orientacao juridica clara, pratica e facil de usar.
            </p>

            <div className="hero-actions">
              {data.heroActions.map((action) => (
                <ActionLink key={`${action.label}-${action.href}`} action={action} />
              ))}
            </div>

            <div className="value-pills" aria-label="Destaques da plataforma">
              {valuePillars.map((pillar) => (
                <span key={pillar} className="value-pill">
                  {pillar}
                </span>
              ))}
            </div>
          </div>

          <div className="hero-panel">
            <article className="hero-card assistant-card">
              <div className="card-label">
                <span className="status-dot"></span>
                <span>IA juridica ao vivo</span>
              </div>
              <h2>Comece por perguntas que ja fazem parte da rotina.</h2>
              <p>
                Abra o chat com um clique, use prompts prontos e avance para PDF ou video quando
                precisar de contexto adicional.
              </p>

              <div className="compact-prompts">
                {data.showcasePrompts.map((prompt) => (
                  <PromptCard key={prompt.title} prompt={prompt} compact />
                ))}
              </div>
            </article>

            <article className="hero-card insight-card">
              <span className="card-label muted-label">Fluxo de uso</span>
              <div className="insight-steps">
                <div>
                  <strong>1. Pergunte</strong>
                  <span>Use uma duvida objetiva do cotidiano.</span>
                </div>
                <div>
                  <strong>2. Aprofunde</strong>
                  <span>Anexe PDF ou envie um link quando precisar resumir material.</span>
                </div>
                <div>
                  <strong>3. Valide</strong>
                  <span>Leve a triagem inicial para uma analise juridica profissional.</span>
                </div>
              </div>

              <a className="text-link" href={data.links.chat}>
                Abrir o assistente
                <i className="bi bi-arrow-right-short" aria-hidden="true"></i>
              </a>
            </article>
          </div>
        </section>

        <section className="section-shell showcase-section">
          <div className="section-head">
            <span className="section-kicker">Experimente a IA</span>
            <h2 className="section-title">Prompts iniciais para destravar a conversa</h2>
            <p className="section-text">
              Cada cartao abre o chat com uma pergunta pronta para facilitar o primeiro contato.
            </p>
          </div>

          <div className="showcase-grid">
            {data.showcasePrompts.map((prompt) => (
              <PromptCard key={`${prompt.title}-full`} prompt={prompt} />
            ))}
          </div>
        </section>

        <section className="section-shell feature-section">
          <div className="section-head">
            <span className="section-kicker">O que voce pode fazer aqui</span>
            <h2 className="section-title">Uma base unica para tirar duvidas e acelerar leitura inicial</h2>
          </div>

          <div className="feature-grid">
            {featureCards.map((feature) => (
              <article key={feature.title} className="feature-card">
                <span className="feature-icon" aria-hidden="true">
                  <i className={feature.icon}></i>
                </span>
                <h3>{feature.title}</h3>
                <p>{feature.text}</p>
              </article>
            ))}
          </div>
        </section>

        <section className="section-shell audience-section">
          <div className="audience-copy">
            <span className="section-kicker">Para quem e a plataforma</span>
            <h2 className="section-title">Uma camada inicial de apoio para quem precisa entender o basico com rapidez</h2>
            <p className="section-text">
              A resposta da IA serve como ponto de partida. Quando o caso exige decisao ou defesa,
              a orientacao de um profissional continua sendo indispensavel.
            </p>

            <div className="audience-actions">
              <a className="action-link primary" href={data.links.chat}>
                <i className="bi bi-stars" aria-hidden="true"></i>
                <span>Ir para o chat</span>
              </a>
              {!data.isLoggedIn ? (
                <a className="action-link secondary" href={data.links.login}>
                  <i className="bi bi-box-arrow-in-right" aria-hidden="true"></i>
                  <span>Fazer login</span>
                </a>
              ) : null}
            </div>
          </div>

          <div className="audience-grid">
            {audienceCards.map((audience) => (
              <article key={audience.title} className="audience-card">
                <span className="feature-icon" aria-hidden="true">
                  <i className={audience.icon}></i>
                </span>
                <h3>{audience.title}</h3>
                <p>{audience.text}</p>
              </article>
            ))}
          </div>
        </section>
      </main>
    </div>
  )
}

export default App

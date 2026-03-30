import { Link } from 'react-router-dom'
import { useAuth } from '../lib/auth'

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

const showcasePrompts = [
  {
    title: 'Trabalho',
    text: 'Posso faltar ao trabalho com atestado?',
    q: 'Posso faltar ao trabalho com atestado?',
    icon: 'bi bi-briefcase-fill',
  },
  {
    title: 'Consumidor',
    text: 'Quais sao meus direitos em uma compra com defeito?',
    q: 'Quais sao meus direitos em uma compra com defeito?',
    icon: 'bi bi-bag-check-fill',
  },
  {
    title: 'Familia',
    text: 'Como funciona pensao alimenticia no Brasil?',
    q: 'Como funciona pensao alimenticia no Brasil?',
    icon: 'bi bi-people-fill',
  },
]

function PromptCard({ prompt, compact = false }) {
  return (
    <Link
      className={`prompt-card${compact ? ' compact' : ''}`}
      to={`/chat?q=${encodeURIComponent(prompt.q)}`}
    >
      <span className="prompt-icon" aria-hidden="true">
        <i className={prompt.icon}></i>
      </span>
      <span className="prompt-copy">
        <strong>{prompt.title}</strong>
        <span>{prompt.text}</span>
      </span>
      <i className="bi bi-arrow-up-right-circle prompt-arrow" aria-hidden="true"></i>
    </Link>
  )
}

export default function HomePage() {
  const { user, loading } = useAuth()
  const isLoggedIn = !loading && !!user

  return (
    <>
      <section className="hero-section">
        <div className="hero-copy">
          <span className="section-kicker">Educacao juridica acessivel</span>
          <h1>Entenda seus direitos com uma interface mais rapida e uma IA pronta para conversar.</h1>
          <p className="hero-text">
            A Legisla.IA foi reorganizada em React para deixar a navegacao mais fluida, sem perder o foco
            em orientacao juridica clara, pratica e facil de usar.
          </p>

          <div className="hero-actions">
            {isLoggedIn ? (
              <Link className="action-link primary" to="/chat">
                <i className="bi bi-stars" aria-hidden="true"></i>
                <span>Ir para o chat</span>
              </Link>
            ) : (
              <>
                <Link className="action-link primary" to="/cadastro">
                  <i className="bi bi-person-plus" aria-hidden="true"></i>
                  <span>Criar conta gratis</span>
                </Link>
                <Link className="action-link secondary" to="/login">
                  <i className="bi bi-box-arrow-in-right" aria-hidden="true"></i>
                  <span>Entrar</span>
                </Link>
              </>
            )}
          </div>

          <div className="value-pills" aria-label="Destaques da plataforma">
            {valuePillars.map((pillar) => (
              <span key={pillar} className="value-pill">{pillar}</span>
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
              {showcasePrompts.map((prompt) => (
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
            <Link className="text-link" to="/chat">
              Abrir o assistente
              <i className="bi bi-arrow-right-short" aria-hidden="true"></i>
            </Link>
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
          {showcasePrompts.map((prompt) => (
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
            <Link className="action-link primary" to="/chat">
              <i className="bi bi-stars" aria-hidden="true"></i>
              <span>Ir para o chat</span>
            </Link>
            {!isLoggedIn && (
              <Link className="action-link secondary" to="/login">
                <i className="bi bi-box-arrow-in-right" aria-hidden="true"></i>
                <span>Fazer login</span>
              </Link>
            )}
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
    </>
  )
}

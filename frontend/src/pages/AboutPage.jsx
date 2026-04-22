const team = [
  { name: 'Joao Miranda', role: 'Designer', img: '/imagens/Joao.png' },
  { name: 'Alan Nunes', role: 'Dev Full Stack', img: '/imagens/alan.jpeg' },
  { name: 'Bruno Deanin', role: 'Gerente de Projetos - Desenvolvedor Web', img: '/imagens/Bruno.png' },
  { name: 'Caio Bueno', role: 'Desenvolvedor BackEnd', img: '/imagens/Caio.jpeg' },
  { name: 'Ana Julia', role: 'Administrativo', img: '/imagens/anajulia.jpg' },
  { name: 'Kelven', role: 'Videomaker', img: '/imagens/kelven.jpg' },
  { name: 'Lara Botin', role: 'Auxiliar-Administrativo', img: '/imagens/lara.jpg' },
]

export default function AboutPage() {
  return (
    <section className="section-shell" style={{ textAlign: 'center' }}>
      <div className="section-head" style={{ marginBottom: 32 }}>
        <span className="section-kicker">Nossa equipe</span>
        <h2 className="section-title" style={{ maxWidth: 'none' }}>Conheca nossa equipe</h2>
      </div>

      <div
        style={{
          display: 'flex',
          flexWrap: 'wrap',
          gap: 24,
          justifyContent: 'center',
        }}
      >
        {team.map((member) => (
          <article
            key={member.name}
            className="feature-card"
            style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', textAlign: 'center', width: 200 }}
          >
            <img
              src={member.img}
              alt={member.name}
              style={{
                width: 120,
                height: 120,
                borderRadius: '50%',
                objectFit: 'cover',
                border: '3px solid var(--border-strong)',
              }}
            />
            <h3 style={{ margin: 0 }}>{member.name}</h3>
            <p style={{ margin: 0 }}>{member.role}</p>
          </article>
        ))}
      </div>
    </section>
  )
}

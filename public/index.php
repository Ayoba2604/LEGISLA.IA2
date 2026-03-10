<?php
session_start();
require_once "../routes/routesUsuarios.php";

$route = $_POST['route'] ?? $_GET['route'] ?? '';
$method = $_SERVER['REQUEST_METHOD'];

$shouldHandleRoute =
    ($method === 'POST' && in_array($route, ['consultas/login', 'consultas/cadastrar'], true)) ||
    ($method === 'GET' && in_array($route, ['consultas/logout', 'consultas/chat-token'], true));

if ($shouldHandleRoute) {
    handleRoute();
}
?>

<!DOCTYPE html>
<html lang="pt-br">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>Dashboard</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.css" rel="stylesheet">
  <link href="https://unpkg.com/boxicons@2.1.4/css/boxicons.min.css" rel="stylesheet" />
  <link rel="stylesheet" href="../assets/css/style.css" />
  <link rel="icon" href="/favicon.ico" type="image/x-icon">
  <link rel="shortcut icon" href="favicon.ico">
</head>
<body class="home-page">

<header class="site-header">
    <div class="nav-shell">
    <a class="nav-brand" href="index.php">Legisla.IA</a>
    <ul class="nav nav-list">
        <li class="nav-item">
            <a class="nav-link" href="index.php">Home</a>
        </li>
        <li class="nav-item">
            <a class="nav-link" href="../app/views/static/sobrenos.php">Sobre Nós</a>
        </li>

        <?php if (!empty($_SESSION['statusLogado']) && $_SESSION['statusLogado'] === true): ?>
            <?php if (!empty($_SESSION['admin']) && $_SESSION['admin'] === true): ?>
                <li class="nav-item">
                    <a class="nav-link" href="../app/views/auth/centralDeControle.php">Central de Controle</a>
                </li>
            <?php endif; ?>

            <li class="nav-item">
                <a class="nav-link nav-link-cta" href="index.php?route=consultas/logout">Sair</a>
            </li>
        <?php else: ?>
            <!-- <li class="nav-item">
                <a class="nav-link" href="../app/views/auth/formLogin.php">Entrar</a>
            </li>
            <li class="nav-item">
                <a class="nav-link" href="../app/views/auth/formCadastro.php">Cadastro</a>
            </li> -->
        <?php endif; ?>

        <li class="nav-item theme-nav-item">
            <details class="theme-details" id="theme-details">
                <summary class="nav-link theme-summary">
                    Tema <span class="chevron" aria-hidden="true">▾</span>
                </summary>
                <div class="theme-menu" id="theme-menu">
                    <button type="button" class="theme-option" data-theme="light">Claro</button>
                    <button type="button" class="theme-option" data-theme="dark">Escuro</button>
                </div>
            </details>
            <input type="checkbox" id="toggle-theme" hidden>
        </li>
    </ul>
    </div>
</header>

<!-- <main> 
    <div class="Introducao" >
        <h1>A melhor ferramenta de educação jurídica</h1>
        <p>
            Nossa ferramenta promete garantir tirar dúvidas, corrigir e informar pessoas de todas as idades, 
            disponibilizando dados de forma clara e sucinta, para que a nossa sociedade torne-se conhecedora de 
            seus direitos e deveres para assim termos um Brasil mais civilizado.
        </p>
    </div>

    <?php //if (!empty($_SESSION['statusLogado']) && $_SESSION['statusLogado'] === true && $_SESSION['admin'] === false): ?>
        <div style="margin-top:20px;">
            <a href="../app/views/static/ia_chat.html" class="btn btn-primary">Try on Legisla.IA</a>
        </div>
    <?php //endif; ?>
</main> -->

<main> 
    <!-- HERO -->
    <section class="hero">
        <div class="Introducao">
            <h1>A melhor ferramenta de educação jurídica</h1>
            <p>
                Nossa plataforma ajuda você a compreender seus direitos e deveres de forma clara,
                simples e acessível, promovendo uma sociedade mais consciente e justa.
            </p>

            <div class="hero-actions">
                <?php if (empty($_SESSION['statusLogado'])): ?>
                    <a href="../app/views/auth/formCadastro.php" class="btn primary">
                        <i class="bi bi-person-plus"></i> Criar conta grátis
                    </a>
                    <a href="../app/views/auth/formLogin.php" class="btn primary">
                        <i class="bi bi-box-arrow-in-right"></i> Entrar
                    </a>
                <?php else: ?>
                    <a href="../app/views/static/ia_chat.html" class="btn primary">
                        <i class="bi bi-chat-dots"></i> Tirar uma dúvida agora
                    </a>
                <?php endif; ?>
            </div>
        </div>
    </section>
    <!-- IA EM DESTAQUE -->
    <section class="ai-showcase">
        <div class="ai-showcase-head">
            <span class="ai-badge"><i class="bi bi-stars"></i> IA Juridica ao vivo</span>
            <h2>Converse com a Legisla.IA e receba orientacao em segundos</h2>
            <p>Pergunte sobre direitos, deveres e situacoes do dia a dia com linguagem simples.</p>
        </div>

        <div class="ai-showcase-grid">
            <a href="../app/views/static/ia_chat.html?q=Posso%20faltar%20ao%20trabalho%20com%20atestado%3F" class="ai-chip">
                <i class="bi bi-briefcase"></i> Trabalho
            </a>
            <a href="../app/views/static/ia_chat.html?q=Quais%20sao%20meus%20direitos%20como%20consumidor%3F" class="ai-chip">
                <i class="bi bi-receipt"></i> Consumidor
            </a>
            <a href="../app/views/static/ia_chat.html?q=Como%20funciona%20pensao%20alimenticia%3F" class="ai-chip">
                <i class="bi bi-people"></i> Familia
            </a>
        </div>

        <div class="ai-showcase-actions">
            <a href="../app/views/static/ia_chat.html" class="btn primary">
                <i class="bi bi-chat-dots-fill"></i> Abrir chat da IA
            </a>
        </div>
    </section>

    <!-- FUNCIONALIDADES -->
    <section class="features">
        <h2>O que você pode fazer aqui</h2>

        <div class="cards">
            <div class="card">
                <i class="bi bi-question-circle"></i>
                <h3>Tirar dúvidas</h3>
                <p>Respostas jurídicas diretas, sem juridiquês.</p>
            </div>

            <div class="card">
                <i class="bi bi-book"></i>
                <h3>Aprender seus direitos</h3>
                <p>Conteúdo educativo baseado na legislação brasileira.</p>
            </div>

            <div class="card">
                <i class="bi bi-cpu"></i>
                <h3>IA jurídica</h3>
                <p>Utilize inteligência artificial para aprender na prática.</p>
            </div>
        </div>
    </section>

    <!-- PÚBLICO -->
    <section class="publico">
        <h2>Para quem é a plataforma?</h2>

        <ul>
            <li><i class="bi bi-people"></i> Cidadãos em geral</li>
            <li><i class="bi bi-mortarboard"></i> Estudantes</li>
            <li><i class="bi bi-briefcase"></i> Iniciantes no Direito</li>
            <li><i class="bi bi-building"></i> Projetos educacionais</li>
        </ul>
    </section>
</main>

<script src="./JS/Storage.js"></script>
<script src="./JS/themeMenu.js"></script>
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>

</body>
</html>


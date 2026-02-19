<?php
session_start();
require_once "../routes/routesUsuarios.php";

$url = parse_url($_SERVER['REQUEST_URI'], PHP_URL_PATH);

if ($url !== '/index.php') { 
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
  <link rel="shortcut icon" href="/favicon.ico">
</head>
<body>

<header>
    <ul class="nav">
        <li class="nav-item">
            <a class="nav-link" href="index.php">Home</a>
        </li>

        <?php if (!empty($_SESSION['statusLogado']) && $_SESSION['statusLogado'] === true && !empty($_SESSION['admin']) && $_SESSION['admin'] === true): ?>
            <!-- Botões visíveis apenas para admin -->
            <li class="nav-item">
                <a class="nav-link" href="../app/views/auth/centralDeControle.php">Central de Controle</a>
            </li>
            <li class="nav-item">
                <a class="nav-link" href="index.php?route=consultas/logout">Sair</a>
            </li>

        <?php elseif (!empty($_SESSION['statusLogado']) && $_SESSION['statusLogado'] === true): ?>
            <!-- Botões visíveis apenas para usuários logados -->
            <li class="nav-item">
                <a class="nav-link" href="../app/views/auth/perfil.php">Perfil</a>
            </li>
            <li class="nav-item">
                <a class="nav-link" href="index.php?route=consultas/logout">Sair</a>
            </li>
            <li class="nav-item">
                <a class="nav-link" href="../app/views/static/teste.html">IA</a>
            </li>

        <?php else: ?>
            <!-- Botões para quem NÃO está logado -->
            <li class="nav-item">
                <a class="nav-link" href="../app/views/auth/formLogin.php">Login</a>
            </li>
            <li class="nav-item">
                <a class="nav-link" href="../app/views/auth/formCadastro.php">Cadastro</a>
            </li>
        <?php endif; ?>

        <li class="nav-item">
            <a class="nav-link" href="../app/views/static/sobrenos.php">Sobre Nós</a>
        </li>
    </ul>
</header>
    
<div class="theme-switch">
    <label class="mudar tema">
        <input type="checkbox" id="toggle-theme">
        <span class="slider"></span>
    </label>
</div>

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
            <a href="../app/views/static/teste.html" class="btn btn-primary">Try on Legisla.IA</a>
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
                    <a href="../app/views/static/teste.html" class="btn primary">
                        <i class="bi bi-chat-dots"></i> Tirar uma dúvida agora
                    </a>
                <?php endif; ?>
            </div>
        </div>
    </section>

    <!-- PERGUNTA -->
    <section class="question-box">
        <h2>Qual é sua dúvida jurídica?</h2>
        <p>Digite sua pergunta e receba uma explicação simples.</p>

        <form action="../app/views/static/teste.html" method="GET">
            <input 
                type="text" 
                placeholder="Ex: Posso faltar ao trabalho com atestado?"
                required
            >
            <button type="submit">
                <i class="bi bi-search"></i> Perguntar
            </button>
        </form>
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
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>

</body>
</html>

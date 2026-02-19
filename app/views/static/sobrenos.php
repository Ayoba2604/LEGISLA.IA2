<?php 
session_start();
?>
<!DOCTYPE html>
<html lang="pt-br">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>Cadastro</title>
  <link rel="stylesheet" href="../../assets/css/style_login.css" />
  <link href="https://unpkg.com/boxicons@2.1.4/css/boxicons.min.css" rel="stylesheet" />
  <link rel="stylesheet" href="../../../assets/css/style.css" />
</head>
<body>

<header>
    <ul class="nav">
        <li class="nav-item">
            <a class="nav-link" href="../../../public/index.php">Home</a>
        </li>

        <?php if (!empty($_SESSION['statusLogado']) && $_SESSION['statusLogado'] === true): ?>
            <!-- Botões visíveis só quando logado -->
            <?php if (!empty($_SESSION['admin']) && $_SESSION['admin'] === true): ?>
                <!-- Usuário admin -->
                <li class="nav-item">
                    <a class="nav-link" href="../usuario/adminDashboard.php">Central de Controle</a>
                </li>
            <?php else: ?>
                <!-- Usuário comum -->
                <li class="nav-item">
                    <a class="nav-link" href="../auth/perfil.php">Perfil</a>
                </li>
            <?php endif; ?>
            <li class="nav-item">
                <a class="nav-link" href="../../../public/index.php?route=consultas/logout">Sair</a>
            </li>
        <?php else: ?>
            <!-- Botões para quem NÃO está logado -->
            <li class="nav-item">
                <a class="nav-link" href="../auth/formLogin.php">Login</a>
            </li>
            <li class="nav-item">
                <a class="nav-link" href="../auth/formCadastro.php">Cadastro</a>
            </li>
            <li class="nav-item">
                <a class="nav-link" href="../static/teste.html">IA</a>
            </li>
        <?php endif; ?>

        <li class="nav-item">
            <a class="nav-link" href="sobrenos.php">Sobre Nós</a>
        </li>
    </ul>
</header>

    <div class="theme-switch">
        <label class="mudar tema">
            <input type="checkbox" id="toggle-theme">
            <span class="slider"></span>
        </label>
    </div>
</body>

<section class="sobre-nos">
        <h1 clas='nozes'>Conheça nossa equipe</h1>
        <div class="colaboradores">
            <div class="colaborador">
                <img src="../../../public/imagens/Joao.png" alt="Joao Miranda foto">
                <p>João Miranda - Designer Gráfico</p>
            </div>
            <div class="colaborador">
                <img src="../../../public/imagens/alan.jpeg" alt="Alan Nunes">
                <p>Alan Nunes - Desenvolvedor Full Stack</p>
            </div>
            <div class="colaborador">
                <img src="../../../public/imagens/Bruno.png" alt="Bruno Deanin">
                <p>Bruno Deanin - Gerente de Projetos - Desenvolvedor Web</p>
            </div>
            <div class="colaborador">
                <img src="../../../public/imagens/Caio.jpeg" alt="Caio Bueno">
                <p>Caio Bueno - Desenvolvedor BackEnd</p>
            </div>
        </div>
</section>

    <script src="../../../public/JS/Storage.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
</html>

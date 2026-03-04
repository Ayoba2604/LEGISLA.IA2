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

<?php
$currentView = 'sobrenos';
require_once __DIR__ . '/nav_view.php';
?>

    </body>

<section class="sobre-nos">
        <h1 clas='nozes'>ConheÃ§a nossa equipe</h1>
        <div class="colaboradores">
            <div class="colaborador">
                <img src="../../../public/imagens/Joao.png" alt="Joao Miranda foto">
                <p>JoÃ£o Miranda - Designer GrÃ¡fico</p>
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
    <script src="../../../public/JS/themeMenu.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
</html>


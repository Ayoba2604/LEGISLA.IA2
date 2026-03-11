










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
$currentView = 'cadastro';
require_once __DIR__ . '/../static/nav_view.php';
?>

</body>
  <div class="container">
    <div class="form-box login">
      <form method="POST" action="../../../public/index.php">

      <div class="teste"><h1>Cadastro</h1></div>
        

        <div class="input-box">
          <input type="hidden" name="route" value="consultas/cadastrar">
          <input type="text" name="nome" placeholder="Nome completo" required />
          <i class="bx bxs-user"></i>
        </div>

        <div class="input-box">
          <input type="email" name="email" placeholder="Email" required />
          <i class="bx bxs-envelope"></i>
        </div>

        <div class="input-box">
          <input type="password" name="senha" placeholder="Senha" required />
          <i class="bx bxs-lock-alt"></i>
        </div>

        <button type="submit" class="btn">Cadastrar</button>
      </form>
      
    </div>
  </div>

  


    <script src="../../../assets/css/style.css"></script>
    <script src="../../../public/JS/Storage.js"></script>
    <script src="../../../public/JS/themeMenu.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
</html>


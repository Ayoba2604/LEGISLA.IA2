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
        <li class="nav-item">
            <a class="nav-link" href="formLogin.php">Login</a>
        </li>
        <li class="nav-item">
            <a class="nav-link" href="formCadastro.php">Cadastro</a>
        </li>
        <li class="nav-item">
            <a class="nav-link" href="../static/teste.html">IA</a>
        </li>
        <li class="nav-item">
            <a class="nav-link" href="../static/sobrenos.php">Sobre Nós</a>
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

  <div class="container">
    <div class="form-box login">
      <form method="POST" action="../../../public/index.php">
        <h1>Login</h1>
        <?php if (isset($_GET['error']) && $_GET['error'] == 1): ?>
            <div class="error-message" style="color: red; margin-bottom: 10px; text-align: center;">
                Email ou senha inválidos
            </div>
        <?php endif; ?>

        <div class="input-box">
          <input type="hidden" name="route" value="consultas/login">
          <input type="text" name="email" placeholder="Nome de usuário" required />
          <i class="bx bxs-user"></i>
        </div>

        <div class="input-box">
          <input type="password" name="senha" placeholder="Senha" required />
          <i class="bx bxs-lock-alt"></i>
        </div>

        <div class="forgout-link">
          <a href="#">Esqueceu a senha?</a>
        </div>

        <button type="submit" class="btn">Login</button>
      </form>

      <!-- Switch do tema fora do form -->
        
    </div>
  </div>

    <script src="../../../assets/css/style.css"></script>
    <script src="../../../public/JS/Storage.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
</html>

  



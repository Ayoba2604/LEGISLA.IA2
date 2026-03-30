<!DOCTYPE html>
<html lang="pt-br">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>Login | Legisla.IA</title>
  <link rel="stylesheet" href="../../assets/css/style_login.css" />
  <link href="https://unpkg.com/boxicons@2.1.4/css/boxicons.min.css" rel="stylesheet" />
  <link rel="stylesheet" href="../../../assets/css/style.css" />
</head>
<body>

<?php
$currentView = 'login';
require_once __DIR__ . '/../static/nav_view.php';
?>

  <div class="container">
    <div class="form-box login">
      <form id="login-form">
        <h1>Login</h1>

        <div id="login-msg" class="form-msg" hidden></div>

        <div class="input-box">
          <input type="text" name="email" id="login-email" placeholder="Email" required />
          <i class="bx bxs-user"></i>
        </div>

        <div class="input-box">
          <input type="password" name="senha" id="login-senha" placeholder="Senha" required />
          <i class="bx bxs-lock-alt"></i>
        </div>

        <div class="forgout-link">
          <a href="#">Esqueceu a senha?</a>
        </div>

        <button type="submit" class="btn" id="login-btn">Login</button>
      </form>
    </div>
  </div>

  <script src="../../../public/JS/Storage.js"></script>
  <script src="../../../public/JS/themeMenu.js"></script>
  <script>
  (function() {
    const form = document.getElementById('login-form');
    const msg = document.getElementById('login-msg');
    const btn = document.getElementById('login-btn');
    const error = new URLSearchParams(window.location.search).get('error');

    function showMsg(text, isError) {
      msg.textContent = text;
      msg.className = 'form-msg ' + (isError ? 'msg-error' : 'msg-ok');
      msg.hidden = false;
    }

    if (error === 'admin') {
      showMsg('A dashboard e exclusiva para administradores. Entre com uma conta admin.', true);
    }

    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      msg.hidden = true;
      btn.disabled = true;
      btn.textContent = 'Entrando...';

      const email = document.getElementById('login-email').value.trim();
      const senha = document.getElementById('login-senha').value;

      try {
        const res = await fetch('../../../public/api_auth.php', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ action: 'login', email, senha })
        });

        const data = await res.json();

        if (data.ok) {
          showMsg('Login realizado! Redirecionando...', false);
          setTimeout(() => {
            window.location.href = data.admin
              ? '../../../public/index.php?route=admin/dashboard'
              : '../../../public/index.php';
          }, 600);
        } else {
          showMsg(data.erro || 'Email ou senha invalidos.', true);
          btn.disabled = false;
          btn.textContent = 'Login';
        }
      } catch (err) {
        showMsg('Erro de conexao. Tente novamente.', true);
        btn.disabled = false;
        btn.textContent = 'Login';
      }
    });
  })();
  </script>
</body>
</html>

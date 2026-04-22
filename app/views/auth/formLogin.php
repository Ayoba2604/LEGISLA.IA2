<!DOCTYPE html>
<html lang="pt-br">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>Login | Legisla.IA</title>
  <link rel="stylesheet" href="../../../assets/css/style.css" />
  <link rel="stylesheet" href="../../../assets/css/style_login.css" />
</head>
<body class="auth-screen">

<?php
$currentView = 'login';
require_once __DIR__ . '/../static/nav_view.php';
?>

  <main class="auth-page">
    <section class="auth-card" aria-labelledby="auth-title">
      <span class="auth-pill">Acesso a conta</span>
      <h1 class="auth-title" id="auth-title">Entrar na sua conta</h1>
      <p class="auth-lead">Use seu email para acessar a plataforma e deixe as outras formas de entrada prontas para os proximos passos.</p>

      <div class="auth-socials" aria-hidden="true">
        <button type="button" class="social-btn google" tabindex="-1">
          <img src="https://unpkg.com/devicon/icons/google/google-original.svg" alt="" loading="lazy" width="22" height="22" class="social-icon social-icon-google" />
          Continuar com Google
        </button>
        <button type="button" class="social-btn discord" tabindex="-1">
          <img src="https://cdn.jsdelivr.net/npm/simple-icons@16.7.0/icons/discord.svg" alt="" loading="lazy" width="22" height="22" class="social-icon social-icon-discord" />
          Continuar com Discord
        </button>
      </div>

      <div class="auth-divider"><span>Ou entre com email</span></div>

      <form id="login-form" class="auth-form">
        <div id="login-msg" class="form-msg" hidden></div>

        <label class="auth-field" for="login-email">
          <span>Email</span>
          <input type="email" name="email" id="login-email" placeholder="seu@email.com" autocomplete="email" required />
        </label>

        <label class="auth-field" for="login-senha">
          <span>Senha</span>
          <input type="password" name="senha" id="login-senha" placeholder="Sua senha" autocomplete="current-password" required />
        </label>

        <button type="submit" class="auth-submit" id="login-btn">Entrar</button>
      </form>

      <p class="auth-switch">Nao tem conta? <a href="./formCadastro.php">Criar conta</a></p>
    </section>
  </main>

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
          btn.textContent = 'Entrar';
        }
      } catch (err) {
        showMsg('Erro de conexao. Tente novamente.', true);
        btn.disabled = false;
        btn.textContent = 'Entrar';
      }
    });
  })();
  </script>
</body>
</html>

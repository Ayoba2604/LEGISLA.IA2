<!DOCTYPE html>
<html lang="pt-br">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>Cadastro | Legisla.IA</title>
  <link rel="stylesheet" href="../../../assets/css/style.css" />
  <link rel="stylesheet" href="../../../assets/css/style_login.css" />
</head>
<body class="auth-screen">

<?php
$currentView = 'cadastro';
require_once __DIR__ . '/../static/nav_view.php';
?>

  <main class="auth-page">
    <section class="auth-card" aria-labelledby="auth-title">
      <span class="auth-pill">Criacao de conta</span>
      <h1 class="auth-title" id="auth-title">Criar sua conta</h1>
      <p class="auth-lead">Comece pelo cadastro com email e deixe as outras formas de entrada prontas para o proximo passo.</p>

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

      <div class="auth-divider"><span>Ou cadastre com email</span></div>

      <form id="cadastro-form" class="auth-form">
        <div id="cadastro-msg" class="form-msg" hidden></div>

        <label class="auth-field" for="cadastro-nome">
          <span>Nome completo</span>
          <input type="text" name="nome" id="cadastro-nome" placeholder="Seu nome" autocomplete="name" required />
        </label>

        <label class="auth-field" for="cadastro-email">
          <span>Email</span>
          <input type="email" name="email" id="cadastro-email" placeholder="seu@email.com" autocomplete="email" required />
        </label>

        <label class="auth-field" for="cadastro-senha">
          <span>Senha</span>
          <input type="password" name="senha" id="cadastro-senha" placeholder="Minimo 6 caracteres" autocomplete="new-password" required />
        </label>

        <button type="submit" class="auth-submit" id="cadastro-btn">Cadastrar</button>
      </form>

      <p class="auth-switch">Ja tem conta? <a href="./formLogin.php">Fazer login</a></p>
    </section>
  </main>

  <script src="../../../public/JS/Storage.js"></script>
  <script src="../../../public/JS/themeMenu.js"></script>
  <script>
  (function() {
    const form = document.getElementById('cadastro-form');
    const msg = document.getElementById('cadastro-msg');
    const btn = document.getElementById('cadastro-btn');

    function showMsg(text, isError) {
      msg.textContent = text;
      msg.className = 'form-msg ' + (isError ? 'msg-error' : 'msg-ok');
      msg.hidden = false;
    }

    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      msg.hidden = true;
      btn.disabled = true;
      btn.textContent = 'Cadastrando...';

      const nome = document.getElementById('cadastro-nome').value.trim();
      const email = document.getElementById('cadastro-email').value.trim();
      const senha = document.getElementById('cadastro-senha').value;

      if (senha.length < 6) {
        showMsg('A senha deve ter pelo menos 6 caracteres.', true);
        btn.disabled = false;
        btn.textContent = 'Cadastrar';
        return;
      }

      try {
        const res = await fetch('../../../public/api_auth.php', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ action: 'cadastrar', nome, email, senha })
        });

        const data = await res.json();

        if (data.ok) {
          showMsg('Conta criada com sucesso! Redirecionando...', false);
          setTimeout(() => {
            window.location.href = '../../../public/index.php';
          }, 800);
        } else {
          showMsg(data.erro || 'Erro ao cadastrar.', true);
          btn.disabled = false;
          btn.textContent = 'Cadastrar';
        }
      } catch (err) {
        showMsg('Erro de conexao. Tente novamente.', true);
        btn.disabled = false;
        btn.textContent = 'Cadastrar';
      }
    });
  })();
  </script>
</body>
</html>

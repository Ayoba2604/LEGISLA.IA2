<!DOCTYPE html>
<html lang="pt-br">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>Cadastro | Legisla.IA</title>
  <link rel="stylesheet" href="../../assets/css/style_login.css" />
  <link href="https://unpkg.com/boxicons@2.1.4/css/boxicons.min.css" rel="stylesheet" />
  <link rel="stylesheet" href="../../../assets/css/style.css" />
</head>
<body>

<?php
$currentView = 'cadastro';
require_once __DIR__ . '/../static/nav_view.php';
?>

  <div class="container">
    <div class="form-box login">
      <form id="cadastro-form">
        <div class="teste"><h1>Cadastro</h1></div>

        <div id="cadastro-msg" class="form-msg" hidden></div>

        <div class="input-box">
          <input type="text" name="nome" id="cadastro-nome" placeholder="Nome completo" required />
          <i class="bx bxs-user"></i>
        </div>

        <div class="input-box">
          <input type="email" name="email" id="cadastro-email" placeholder="Email" required />
          <i class="bx bxs-envelope"></i>
        </div>

        <div class="input-box">
          <input type="password" name="senha" id="cadastro-senha" placeholder="Senha" required />
          <i class="bx bxs-lock-alt"></i>
        </div>

        <button type="submit" class="btn" id="cadastro-btn">Cadastrar</button>
      </form>
    </div>
  </div>

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

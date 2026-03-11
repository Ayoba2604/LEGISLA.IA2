<?php
if (session_status() === PHP_SESSION_NONE) {
    session_start();
}

$currentView = $currentView ?? '';

function renderNavItem(string $itemKey, string $currentView, string $href, string $label, string $extraClass = ''): void
{
    if ($itemKey === $currentView) {
        return;
    }

    $linkClass = trim('nav-link ' . $extraClass);
    echo '<li class="nav-item"><a class="' . $linkClass . '" href="' . $href . '">' . $label . '</a></li>';
}
?>
<header class="site-header">
    <div class="nav-shell">
    <a class="nav-brand" href="../../../public/index.php">Legisla.IA</a>
    <ul class="nav nav-list">
        <?php renderNavItem('home', $currentView, '../../../public/index.php', 'Home'); ?>

        <?php if (!empty($_SESSION['statusLogado']) && $_SESSION['statusLogado'] === true): ?>
            <?php if (!empty($_SESSION['admin']) && $_SESSION['admin'] === true): ?>
                <?php renderNavItem('central', $currentView, '../auth/centralDeControle.php', 'Central de Controle'); ?>
            <?php else: ?>
                <?php renderNavItem('perfil', $currentView, '../auth/perfil.php', 'Perfil'); ?>
            <?php endif; ?>

            <?php renderNavItem('ia', $currentView, '../static/ia_chat.html', 'IA'); ?>
            <?php renderNavItem('sobrenos', $currentView, '../static/sobrenos.php', 'Sobre Nos'); ?>
            <?php renderNavItem('logout', $currentView, '../../../public/index.php?route=consultas/logout', 'Sair', 'nav-link-cta'); ?>
        <?php else: ?>
            <?php renderNavItem('login', $currentView, '../auth/formLogin.php', 'Login'); ?>
            <?php renderNavItem('cadastro', $currentView, '../auth/formCadastro.php', 'Cadastro'); ?>
            <?php renderNavItem('sobrenos', $currentView, '../static/sobrenos.php', 'Sobre Nos'); ?>
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





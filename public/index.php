<?php
session_start();
require_once "../routes/routesUsuarios.php";
require_once "../routes/routesAdms.php";

$route = $_POST['route'] ?? $_GET['route'] ?? '';
$method = $_SERVER['REQUEST_METHOD'];

$shouldHandleRoute =
    ($method === 'POST' && in_array($route, ['consultas/login', 'consultas/cadastrar'], true)) ||
    ($method === 'GET' && in_array($route, ['consultas/logout', 'admin/dashboard'], true));

if ($shouldHandleRoute) {
    if ($route === 'admin/dashboard') {
        handleAdminRoute();
    } else {
        handleRoute();
    }
}

function renderReactHomeAssets(string $manifestPath, string $assetPrefix, string $entry = 'index.html'): bool
{
    if (!is_file($manifestPath)) {
        return false;
    }

    $manifestJson = file_get_contents($manifestPath);
    if ($manifestJson === false) {
        return false;
    }

    $manifest = json_decode($manifestJson, true);
    if (!is_array($manifest) || !isset($manifest[$entry]['file'])) {
        return false;
    }

    $entryChunk = $manifest[$entry];

    foreach ($entryChunk['css'] ?? [] as $cssFile) {
        $href = htmlspecialchars($assetPrefix . $cssFile, ENT_QUOTES, 'UTF-8');
        echo '<link rel="stylesheet" href="' . $href . '">' . PHP_EOL;
    }

    foreach ($entryChunk['imports'] ?? [] as $importName) {
        if (!isset($manifest[$importName]['file'])) {
            continue;
        }

        $href = htmlspecialchars($assetPrefix . $manifest[$importName]['file'], ENT_QUOTES, 'UTF-8');
        echo '<link rel="modulepreload" href="' . $href . '">' . PHP_EOL;
    }

    $src = htmlspecialchars($assetPrefix . $entryChunk['file'], ENT_QUOTES, 'UTF-8');
    echo '<script type="module" src="' . $src . '"></script>' . PHP_EOL;

    return true;
}

function buildPromptHref(string $baseHref, string $question): string
{
    return $baseHref . '?q=' . rawurlencode($question);
}

$isLoggedIn = !empty($_SESSION['statusLogado']) && $_SESSION['statusLogado'] === true;
$isAdmin = !empty($_SESSION['admin']);

$homeHref = 'index.php';
$aboutHref = '../app/views/static/sobrenos.php';
$loginHref = '../app/views/auth/formLogin.php';
$registerHref = '../app/views/auth/formCadastro.php';
$chatHref = '../app/views/static/ia_chat.html';
$controlHref = 'index.php?route=admin/dashboard';
$logoutHref = 'index.php?route=consultas/logout';

$navLinks = [
    ['href' => $homeHref, 'label' => 'Home'],
    ['href' => $aboutHref, 'label' => 'Sobre Nos'],
];

if ($isLoggedIn && $isAdmin) {
    $navLinks[] = ['href' => $controlHref, 'label' => 'Central de Controle'];
}

if ($isLoggedIn) {
    $navLinks[] = ['href' => $logoutHref, 'label' => 'Sair', 'cta' => true];
}

$heroActions = $isLoggedIn
    ? [
        [
            'href' => $chatHref,
            'label' => 'Tirar uma duvida agora',
            'icon' => 'bi bi-chat-dots-fill',
            'variant' => 'primary',
        ],
    ]
    : [
        [
            'href' => $registerHref,
            'label' => 'Criar conta gratis',
            'icon' => 'bi bi-person-plus',
            'variant' => 'primary',
        ],
        [
            'href' => $loginHref,
            'label' => 'Entrar',
            'icon' => 'bi bi-box-arrow-in-right',
            'variant' => 'secondary',
        ],
    ];

$appData = [
    'brand' => 'Legisla.IA',
    'logoSrc' => './favicon.svg',
    'isLoggedIn' => $isLoggedIn,
    'isAdmin' => $isAdmin,
    'navLinks' => $navLinks,
    'heroActions' => $heroActions,
    'links' => [
        'chat' => $chatHref,
        'login' => $loginHref,
        'register' => $registerHref,
    ],
    'showcasePrompts' => [
        [
            'title' => 'Trabalho',
            'text' => 'Posso faltar ao trabalho com atestado?',
            'href' => buildPromptHref($chatHref, 'Posso faltar ao trabalho com atestado?'),
            'icon' => 'bi bi-briefcase-fill',
        ],
        [
            'title' => 'Consumidor',
            'text' => 'Quais sao meus direitos em uma compra com defeito?',
            'href' => buildPromptHref($chatHref, 'Quais sao meus direitos em uma compra com defeito?'),
            'icon' => 'bi bi-bag-check-fill',
        ],
        [
            'title' => 'Familia',
            'text' => 'Como funciona pensao alimenticia no Brasil?',
            'href' => buildPromptHref($chatHref, 'Como funciona pensao alimenticia no Brasil?'),
            'icon' => 'bi bi-people-fill',
        ],
    ],
];

$encodedAppData = json_encode(
    $appData,
    JSON_UNESCAPED_UNICODE |
    JSON_UNESCAPED_SLASHES |
    JSON_HEX_TAG |
    JSON_HEX_APOS |
    JSON_HEX_QUOT |
    JSON_HEX_AMP
);

$manifestPath = __DIR__ . '/react-home/manifest.json';
$assetPrefix = './react-home/';
$hasReactBuild = is_file($manifestPath);
?>
<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Legisla.IA</title>
  <link rel="icon" href="./favicon.svg" type="image/svg+xml">
  <link rel="icon" href="./favicon-96x96.png" type="image/png" sizes="96x96">
  <link rel="icon" href="./favicon.ico" type="image/x-icon">
  <link rel="shortcut icon" href="./favicon.ico">
  <link rel="apple-touch-icon" sizes="180x180" href="./apple-touch-icon.png">
  <link rel="manifest" href="./site.webmanifest">
  <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.css" rel="stylesheet">
  <script>
    (function () {
      var savedTheme = localStorage.getItem('theme') || 'light';
      document.documentElement.setAttribute('data-theme', savedTheme === 'dark' ? 'dark' : 'light');
    })();
  </script>
  <script>
    window.LEGISLA_HOME = <?php echo $encodedAppData ?: '{}'; ?>;
  </script>
<?php if (!$hasReactBuild): ?>
  <style>
    body {
      margin: 0;
      min-height: 100vh;
      display: grid;
      place-items: center;
      font-family: Arial, sans-serif;
      background: #f4f7fb;
      color: #0f172a;
    }

    .build-notice {
      width: min(640px, calc(100% - 32px));
      padding: 32px;
      border-radius: 20px;
      background: #ffffff;
      box-shadow: 0 20px 40px rgba(15, 23, 42, 0.12);
    }

    .build-notice h1 {
      margin: 0 0 12px;
      font-size: 28px;
    }

    .build-notice p {
      margin: 0 0 12px;
      line-height: 1.6;
    }

    .build-notice code {
      display: inline-block;
      padding: 4px 8px;
      border-radius: 8px;
      background: #e2e8f0;
    }
  </style>
<?php endif; ?>
<?php renderReactHomeAssets($manifestPath, $assetPrefix); ?>
</head>
<body>
  <div id="root"></div>

<?php if (!$hasReactBuild): ?>
  <main class="build-notice">
    <h1>Build React ausente</h1>
    <p>A home foi preparada para carregar o bundle compilado do Vite, mas o manifesto ainda nao existe.</p>
    <p>Execute <code>npm install</code> e depois <code>npm run build</code> dentro de <code>frontend/</code>.</p>
  </main>
<?php endif; ?>
</body>
</html>

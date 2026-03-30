<?php
require_once __DIR__ . '/../../controllers/admsController.php';

if (session_status() === PHP_SESSION_NONE) {
    session_start();
}

$isLoggedIn = !empty($_SESSION['statusLogado']) && $_SESSION['statusLogado'] === true;
$isAdmin = !empty($_SESSION['admin']);

if (!$isLoggedIn) {
    header('Location: formLogin.php');
    exit;
}

if (!$isAdmin) {
    header('Location: ../../../public/index.php');
    exit;
}

$adminController = new AdminController();
$message = '';
$currentUserId = (int) ($_SESSION['id'] ?? 0);

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $action = $_POST['action'] ?? '';
    $userId = (int) ($_POST['id_usuario'] ?? 0);
    $result = false;

    if ($userId <= 0) {
        $message = 'Usuario invalido.';
    } elseif ($action === 'delete' && $userId === $currentUserId) {
        $message = 'Voce nao pode deletar sua propria conta admin enquanto estiver logado.';
    } elseif ($action === 'revoke_admin' && $userId === $currentUserId) {
        $message = 'Voce nao pode remover o proprio acesso de administrador.';
    } else {
        switch ($action) {
            case 'delete':
                $result = $adminController->deletarUsuario($userId);
                $message = $result ? 'Usuario deletado com sucesso.' : 'Erro ao deletar usuario.';
                break;

            case 'make_admin':
                $result = $adminController->tornarAdmin($userId);
                $message = $result ? 'Usuario promovido para admin.' : 'Erro ao tornar admin.';
                break;

            case 'revoke_admin':
                $result = $adminController->revogarAdmin($userId);
                $message = $result ? 'Privilegios de admin revogados.' : 'Erro ao revogar admin.';
                break;

            default:
                $message = 'Acao invalida.';
                break;
        }
    }

    $_SESSION['status_message'] = $message;
    header('Location: centralDeControle.php');
    exit;
}

$usuarios = $adminController->listarUsuarios();
$totalUsuarios = is_array($usuarios) ? count($usuarios) : 0;
$totalAdmins = 0;

foreach ($usuarios as $usuario) {
    if (!empty($usuario['admin'])) {
        $totalAdmins++;
    }
}

$totalComuns = $totalUsuarios - $totalAdmins;
$statusMessage = $_SESSION['status_message'] ?? '';
unset($_SESSION['status_message']);
?>
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dashboard Admin | Legisla.IA</title>
    <link rel="stylesheet" href="../../../assets/css/style.css">
    <style>
        body {
            margin: 0;
            min-height: 100vh;
            background:
                radial-gradient(circle at top left, rgba(13, 92, 99, 0.12), transparent 24%),
                radial-gradient(circle at top right, rgba(208, 183, 124, 0.22), transparent 18%),
                #f5efe4;
            color: #102542;
            font-family: "Segoe UI", Tahoma, Geneva, Verdana, sans-serif;
        }

        * {
            box-sizing: border-box;
        }

        .admin-layout {
            display: grid;
            grid-template-columns: 260px minmax(0, 1fr);
            gap: 22px;
            width: min(1320px, calc(100% - 32px));
            margin: 18px auto 32px;
        }

        .admin-sidebar,
        .admin-hero,
        .metric-card,
        .admin-panel {
            border: 1px solid rgba(16, 37, 66, 0.12);
            border-radius: 24px;
            background: rgba(255, 255, 255, 0.84);
            box-shadow: 0 24px 60px rgba(16, 37, 66, 0.12);
            backdrop-filter: blur(12px);
        }

        .admin-sidebar {
            position: sticky;
            top: 18px;
            align-self: start;
            padding: 22px;
        }

        .brand-box {
            display: grid;
            grid-template-columns: 56px 1fr;
            gap: 14px;
            align-items: center;
            margin-bottom: 22px;
        }

        .brand-mark,
        .avatar-badge {
            display: grid;
            place-items: center;
            width: 56px;
            height: 56px;
            border-radius: 18px;
            background: #d9f0ed;
            color: #0d5c63;
            font-weight: 800;
        }

        .brand-mark {
            font-size: 28px;
        }

        .brand-box strong,
        .admin-hero h1,
        .admin-panel h2,
        .metric-card strong {
            display: block;
            margin: 0;
            letter-spacing: -0.04em;
        }

        .brand-box span,
        .admin-hero p,
        .metric-card p,
        .panel-text,
        .table-user-copy span,
        .recent-item span {
            color: #475569;
            line-height: 1.6;
        }

        .sidebar-links {
            display: grid;
            gap: 8px;
            margin-bottom: 20px;
        }

        .sidebar-link {
            display: inline-flex;
            align-items: center;
            min-height: 46px;
            padding: 0 14px;
            border: 1px solid transparent;
            border-radius: 14px;
            color: #475569;
            font-weight: 700;
            text-decoration: none;
            transition: all 0.18s ease;
        }

        .sidebar-link:hover,
        .sidebar-link.active {
            color: #102542;
            border-color: rgba(16, 37, 66, 0.12);
            background: rgba(255, 255, 255, 0.56);
            transform: translateY(-1px);
        }

        .sidebar-card {
            padding: 18px;
            border: 1px solid rgba(16, 37, 66, 0.12);
            border-radius: 20px;
            background: #ffffff;
        }

        .chip,
        .profile-pill,
        .role-pill {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: fit-content;
            min-height: 34px;
            padding: 0 12px;
            border-radius: 999px;
            font-size: 12px;
            font-weight: 800;
        }

        .chip {
            background: #ebe4d6;
            color: #64748b;
            text-transform: uppercase;
            letter-spacing: 0.06em;
        }

        .profile-pill,
        .role-pill.admin {
            background: #d9f0ed;
            color: #0d5c63;
        }

        .admin-main {
            display: grid;
            gap: 18px;
        }

        .admin-hero {
            display: flex;
            justify-content: space-between;
            gap: 18px;
            align-items: flex-start;
            padding: 28px 30px;
            background:
                radial-gradient(circle at top right, rgba(13, 92, 99, 0.16), transparent 28%),
                radial-gradient(circle at bottom left, rgba(208, 183, 124, 0.16), transparent 20%),
                rgba(255, 255, 255, 0.9);
        }

        .hero-kicker {
            display: inline-flex;
            padding: 8px 12px;
            border-radius: 999px;
            background: #d9f0ed;
            color: #0d5c63;
            font-size: 13px;
            font-weight: 800;
            text-transform: uppercase;
            letter-spacing: 0.06em;
        }

        .admin-hero h1 {
            margin: 12px 0 8px;
            font-size: clamp(34px, 5vw, 54px);
            line-height: 0.96;
        }

        .hero-actions {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
        }

        .hero-button {
            display: inline-flex;
            align-items: center;
            min-height: 42px;
            padding: 0 14px;
            border: 1px solid rgba(13, 92, 99, 0.2);
            border-radius: 999px;
            background: #ffffff;
            color: #102542;
            font-weight: 700;
            text-decoration: none;
        }

        .status-message {
            padding: 14px 16px;
            border-radius: 16px;
            border: 1px solid rgba(13, 92, 99, 0.2);
            background: linear-gradient(90deg, rgba(13, 92, 99, 0.12), transparent), #ffffff;
            font-weight: 700;
        }

        .metrics-grid,
        .admin-summary {
            display: grid;
            gap: 16px;
        }

        .metrics-grid {
            grid-template-columns: repeat(4, minmax(0, 1fr));
        }

        .metric-card {
            display: grid;
            gap: 6px;
            padding: 22px;
        }

        .metric-card span {
            color: #64748b;
            font-size: 12px;
            font-weight: 800;
            text-transform: uppercase;
            letter-spacing: 0.08em;
        }

        .metric-card strong {
            font-size: 36px;
        }

        .metric-card p {
            margin: 0;
        }

        .admin-summary {
            grid-template-columns: minmax(0, 1.1fr) minmax(300px, 0.9fr);
        }

        .admin-panel {
            padding: 24px;
        }

        .panel-head {
            display: flex;
            justify-content: space-between;
            gap: 16px;
            align-items: flex-start;
            margin-bottom: 18px;
        }

        .panel-head h2 {
            margin: 10px 0 0;
            font-size: 28px;
        }

        .summary-list,
        .recent-list {
            display: grid;
            gap: 12px;
        }

        .summary-item,
        .recent-item {
            padding: 16px;
            border: 1px solid rgba(16, 37, 66, 0.12);
            border-radius: 16px;
            background: rgba(255, 255, 255, 0.58);
        }

        .summary-item strong,
        .recent-item strong {
            display: block;
            margin-bottom: 4px;
        }

        .recent-item {
            display: grid;
            grid-template-columns: 42px 1fr auto;
            gap: 12px;
            align-items: center;
        }

        .avatar-badge {
            width: 42px;
            height: 42px;
            border-radius: 14px;
            font-size: 14px;
        }

        .role-pill {
            background: #ebe4d6;
            color: #475569;
        }

        .table-wrap {
            overflow-x: auto;
            margin: 0 -24px -24px;
            padding: 0 24px 24px;
        }

        table {
            width: 100%;
            min-width: 860px;
            border-collapse: collapse;
        }

        th,
        td {
            padding: 16px 14px;
            text-align: left;
            border-bottom: 1px solid rgba(16, 37, 66, 0.12);
            vertical-align: middle;
        }

        th {
            color: #64748b;
            font-size: 12px;
            font-weight: 800;
            text-transform: uppercase;
            letter-spacing: 0.08em;
        }

        tbody tr:hover {
            background: rgba(255, 255, 255, 0.36);
        }

        .row-admin {
            background: linear-gradient(90deg, rgba(13, 92, 99, 0.08), transparent 58%);
        }

        .table-user {
            display: grid;
            grid-template-columns: 42px 1fr;
            gap: 12px;
            align-items: center;
        }

        .table-user .avatar-badge {
            width: 42px;
            height: 42px;
        }

        .table-user-copy {
            display: grid;
            gap: 4px;
        }

        .actions {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
        }

        .actions form {
            margin: 0;
        }

        .action-button {
            border: none;
            border-radius: 12px;
            padding: 10px 12px;
            color: #fff;
            cursor: pointer;
            font-weight: 700;
            transition: all 0.18s ease;
        }

        .action-button:hover:not(:disabled) {
            transform: translateY(-1px);
            box-shadow: 0 14px 24px rgba(16, 37, 66, 0.14);
        }

        .action-button:disabled {
            opacity: 0.45;
            cursor: not-allowed;
        }

        .btn-delete { background: #c44f4f; }
        .btn-promote { background: #1d8f6d; }
        .btn-revoke { background: #d7821b; }

        .empty-state {
            padding: 30px 16px;
            color: #475569;
            text-align: center;
        }

        @media (max-width: 1080px) {
            .admin-layout,
            .metrics-grid,
            .admin-summary {
                grid-template-columns: 1fr;
            }

            .admin-sidebar {
                position: static;
            }

            .admin-hero,
            .panel-head {
                display: grid;
            }
        }

        @media (max-width: 720px) {
            .admin-layout {
                width: min(100%, calc(100% - 12px));
                margin-top: 12px;
            }

            .admin-sidebar,
            .admin-hero,
            .admin-panel,
            .metric-card {
                padding: 18px;
            }

            .hero-actions,
            .actions,
            .recent-item {
                display: grid;
            }

            .hero-button,
            .action-button {
                width: 100%;
                justify-content: center;
            }
        }
    </style>
</head>
<body>
<main class="admin-layout">
    <aside class="admin-sidebar">
        <div class="brand-box">
            <div class="brand-mark">L</div>
            <div>
                <strong>Legisla.IA</strong>
                <span>Painel administrativo</span>
            </div>
        </div>

        <nav class="sidebar-links">
            <a class="sidebar-link active" href="#visao-geral">Visao geral</a>
            <a class="sidebar-link" href="#resumo">Resumo</a>
            <a class="sidebar-link" href="#usuarios">Usuarios</a>
            <a class="sidebar-link" href="../../../public/index.php">Voltar ao site</a>
        </nav>

        <section class="sidebar-card">
            <span class="chip">Conta atual</span>
            <h3><?php echo htmlspecialchars($_SESSION['usuario'] ?? 'Administrador'); ?></h3>
            <p class="panel-text">Acompanhe a base, revise permissoes e mantenha a area administrativa organizada a partir deste painel.</p>
            <span class="profile-pill">Modo admin ativo</span>
        </section>
    </aside>

    <div class="admin-main">
        <section class="admin-hero" id="visao-geral">
            <div>
                <span class="hero-kicker">Dashboard</span>
                <h1>Central de Controle</h1>
                <p>Layout reorganizado com inspiracao em dashboards Bootstrap, mas adaptado ao visual do Legisla.IA para leitura mais clara e uma sensacao mais profissional.</p>
            </div>
            <div class="hero-actions">
                <a class="hero-button" href="centralDeControle.php">Atualizar dados</a>
                <span class="hero-button"><?php echo htmlspecialchars($_SESSION['usuario'] ?? 'Administrador'); ?></span>
            </div>
        </section>

        <section class="metrics-grid">
            <article class="metric-card">
                <span>Usuarios totais</span>
                <strong><?php echo $totalUsuarios; ?></strong>
                <p>Base cadastrada no sistema.</p>
            </article>
            <article class="metric-card">
                <span>Admins ativos</span>
                <strong><?php echo $totalAdmins; ?></strong>
                <p>Contas com acesso ao painel.</p>
            </article>
            <article class="metric-card">
                <span>Usuarios comuns</span>
                <strong><?php echo $totalComuns; ?></strong>
                <p>Perfis sem permissao administrativa.</p>
            </article>
            <article class="metric-card">
                <span>Cobertura admin</span>
                <strong><?php echo $totalUsuarios > 0 ? (int) round(($totalAdmins / $totalUsuarios) * 100) : 0; ?>%</strong>
                <p>Percentual de admins na base.</p>
            </article>
        </section>

        <?php if ($statusMessage !== ''): ?>
            <div class="status-message"><?php echo htmlspecialchars($statusMessage); ?></div>
        <?php endif; ?>

        <section class="admin-summary" id="resumo">
            <article class="admin-panel">
                <div class="panel-head">
                    <div>
                        <span class="chip">Resumo operacional</span>
                        <h2>Leituras rapidas</h2>
                    </div>
                    <span class="chip">Painel ao vivo</span>
                </div>
                <div class="summary-list">
                    <div class="summary-item">
                        <strong>Gestao mais clara</strong>
                        <p class="panel-text">A estrutura separa visao geral, resumo e tabela para facilitar a analise do site.</p>
                    </div>
                    <div class="summary-item">
                        <strong>Controle mais seguro</strong>
                        <p class="panel-text">A propria conta logada continua protegida contra exclusao e perda acidental do acesso admin.</p>
                    </div>
                    <div class="summary-item">
                        <strong>Operacao centralizada</strong>
                        <p class="panel-text">Promova admins, revise perfis e remova contas a partir de uma unica tabela.</p>
                    </div>
                </div>
            </article>

            <article class="admin-panel">
                <div class="panel-head">
                    <div>
                        <span class="chip">Entradas recentes</span>
                        <h2>Ultimos usuarios</h2>
                    </div>
                </div>
                <div class="recent-list">
                    <?php foreach (array_slice(array_reverse($usuarios), 0, 4) as $usuario): ?>
                        <?php $usuarioEhAdmin = !empty($usuario['admin']); ?>
                        <div class="recent-item">
                            <div class="avatar-badge"><?php echo htmlspecialchars(strtoupper(substr($usuario['nome'], 0, 1))); ?></div>
                            <div>
                                <strong><?php echo htmlspecialchars($usuario['nome']); ?></strong>
                                <span><?php echo htmlspecialchars($usuario['email']); ?></span>
                            </div>
                            <span class="role-pill <?php echo $usuarioEhAdmin ? 'admin' : ''; ?>">
                                <?php echo $usuarioEhAdmin ? 'Admin' : 'Usuario'; ?>
                            </span>
                        </div>
                    <?php endforeach; ?>
                </div>
            </article>
        </section>

        <section class="admin-panel" id="usuarios">
            <div class="panel-head">
                <div>
                    <span class="chip">Diretorio</span>
                    <h2>Usuarios e permissoes</h2>
                    <p class="panel-text">Tabela principal para promover administradores, revisar perfis e remover acessos.</p>
                </div>
                <span class="chip"><?php echo $totalUsuarios; ?> registros</span>
            </div>

            <div class="table-wrap">
                <table>
                    <thead>
                        <tr>
                            <th>Usuario</th>
                            <th>ID</th>
                            <th>Email</th>
                            <th>Perfil</th>
                            <th>Acoes</th>
                        </tr>
                    </thead>
                    <tbody>
                        <?php if (!empty($usuarios)): ?>
                            <?php foreach ($usuarios as $usuario): ?>
                                <?php
                                $usuarioEhAdmin = !empty($usuario['admin']);
                                $isCurrentUser = (int) $usuario['id_usuario'] === $currentUserId;
                                ?>
                                <tr class="<?php echo $usuarioEhAdmin ? 'row-admin' : ''; ?>">
                                    <td>
                                        <div class="table-user">
                                            <div class="avatar-badge"><?php echo htmlspecialchars(strtoupper(substr($usuario['nome'], 0, 1))); ?></div>
                                            <div class="table-user-copy">
                                                <strong><?php echo htmlspecialchars($usuario['nome']); ?></strong>
                                                <span><?php echo $isCurrentUser ? 'Conta em uso nesta sessao' : 'Conta cadastrada no sistema'; ?></span>
                                            </div>
                                        </div>
                                    </td>
                                    <td>#<?php echo htmlspecialchars((string) $usuario['id_usuario']); ?></td>
                                    <td><?php echo htmlspecialchars($usuario['email']); ?></td>
                                    <td>
                                        <span class="role-pill <?php echo $usuarioEhAdmin ? 'admin' : ''; ?>">
                                            <?php echo $usuarioEhAdmin ? 'Administrador' : 'Usuario'; ?>
                                        </span>
                                    </td>
                                    <td>
                                        <div class="actions">
                                            <?php if (!$usuarioEhAdmin): ?>
                                                <form method="POST" action="centralDeControle.php" onsubmit="return confirm('Deseja tornar este usuario um administrador?');">
                                                    <input type="hidden" name="action" value="make_admin">
                                                    <input type="hidden" name="id_usuario" value="<?php echo (int) $usuario['id_usuario']; ?>">
                                                    <button type="submit" class="action-button btn-promote">Promover</button>
                                                </form>
                                            <?php endif; ?>

                                            <?php if ($usuarioEhAdmin): ?>
                                                <form method="POST" action="centralDeControle.php" onsubmit="return confirm('Deseja revogar o modo admin deste usuario?');">
                                                    <input type="hidden" name="action" value="revoke_admin">
                                                    <input type="hidden" name="id_usuario" value="<?php echo (int) $usuario['id_usuario']; ?>">
                                                    <button type="submit" class="action-button btn-revoke" <?php echo $isCurrentUser ? 'disabled' : ''; ?>>Revogar</button>
                                                </form>
                                            <?php endif; ?>

                                            <form method="POST" action="centralDeControle.php" onsubmit="return confirm('Deseja deletar este usuario?');">
                                                <input type="hidden" name="action" value="delete">
                                                <input type="hidden" name="id_usuario" value="<?php echo (int) $usuario['id_usuario']; ?>">
                                                <button type="submit" class="action-button btn-delete" <?php echo $isCurrentUser ? 'disabled' : ''; ?>>Excluir</button>
                                            </form>
                                        </div>
                                    </td>
                                </tr>
                            <?php endforeach; ?>
                        <?php else: ?>
                            <tr>
                                <td colspan="5" class="empty-state">Nenhum usuario encontrado no banco de dados.</td>
                            </tr>
                        <?php endif; ?>
                    </tbody>
                </table>
            </div>
        </section>
    </div>
</main>

<script src="../../../public/JS/Storage.js"></script>
<script src="../../../public/JS/themeMenu.js"></script>
</body>
</html>

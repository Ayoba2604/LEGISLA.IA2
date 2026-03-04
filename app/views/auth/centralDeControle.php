<?php
// 1. CORREÇÃO DE CAMINHOS: Assumindo que este arquivo está em views/auth/
// O caminho correto para subir dois níveis e entrar em controllers/models é '../controllers' e '../models' 
// se 'controllers' e 'models' são irmãos de 'views'.
// NO SEU CASO (app/views/auth): você precisa subir DOIS NÍVEIS (auth -> views -> app) e depois entrar em controllers.
// Se a estrutura é: /app/controllers, /app/models e este arquivo é /app/views/auth/centralDeControle.php
// Você deve usar:
require_once '../../controllers/admsController.php'; // Sobe (auth->views->app) e entra em 'controllers'
require_once '../../models/usuariosModel.php';      // Sobe (auth->views->app) e entra em 'models'

session_start();

// ===============================================
// 2. VERIFICAÇÃO DE ADMIN (CONTROLE DE ACESSO)
// ===============================================
if (!isset($_SESSION['admin']) || $_SESSION['admin'] !== true) 
{
    header("Location: formLogin.php"); 
    exit("Acesso negado. Você não tem permissões de administrador.");
}

// ===============================================
// 3. PROCESSAMENTO DE AÇÕES (CRUD)
// ===============================================

$adminController = new AdminController();
$message = '';

// Verifica se uma ação de CRUD foi solicitada via POST e se o ID foi enviado
if (isset($_POST['action']) && isset($_POST['id_usuario'])) 
{
    // CORREÇÃO: Pegando o ID da variável correta 'id_usuario' e convertendo para inteiro por segurança
    $userId = (int)$_POST['id_usuario'];
    $action = $_POST['action'];
    $result = false;

    // É altamente recomendado verificar se $userId > 0

    switch ($action) 
    {
        case 'delete':
            $result = $adminController->deletarUsuario($userId);
            $message = $result ? "Usuário ID: $userId deletado com sucesso." : "Erro ao deletar usuário.";
            break;
        case 'make_admin':
            $result = $adminController->tornarAdmin($userId);
            $message = $result ? "Usuário ID: $userId agora é administrador." : "Erro ao tornar admin.";
            break;
        case 'revoke_admin':
            $result = $adminController->revogarAdmin($userId);
            $message = $result ? "Privilégios de admin revogados para o ID: $userId." : "Erro ao revogar admin.";
            break;
        default:
            $message = "Ação inválida.";
    }
    
    // Redirecionamento (PRG Pattern)
    if (!empty($message)) 
    {
        $_SESSION['status_message'] = $message;
        header("Location: centralDeControle.php"); 
        exit;
    }
}

// ===============================================
// 4. LISTAGEM E MENSAGENS
// ===============================================

// Garante que o método listarUsuarios exista no seu Controller
$usuarios = $adminController->listarUsuarios();


$status_message = '';
if (isset($_SESSION['status_message'])) 
{
    $status_message = $_SESSION['status_message'];
    unset($_SESSION['status_message']);
}

?>

<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <title>Painel de Administração de Usuários</title>
    <link rel="stylesheet" href="../../assets/css/style.css"> 
    <style>
        .action-button { margin-right: 5px; padding: 5px 10px; cursor: pointer; border-radius: 3px; }
        table { width: 100%; border-collapse: collapse; margin-top: 20px; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        .admin { background-color: #fffacd; }
        .message { padding: 10px; margin-bottom: 15px; border: 1px solid #4CAF50; color: #4CAF50; background-color: #e6ffe6; }
    </style>
</head>
<body>

    <?php
$currentView = 'central';
require_once __DIR__ . '/../static/nav_view.php';
?>
    
    <?php if (!empty($status_message)): ?>
        <div class="message"><?php echo htmlspecialchars($status_message); ?></div>
    <?php endif; ?>

    <table>
        <thead>
            <tr>
                <th>ID</th>
                <th>Nome</th>
                <th>Email</th>
                <th>Admin</th>
                <th>Ações</th>
            </tr>
        </thead>
        <tbody>
            <?php if (!empty($usuarios)): ?>
                <?php foreach ($usuarios as $usuario): ?>
                    <tr class="<?php echo $usuario['admin'] ? 'admin' : ''; ?>">
                        <td><?php echo htmlspecialchars($usuario['id_usuario']); ?></td> 
                        <td><?php echo htmlspecialchars($usuario['nome']); ?></td>
                        <td><?php echo htmlspecialchars($usuario['email']); ?></td>
                        <td><?php echo $usuario['admin'] ? 'Sim' : 'Não'; ?></td>
                        <td>
                            <form method="POST" action="centralDeControle.php" style="display: inline;" onsubmit="return confirm('Tem certeza que deseja DELETAR o usuário: <?php echo htmlspecialchars($usuario['nome']); ?>?');">
                                <input type="hidden" name="action" value="delete">
                                <input type="hidden" name="id_usuario" value="<?php echo $usuario['id_usuario']; ?>"> 
                                
                                <button type="submit" class="action-button" style="background-color: #f44336; color: white; border: none;">
                                    Deletar
                                </button>
                            </form>
                            
                            <?php if ($usuario['admin']): ?>
                                <form method="POST" action="centralDeControle.php" style="display: inline;" onsubmit="return confirm('Tem certeza que deseja REVOGAR os privilégios de admin para: <?php echo htmlspecialchars($usuario['nome']); ?>?');">
                                    <input type="hidden" name="action" value="revoke_admin">
                                    <input type="hidden" name="id_usuario" value="<?php echo $usuario['id_usuario']; ?>">
                                    
                                    <button type="submit" class="action-button" style="background-color: #ff9800; color: white; border: none;">
                                        Revogar Admin
                                    </button>
                                </form>
                            <?php else: ?>
                                <form method="POST" action="centralDeControle.php" style="display: inline;" onsubmit="return confirm('Tem certeza que deseja TORNAR ADMIN o usuário: <?php echo htmlspecialchars($usuario['nome']); ?>?');">
                                    <input type="hidden" name="action" value="make_admin">
                                    <input type="hidden" name="id_usuario" value="<?php echo $usuario['id_usuario']; ?>">
                                    
                                    <button type="submit" class="action-button" style="background-color: #4CAF50; color: white; border: none;">
                                        Tornar Admin
                                    </button>
                                </form>
                            <?php endif; ?>
                        </td>
                    </tr>
                <?php endforeach; ?>
            <?php else: ?>
                <tr>
                    <td colspan="5">Nenhum usuário encontrado no banco de dados.</td>
                </tr>
            <?php endif; ?>
        </tbody>
    </table>

    <script src="../../../public/JS/Storage.js"></script>
    <script src="../../../public/JS/themeMenu.js"></script>
</body>
</html>

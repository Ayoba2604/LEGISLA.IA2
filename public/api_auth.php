<?php
session_start();
header('Content-Type: application/json; charset=UTF-8');

require_once __DIR__ . '/../app/controllers/usuariosController.php';

$method = $_SERVER['REQUEST_METHOD'];

if ($method === 'OPTIONS') {
    http_response_code(204);
    exit;
}

if ($method !== 'POST') {
    http_response_code(405);
    echo json_encode(['ok' => false, 'erro' => 'Metodo nao permitido']);
    exit;
}

$input = json_decode(file_get_contents('php://input'), true);
$action = $input['action'] ?? '';

$controller = new UsuarioController();

switch ($action) {
    case 'login':
        $email = trim($input['email'] ?? '');
        $senha = $input['senha'] ?? '';

        if (empty($email) || empty($senha)) {
            http_response_code(400);
            echo json_encode(['ok' => false, 'erro' => 'Email e senha sao obrigatorios.']);
            exit;
        }

        if ($controller->loginConta($email, $senha)) {
            echo json_encode([
                'ok' => true,
                'usuario' => $_SESSION['usuario'],
                'admin' => (bool) $_SESSION['admin'],
            ]);
        } else {
            http_response_code(401);
            echo json_encode(['ok' => false, 'erro' => 'Email ou senha invalidos.']);
        }
        break;

    case 'cadastrar':
        $nome  = trim($input['nome'] ?? '');
        $email = trim($input['email'] ?? '');
        $senha = $input['senha'] ?? '';

        if (empty($nome) || empty($email) || empty($senha)) {
            http_response_code(400);
            echo json_encode(['ok' => false, 'erro' => 'Todos os campos sao obrigatorios.']);
            exit;
        }

        if (!filter_var($email, FILTER_VALIDATE_EMAIL)) {
            http_response_code(400);
            echo json_encode(['ok' => false, 'erro' => 'Email invalido.']);
            exit;
        }

        $result = $controller->cadastrarConta($nome, $email, $senha);

        if ($result === true) {
            echo json_encode([
                'ok' => true,
                'usuario' => $_SESSION['usuario'],
                'admin' => (bool) $_SESSION['admin'],
            ]);
        } else {
            http_response_code(400);
            echo json_encode(['ok' => false, 'erro' => is_string($result) ? $result : 'Erro ao cadastrar.']);
        }
        break;

    case 'logout':
        $controller->logout();
        echo json_encode(['ok' => true]);
        break;

    case 'status':
        if (!empty($_SESSION['statusLogado']) && $_SESSION['statusLogado'] === true) {
            echo json_encode([
                'ok' => true,
                'logado' => true,
                'usuario' => $_SESSION['usuario'] ?? '',
                'admin' => (bool) ($_SESSION['admin'] ?? false),
            ]);
        } else {
            echo json_encode(['ok' => true, 'logado' => false]);
        }
        break;

    default:
        http_response_code(400);
        echo json_encode(['ok' => false, 'erro' => 'Acao invalida.']);
        break;
}

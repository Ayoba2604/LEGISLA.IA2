<?php
require_once __DIR__ . '/../models/usuariosModel.php';

class UsuarioController {

    protected $model;

    public function __construct() {
        // Prefer environment variables for DB credentials; fallback to hardcoded defaults.
        // You can set DB_DSN (full DSN) or DB_HOST/DB_NAME/DB_PORT and DB_USER/DB_PASS.
        $env_dsn = getenv('DB_DSN') ?: null;
        if (!$env_dsn && getenv('DB_HOST') && getenv('DB_NAME')) {
            $port = getenv('DB_PORT') ?: '5432';
            $env_dsn = sprintf('pgsql:host=%s;port=%s;dbname=%s;', getenv('DB_HOST'), $port, getenv('DB_NAME'));
        }

        $dsn = $env_dsn ?: "pgsql:host=localhost;port=5432;dbname=UsuariosLegislaIA;";
        $username = getenv('DB_USER') ?: 'postgres';
        $password = getenv('DB_PASS') ?: 'postgres';

        $this->model = new UsuarioModel($dsn, $username, $password);
    }

    // Cadastrar novo usuário
    public function cadastrarConta($nome, $email, $senha) 
    {
        // Validação básica
        if (empty($nome) || empty($email) || empty($senha)) {
            return "Todos os campos são obrigatórios!";
        }

        if (!filter_var($email, FILTER_VALIDATE_EMAIL)) {
            return "Por favor, insira um email válido!";
        }

        // Chama a model para criar usuário
        $sucesso = $this->model->criarUsuario($nome, $email, $senha);

        if ($sucesso) {
            // Busca o usuário recém-criado para preencher a sessão
            $usuario = $this->model->getUsuarioPorEmail($email); 
            if ($usuario) 
            {
                $_SESSION['statusLogado'] = true;
                $_SESSION['id'] = $usuario['id_usuario'];
                $_SESSION['usuario'] = $usuario['nome'];
                $_SESSION['email'] = $usuario['email'];
                $_SESSION['admin'] = $usuario['admin'];
            }
            return true;
        }
        else {
            return "Erro ao cadastrar usuário.";
        }
    }

    // Login
    public function loginConta($email, $senha) {
        if (empty($email) || empty($senha)) {
            return false; // falha
        }

        if ($login = $this->model->login($email, $senha)) {
            $_SESSION['id'] = $login['id_usuario'];
            $_SESSION['statusLogado'] = true;
            $_SESSION['usuario'] = $login['nome'];
            $_SESSION['email'] = $login['email'];
            $_SESSION['admin'] = $login['admin'];

            return true;
        }
        return false;
    }

    // Editar usuário
    public function editarConta($id, $nome, $email, $senha) {
        if (empty($nome) || empty($email) || empty($senha)) {
            return "Todos os campos são obrigatórios!";
        }

        return $this->model->atualizarUsuario($id, $nome, $email, $senha);
    }

    // Excluir usuário
    public function deletarConta($id) {
        return $this->model->deletarUsuario($id);
    }

    public function logout() {
        if (session_status() === PHP_SESSION_NONE) {
            session_start(); // só inicia se ainda não tiver sessão
        }

        session_unset();    // limpa variáveis
        session_destroy();  // destrói sessão
    }

}
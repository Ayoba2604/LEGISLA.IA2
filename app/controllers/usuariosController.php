<?php
require_once __DIR__ . '/_php/usuario_requests.php';

class UsuarioController {

    protected $model;

    public function __construct() {
        $this->model = legislaUsuarioModelFromEnv();
    }

    // Cadastrar novo usuario
    public function cadastrarConta($nome, $email, $senha)
    {
        if (empty($nome) || empty($email) || empty($senha)) {
            return 'Todos os campos sao obrigatorios!';
        }

        if (!filter_var($email, FILTER_VALIDATE_EMAIL)) {
            return 'Por favor, insira um email valido!';
        }

        $sucesso = $this->model->criarUsuario($nome, $email, $senha);

        if ($sucesso) {
            $usuario = $this->model->getUsuarioPorEmail($email);
            if ($usuario) {
                $_SESSION['statusLogado'] = true;
                $_SESSION['id'] = $usuario['id_usuario'];
                $_SESSION['usuario'] = $usuario['nome'];
                $_SESSION['email'] = $usuario['email'];
                $_SESSION['admin'] = $usuario['admin'];
            }
            return true;
        }

        return 'Erro ao cadastrar usuario.';
    }

    // Login
    public function loginConta($email, $senha) {
        if (empty($email) || empty($senha)) {
            return false;
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

    // Editar usuario
    public function editarConta($id, $nome, $email, $senha) {
        if (empty($nome) || empty($email) || empty($senha)) {
            return 'Todos os campos sao obrigatorios!';
        }

        return $this->model->atualizarUsuario($id, $nome, $email, $senha);
    }

    // Excluir usuario
    public function deletarConta($id) {
        return $this->model->deletarUsuario($id);
    }

    public function logout() {
        if (session_status() === PHP_SESSION_NONE) {
            session_start();
        }

        session_unset();
        session_destroy();
    }
}

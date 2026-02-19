<?php
require_once __DIR__ . '/../models/usuariosModel.php';

class AdminController {

    private $model;

    public function __construct() {
        // Conexão com o banco usando o model
        $dsn = "pgsql:host=localhost;port=5432;dbname=UsuariosLegislaIA;";
        $username = "postgres";
        $password = "postgres";

        $this->model = new UsuarioModel($dsn, $username, $password);
    }

    // Listar todos os usuários
    public function listarUsuarios() {
        return $this->model->listarUsuarios();
    }

    // Atualizar usuário (incluindo admin)

    // Deletar usuário
    public function deletarUsuario($id) {
        return $this->model->deletarUsuario($id);
    }

    // Tornar um usuário administrador
    public function tornarAdmin($id) {
        return $this->model->tornarAdmin($id);
    }

    // Revogar privilégios de administrador
    public function revogarAdmin($id) {
        return $this->model->revogarAdmin($id);
    }
}
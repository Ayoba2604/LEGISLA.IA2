<?php
require_once __DIR__ . '/_php/usuario_requests.php';

class AdminController {

    private $model;

    public function __construct() {
        $this->model = legislaUsuarioModelFromEnv();
    }

    // Listar todos os usuarios
    public function listarUsuarios() {
        return $this->model->listarUsuarios();
    }

    // Deletar usuario
    public function deletarUsuario($id) {
        return $this->model->deletarUsuario($id);
    }

    // Tornar um usuario administrador
    public function tornarAdmin($id) {
        return $this->model->tornarAdmin($id);
    }

    // Revogar privilegios de administrador
    public function revogarAdmin($id) {
        return $this->model->revogarAdmin($id);
    }
}

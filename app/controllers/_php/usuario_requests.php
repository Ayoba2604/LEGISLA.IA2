<?php
require_once __DIR__ . '/../../models/usuariosModel.php';
require_once __DIR__ . '/db_request.php';

if (!function_exists('legislaUsuarioModelFromEnv')) {
    function legislaUsuarioModelFromEnv(): UsuarioModel
    {
        $config = legislaBuildDbConfig();

        return new UsuarioModel(
            $config['dsn'],
            $config['user'],
            $config['pass']
        );
    }
}

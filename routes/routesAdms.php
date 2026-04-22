<?php

require_once __DIR__ . '/../app/controllers/admsController.php';

function handleAdminRoute()
{
    if (session_status() === PHP_SESSION_NONE) {
        session_start();
    }

    $method = $_SERVER['REQUEST_METHOD'];
    $route = $_POST['route'] ?? $_GET['route'] ?? '';
    $isAdmin = !empty($_SESSION['admin']);

    switch ($route) {
        case 'admin/dashboard':
            if ($method !== 'GET') {
                http_response_code(405);
                exit('Metodo nao permitido.');
            }

            if (!$isAdmin) {
                header('Location: ../app/views/auth/formLogin.php?error=admin');
                exit;
            }

            header('Location: ../app/views/auth/centralDeControle.php');
            exit;

        default:
            return 0;
    }
}

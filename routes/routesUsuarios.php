<?php

require_once "../app/controllers/usuariosController.php";

function handleRoute() 
{
    
    $method = $_SERVER['REQUEST_METHOD'];
    
    // Pegamos a rota do POST ou GET
    $route = $_POST['route'] ?? $_GET['route'] ?? '';

    switch ($route) 
    {
        case 'consultas/cadastrar':
            if ($method === 'POST') 
            {
                //echo "<pre>"; print_r($_POST); echo "</pre>"; // debug
                $nome = $_POST["nome"] ?? '';
                $email = $_POST['email'] ?? '';
                $senha = $_POST['senha'] ?? '';
                $controller = new UsuarioController();
                $controller->cadastrarConta($nome, $email, $senha);
            } 
            else
            {
                echo 'cadastro deu ruim';
            }
            break;

        case 'consultas/login':
            if ($method === 'POST') 
            {
                $email = $_POST['email'] ?? '';
                $senha = $_POST['senha'] ?? '';
                $controller = new UsuarioController();
                
                if ($controller->loginConta($email, $senha)) {
                    header("Location: ../public/index.php");
                    exit();
                } else {
                    header("Location: ../app/views/auth/formLogin.php?error=1");
                    exit();
                }
            }
            break;
        case 'consultas/logout':
            if ($method === 'GET') 
            {
                $controller = new UsuarioController();
                
                $controller->logout();
            }
            default:
            return 0;
            break;
    }
}


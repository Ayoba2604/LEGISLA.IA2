<?php
require_once 'Database.php';

class UsuarioModel extends Database {

    public function __construct($dsn, $username, $password) {
        parent::__construct($dsn, $username, $password);
    }
    //metodo de usuarios
    public function criarUsuario($nome, $email, $senha) {
    $sql = "INSERT INTO usuarios (nome, email, senha) 
            VALUES (:nome, :email, :senha)";
    $stmt = $this->conexao->prepare($sql);
    $stmt->bindValue(':nome', $nome, PDO::PARAM_STR);
    $stmt->bindValue(':email', $email, PDO::PARAM_STR);
    $stmt->bindValue(':senha', password_hash($senha, PASSWORD_BCRYPT),  PDO::PARAM_STR);

    return $stmt->execute(); // retorna true se inseriu, false se deu erro
}

    public function getUsuarioPorEmail($email) {
        $sql = "SELECT * FROM usuarios WHERE email = :email LIMIT 1";
        $stmt = $this->conexao->prepare($sql);
        $stmt->bindValue(':email', $email, PDO::PARAM_STR);
        $stmt->execute();
        return $stmt->fetch(PDO::FETCH_ASSOC);  
    }

    //metodo de usuarios
    public function login($email, $senha) {
       
        $sql = "SELECT * FROM usuarios WHERE email = :email LIMIT 1";
        $stmt = $this->conexao->prepare($sql);
        $stmt->bindValue(':email', $email, PDO::PARAM_STR);
        $stmt->execute();
        
        $usuario = $stmt->fetch(PDO::FETCH_ASSOC);

        if ($usuario && password_verify($senha, $usuario['senha'])) 
        {
            return $usuario;
        }

        return false;
    }

    //metodo de usuarios
    public function atualizarUsuario($id, $nome, $email, $senha = null) {
        $sql = "UPDATE usuarios SET nome = :nome, email = :email";
        if ($senha) $sql .= ", senha = :senha";
        $sql .= " WHERE id_usuario = :id";

        $stmt = $this->conexao->prepare($sql);
        $stmt->bindValue(':nome', $nome, PDO::PARAM_STR);
        $stmt->bindValue(':email', $email, PDO::PARAM_STR);
        if ($senha) $stmt->bindValue(':senha', password_hash($senha, PASSWORD_BCRYPT), PDO::PARAM_STR);
        $stmt->bindValue(':id', $id, PDO::PARAM_INT);

        return $stmt->execute();
    }

    //metodo de usuarios
    public function deletarUsuario($id) {
        $sql = "DELETE FROM usuarios WHERE id_usuario = :id";
        $stmt = $this->conexao->prepare($sql);
        $stmt->bindValue(':id', $id, PDO::PARAM_INT);
        return $stmt->execute();
    }

    //metodo de adms
    public function listarUsuarios() {
        $sql = "SELECT id_usuario, nome, email, admin FROM usuarios";
        $stmt = $this->conexao->prepare($sql);
        $stmt->execute();
        return $stmt->fetchAll();
    }

    //metodo de adms
    public function tornarAdmin($id) {
        $sql = "UPDATE usuarios SET admin = true WHERE id_usuario = :id";
        $stmt = $this->conexao->prepare($sql);
        $stmt->bindValue(':id', $id, PDO::PARAM_INT);
        return $stmt->execute();
    }

    //metodo de adms
    public function revogarAdmin($id) {
        $sql = "UPDATE usuarios SET admin = false WHERE id_usuario = :id";
        $stmt = $this->conexao->prepare($sql);
        $stmt->bindValue(':id', $id, PDO::PARAM_INT);
        return $stmt->execute();
    }
}
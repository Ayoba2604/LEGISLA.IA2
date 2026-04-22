<?php
class Database {
    protected $conexao;

    public function __construct($dsn, $username, $password) {
        try 
        {
            $this->conexao = new PDO($dsn, $username, $password, [
                PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
                PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC
            ]);
        } 
        catch (PDOException $e) 
        {
            die("Erro ao conectar ao banco: " . $e->getMessage());
        }
    }
}
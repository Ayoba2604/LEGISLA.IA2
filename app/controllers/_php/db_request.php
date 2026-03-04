<?php

if (!function_exists('legislaBuildDbConfig')) {
    function legislaBuildDbConfig(): array
    {
        $dsnFromEnv = getenv('DB_DSN') ?: '';
        $driver = strtolower(getenv('DB_DRIVER') ?: 'pgsql');

        if ($dsnFromEnv !== '') {
            $defaultUser = $driver === 'mysql' ? 'root' : 'postgres';
            return [
                'dsn' => $dsnFromEnv,
                'user' => getenv('DB_USER') ?: $defaultUser,
                'pass' => getenv('DB_PASS') ?: '',
            ];
        }

        $host = getenv('DB_HOST') ?: 'localhost';
        $name = getenv('DB_NAME') ?: 'UsuariosLegislaIA';

        if ($driver === 'mysql') {
            $port = getenv('DB_PORT') ?: '3306';
            $charset = getenv('DB_CHARSET') ?: 'utf8mb4';
            $dsn = sprintf('mysql:host=%s;port=%s;dbname=%s;charset=%s', $host, $port, $name, $charset);
            $user = getenv('DB_USER') ?: 'root';
            $pass = getenv('DB_PASS') ?: '';

            return [
                'dsn' => $dsn,
                'user' => $user,
                'pass' => $pass,
            ];
        }

        $port = getenv('DB_PORT') ?: '5432';
        $dsn = sprintf('pgsql:host=%s;port=%s;dbname=%s;', $host, $port, $name);
        $user = getenv('DB_USER') ?: 'postgres';
        $pass = getenv('DB_PASS') ?: 'postgres';

        return [
            'dsn' => $dsn,
            'user' => $user,
            'pass' => $pass,
        ];
    }
}

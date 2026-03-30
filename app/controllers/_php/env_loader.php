<?php

if (!function_exists('legislaLoadEnv')) {
    function legislaLoadEnv(): void
    {
        static $loaded = false;
        if ($loaded) {
            return;
        }

        $root = dirname(__DIR__, 3);
        foreach (['.env', '.env.local'] as $filename) {
            $path = $root . DIRECTORY_SEPARATOR . $filename;
            if (!is_file($path)) {
                continue;
            }

            $lines = file($path, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES);
            if ($lines === false) {
                continue;
            }

            foreach ($lines as $line) {
                $line = trim($line);
                if ($line === '' || strpos($line, '#') === 0 || strpos($line, '=') === false) {
                    continue;
                }

                [$name, $value] = explode('=', $line, 2);
                $name = trim($name);
                $value = trim($value);

                if ($name === '' || getenv($name) !== false) {
                    continue;
                }

                $value = trim($value, "\"'");
                putenv(sprintf('%s=%s', $name, $value));
                $_ENV[$name] = $value;
                $_SERVER[$name] = $value;
            }
        }

        $loaded = true;
    }
}

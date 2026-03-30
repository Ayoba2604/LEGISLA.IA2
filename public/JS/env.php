<?php
header('Content-Type: application/javascript; charset=UTF-8');

require_once __DIR__ . '/../../app/controllers/_php/env_loader.php';
legislaLoadEnv();

$appEnv = getenv('APP_ENV') ?: 'development';
$apiBaseUrl = getenv('LEGISLA_API_BASE_URL') ?: 'http://127.0.0.1:8000';
?>
window.LEGISLA_APP_ENV = <?php echo json_encode($appEnv, JSON_UNESCAPED_SLASHES | JSON_UNESCAPED_UNICODE); ?>;
window.LEGISLA_API_BASE_URL = <?php echo json_encode($apiBaseUrl, JSON_UNESCAPED_SLASHES | JSON_UNESCAPED_UNICODE); ?>;

<?php

function legislaBackendSecret(): string
{
    $secret = getenv('LEGISLA_INTERNAL_SECRET') ?: '';
    return trim($secret);
}

function legislaBase64UrlEncode(string $payload): string
{
    return rtrim(strtr(base64_encode($payload), '+/', '-_'), '=');
}

function legislaGenerateBackendUserToken(array $session, int $ttlSeconds = 900): string
{
    $secret = legislaBackendSecret();
    if ($secret === '') {
        throw new RuntimeException('LEGISLA_INTERNAL_SECRET nao configurado.');
    }

    $issuedAt = time();
    $payload = [
        'user_id' => (string)($session['id'] ?? ''),
        'email' => $session['email'] ?? null,
        'admin' => !empty($session['admin']),
        'session_id' => session_id(),
        'issued_at' => $issuedAt,
        'expires_at' => $issuedAt + $ttlSeconds,
    ];

    $encodedPayload = legislaBase64UrlEncode(json_encode($payload, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES));
    $signature = hash_hmac('sha256', $encodedPayload, $secret);
    return $encodedPayload . '.' . $signature;
}

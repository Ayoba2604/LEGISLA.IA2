from backend.app.security.tokens import AuthenticatedUser, TokenValidationError, create_user_token, decode_user_token


def test_user_token_roundtrip():
    user = AuthenticatedUser(
        user_id="42",
        email="teste@legisla.ai",
        admin=True,
        session_id="sessao-teste",
        issued_at=100,
        expires_at=200,
    )

    token = create_user_token(user, "segredo")
    decoded = decode_user_token(token, "segredo", now_ts=150)

    assert decoded.user_id == "42"
    assert decoded.email == "teste@legisla.ai"
    assert decoded.admin is True


def test_user_token_rejects_expired_token():
    user = AuthenticatedUser(
        user_id="42",
        email="teste@legisla.ai",
        admin=False,
        session_id="sessao-teste",
        issued_at=100,
        expires_at=101,
    )

    token = create_user_token(user, "segredo")

    try:
        decode_user_token(token, "segredo", now_ts=200)
    except TokenValidationError as exc:
        assert "expired" in str(exc).lower()
    else:  # pragma: no cover
        raise AssertionError("Token expirado deveria falhar.")

from datetime import timedelta
import pytest

from app.core.exceptions import AuthenticationException
from app.core.security import create_mock_access_token, verify_supabase_token


@pytest.mark.unit
def test_mock_token_generation_and_verification():
    """Verifica generación y validación de tokens compatibles con Supabase Auth."""
    sub_id = "11111111-1111-1111-1111-111111111111"
    token = create_mock_access_token(sub=sub_id, email="evaluador@lingua.neurotech.org")
    assert isinstance(token, str)

    payload = verify_supabase_token(token)
    assert payload["sub"] == sub_id
    assert payload["email"] == "evaluador@lingua.neurotech.org"


@pytest.mark.unit
def test_expired_token_raises_exception():
    """Verifica que un token expirado lance AuthenticationException."""
    sub_id = "11111111-1111-1111-1111-111111111111"
    # Token expirado hace 10 minutos
    token = create_mock_access_token(
        sub=sub_id,
        expires_delta=timedelta(minutes=-10),
    )
    with pytest.raises(AuthenticationException):
        verify_supabase_token(token)


@pytest.mark.unit
def test_invalid_token_string_raises_exception():
    """Verifica que un token malformado lance AuthenticationException."""
    with pytest.raises(AuthenticationException):
        verify_supabase_token("invalid.token.structure")

    with pytest.raises(AuthenticationException):
        verify_supabase_token("")

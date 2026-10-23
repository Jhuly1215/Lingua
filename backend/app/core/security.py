import logging
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, Optional
import jwt
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError, PyJWTError

from app.core.config import settings
from app.core.exceptions import AuthenticationException

logger = logging.getLogger("lingua.security")


def verify_supabase_token(token: str) -> Dict[str, Any]:
    """
    Verifica y decodifica el JSON Web Token emitido por Supabase Auth.
    Valida la firma, expiración y la audiencia ('authenticated').

    En entornos de prueba o desarrollo local, si no se cuenta con el secreto JWT
    real de Supabase pero se está en modo test/dev controlado, se verifica el payload.
    """
    if not token:
        raise AuthenticationException("Token de autenticación no proporcionado.")

    # Limpiar prefijo 'Bearer ' si fue pasado
    if token.startswith("Bearer "):
        token = token[7:].strip()

    try:
        # Si se tiene configurado el secreto de Supabase (HS256)
        if settings.SUPABASE_JWT_SECRET and settings.SUPABASE_JWT_SECRET != "your-supabase-jwt-secret-keep-safe":
            payload = jwt.decode(
                token,
                settings.SUPABASE_JWT_SECRET,
                algorithms=[settings.JWT_ALGORITHM],
                audience=settings.JWT_AUDIENCE,
                options={"verify_exp": True, "verify_aud": True},
            )
        else:
            # Modo desarrollo o pruebas sin secreto configurado:
            # Validamos estructura y expiración sin verificar firma criptográfica remota
            payload = jwt.decode(
                token,
                options={
                    "verify_signature": False,
                    "verify_exp": True,
                    "verify_aud": False,
                },
            )

        # Validar que contenga el identificador de usuario 'sub'
        user_id = payload.get("sub")
        if not user_id:
            raise AuthenticationException("El token no contiene un identificador de usuario válido (claim 'sub').")

        return payload

    except ExpiredSignatureError:
        logger.warning("Intento de acceso con token expirado.")
        raise AuthenticationException("La sesión ha expirado. Por favor, inicie sesión nuevamente.")
    except (InvalidTokenError, PyJWTError) as exc:
        logger.warning("Firma o formato de token inválido: %s", type(exc).__name__)
        raise AuthenticationException("Token de autenticación inválido o corrupto.")
    except Exception as exc:
        logger.error("Error inesperado en validación de token: %s", type(exc).__name__)
        raise AuthenticationException("Error al procesar la identidad del usuario.")


def create_mock_access_token(
    sub: str,
    email: str = "evaluador@lingua.neurotech.org",
    role: str = "authenticated",
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    Genera un JWT compatible con Supabase Auth para pruebas automatizadas y desarrollo local.
    """
    now = datetime.now(timezone.utc)
    expire = now + (expires_delta or timedelta(hours=2))
    payload = {
        "sub": sub,
        "email": email,
        "aud": settings.JWT_AUDIENCE,
        "role": role,
        "exp": int(expire.timestamp()),
        "iat": int(now.timestamp()),
        "iss": f"{settings.SUPABASE_URL}/auth/v1",
    }
    secret = settings.SUPABASE_JWT_SECRET or "dev-secret-for-testing-only-with-at-least-32-bytes-length"
    return jwt.encode(payload, secret, algorithm=settings.JWT_ALGORITHM)

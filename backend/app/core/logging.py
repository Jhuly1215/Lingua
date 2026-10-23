import logging
import re
import sys
from typing import Any

# Patrones para sanitizar logs y proteger secretos/datos sensibles de salud
SENSITIVE_PATTERNS = [
    (re.compile(r"(Bearer\s+)[A-Za-z0-9\-._~+/]+=*", re.IGNORECASE), r"\1[MASKED_TOKEN]"),
    (re.compile(r"(password|secret|token|service_role_key|anon_key|jwt_secret)\s*[:=]\s*['\"]?([^'\"\s]+)['\"]?", re.IGNORECASE), r"\1=[MASKED]"),
    (re.compile(r"(postgresql(?:\+[a-z0-9]+)?://[^:]+:)([^@]+)(@)", re.IGNORECASE), r"\1*****\3"),
]


class SanitizedFormatter(logging.Formatter):
    """
    Formateador de logs que enmascara automáticamente información sensible:
    - Tokens Bearer y JWT
    - Claves y secretos de API
    - Contraseñas en cadenas de conexión
    """

    def format(self, record: logging.LogRecord) -> str:
        original = super().format(record)
        sanitized = original
        for pattern, replacement in SENSITIVE_PATTERNS:
            sanitized = pattern.sub(replacement, sanitized)
        return sanitized


def setup_logging(log_level: str = "INFO") -> logging.Logger:
    """Configura el logging centralizado de la aplicación."""
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)

    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)

    # Evitar duplicar handlers en reinicios de uvicorn
    if not root_logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = SanitizedFormatter(
            fmt="%(asctime)s [%(levelname)s] [%(name)s]: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        root_logger.addHandler(handler)
    else:
        for handler in root_logger.handlers:
            handler.setFormatter(
                SanitizedFormatter(
                    fmt="%(asctime)s [%(levelname)s] [%(name)s]: %(message)s",
                    datefmt="%Y-%m-%d %H:%M:%S",
                )
            )

    # Configurar nivel para loggers de librerías
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

    logger = logging.getLogger("lingua")
    logger.setLevel(numeric_level)
    return logger

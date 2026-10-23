from typing import Any, Optional
from fastapi import HTTPException, status


class AppException(HTTPException):
    """Excepción base para todos los errores de la aplicación LINGUA."""

    def __init__(
        self,
        status_code: int,
        code: str,
        message: str,
        details: Optional[Any] = None,
    ):
        super().__init__(status_code=status_code, detail=message)
        self.code = code
        self.message = message
        self.details = details


class EntityNotFoundException(AppException):
    """Entidad no encontrada en el sistema (HTTP 404)."""

    def __init__(self, entity_name: str, identifier: Any):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            code="ENTITY_NOT_FOUND",
            message=f"{entity_name} con identificador '{identifier}' no fue encontrado(a).",
            details={"entity": entity_name, "identifier": str(identifier)},
        )


class EntityConflictException(AppException):
    """Conflicto con el estado actual o unicidad (HTTP 409)."""

    def __init__(self, message: str, details: Optional[Any] = None):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            code="ENTITY_CONFLICT",
            message=message,
            details=details,
        )


class ValidationException(AppException):
    """Fallo en las reglas de negocio o validación de dominio (HTTP 422)."""

    def __init__(self, message: str, details: Optional[Any] = None):
        status_code = getattr(status, "HTTP_422_UNPROCESSABLE_CONTENT", 422)
        super().__init__(
            status_code=status_code,
            code="BUSINESS_RULE_VIOLATION",
            message=message,
            details=details,
        )


class AuthenticationException(AppException):
    """Fallo en la autenticación con Supabase Auth (HTTP 401)."""

    def __init__(self, message: str = "Credenciales inválidas, ausentes o expiradas."):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code="UNAUTHENTICATED",
            message=message,
        )


class AuthorizationException(AppException):
    """Acceso denegado por falta de permisos o rol requerido (HTTP 403)."""

    def __init__(self, message: str = "No cuenta con los permisos necesarios para realizar esta acción."):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            code="PERMISSION_DENIED",
            message=message,
        )


class DatabaseConnectionException(AppException):
    """Fallo de conectividad con la base de datos PostgreSQL (HTTP 503)."""

    def __init__(self, message: str = "No se pudo establecer conexión con la base de datos."):
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            code="DATABASE_UNAVAILABLE",
            message=message,
        )

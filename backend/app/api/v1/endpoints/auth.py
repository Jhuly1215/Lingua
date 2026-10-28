from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field

from app.core.security import create_mock_access_token
from app.db.models.user import User
from app.dependencies.auth import get_current_user
from app.schemas.user import UserProfileResponse

router = APIRouter(tags=["Autenticación y Usuario"])


class DemoTokenResponse(BaseModel):
    access_token: str = Field(..., description="Token JWT Bearer generado para autenticarse")
    token_type: str = "bearer"
    role: str = Field("professional", description="Rol clínico asignado al usuario")
    user_email: str = Field("evaluador@lingua.neurotech.org", description="Correo del usuario demo")
    instructions: str = Field(
        ...,
        description="Instrucciones para autorizar Swagger UI",
    )


@router.post(
    "/demo-token",
    response_model=DemoTokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Generar token de acceso para demostración en Swagger UI",
    description=(
        "Genera un token JWT válido para el usuario clínico demo ('professional'). "
        "Permite desbloquear y probar interactivamente todos los endpoints de Swagger UI "
        "haciendo clic en el botón 'Authorize' (candado)."
    ),
)
async def generate_demo_token() -> DemoTokenResponse:
    """Genera token mock de evaluación para Swagger."""
    token = create_mock_access_token(
        sub="11111111-1111-1111-1111-111111111111",
        email="evaluador@lingua.neurotech.org",
    )
    return DemoTokenResponse(
        access_token=token,
        token_type="bearer",
        role="professional",
        user_email="evaluador@lingua.neurotech.org",
        instructions=(
            "1. Copia el valor de 'access_token'. "
            "2. Ve arriba a la derecha en Swagger y haz clic en el botón verde 'Authorize' (candado). "
            "3. Pega el token en el campo de texto y haz clic en 'Authorize'. "
            "¡Listo! Ahora todas las peticiones a endpoints clínicos estarán autenticadas."
        ),
    )


@router.get(
    "/me",
    response_model=UserProfileResponse,
    status_code=status.HTTP_200_OK,
    summary="Obtener perfil del usuario autenticado",
    description="Retorna los datos clínicos, institución y rol asignado al token Bearer validado contra Supabase Auth.",
)
async def get_my_profile(
    current_user: User = Depends(get_current_user),
) -> UserProfileResponse:
    return UserProfileResponse.model_validate(current_user)

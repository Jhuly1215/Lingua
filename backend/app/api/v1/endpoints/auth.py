from fastapi import APIRouter, Depends, status
from app.db.models.user import User
from app.dependencies.auth import get_current_user
from app.schemas.user import UserProfileResponse

router = APIRouter(tags=["Autenticación y Usuario"])


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

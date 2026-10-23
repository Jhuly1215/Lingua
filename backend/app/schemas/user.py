import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class RoleResponse(BaseModel):
    """Información de un rol clínico del sistema."""
    role_id: uuid.UUID
    name: str
    description: Optional[str] = None
    active: bool

    model_config = ConfigDict(from_attributes=True)


class UserResponse(BaseModel):
    """Datos públicos y de perfil de un usuario clínico."""
    user_id: uuid.UUID
    role_id: uuid.UUID
    username: str
    email: EmailStr
    first_name: str
    last_name: str
    active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserProfileResponse(UserResponse):
    """Perfil detallado del usuario autenticado incluyendo su rol asignado."""
    role: Optional[RoleResponse] = None

    model_config = ConfigDict(from_attributes=True)

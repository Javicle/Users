from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr

from src.entities.user.entity import User
from src.infra.repository.db.models.user import UserDBModel


class UserBaseDTO(BaseModel):
    """Базовый класс для DTO пользователя"""

    model_config = ConfigDict(from_attributes=True)


class UserCreateDTO(UserBaseDTO):
    """DTO для создания пользователя"""

    login: str
    name: str
    password: str
    email: EmailStr


class UserUpdateDTO(UserBaseDTO):
    """DTO для обновления пользователя"""

    login: Optional[str] = None
    name: Optional[str] = None
    password: Optional[str] = None
    email: Optional[EmailStr] = None
    is_active: Optional[bool] = None


class UserResponseDTO(UserBaseDTO):
    """DTO для ответа с данными пользователя"""

    id: UUID | str
    login: str
    name: str
    email: EmailStr
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        exclude = {"password"}


class UserLoginDTO(UserBaseDTO):
    """DTO для входа пользователя"""

    login: Optional[str] = None
    email: Optional[EmailStr] = None
    password: str

    def model_post_init(self, _):
        if not self.login and not self.email:
            raise ValueError("Either login or email must be provided")


class UserPasswordChangeDTO(UserBaseDTO):
    """DTO для смены пароля"""

    old_password: str
    new_password: str


def to_user_response_dto(user_db: User | UserDBModel) -> UserResponseDTO:
    """
    Преобразование ORM модели в DTO ответа

    Args:
        user_db: ORM модель пользователя

    Returns:
        UserResponseDTO: DTO с данными пользователя
    """

    if isinstance(user_db, User):
        return UserResponseDTO(
            id=user_db.id,
            login=user_db.login,
            name=user_db.name,
            email=user_db.email,
            is_active=user_db.is_active,
            created_at=datetime.fromisoformat(user_db.created_at.isoformat()),
            updated_at=datetime.now(),
        )

    return UserResponseDTO.model_validate(user_db)

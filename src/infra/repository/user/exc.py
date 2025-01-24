from typing import Optional
from uuid import UUID

from fastapi import HTTPException

from src.entities.user.entity import User


class BaseUserHTTPException(HTTPException):
    def __init__(self, message: str | None = None):
        super().__init__(status_code=400, detail=message if message else "Ошибка валидации")


class AttributeAlreadyExists(HTTPException):
    def __init__(self, attribute: str, message: str | None = None):
        super().__init__(
            status_code=400, detail=message if message else f"{attribute} уже существует"
        )


class UserFoundHTTPException(HTTPException):
    def __init__(
        self,
        user: Optional[User] = None,
        message: str | None = None,
        user_id: Optional[str] = None,
        user_login: Optional[str] = None,
    ):

        detail = (
            message if message else f"Пользователь {user or user_id or user_login} уже существует."
        )
        super().__init__(status_code=400, detail=detail)


class UserNotFoundHTTPException(HTTPException):
    def __init__(
        self,
        user: Optional[User] = None,
        message: str | None = None,
        user_id: Optional[UUID | str] = None,
        user_login: Optional[str] = None,
    ):
        detail = (
            message if message else f"Пользователь {user or user_id or user_login} не существует."
        )
        super().__init__(status_code=400, detail=detail)

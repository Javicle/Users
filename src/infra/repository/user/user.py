from datetime import datetime
from typing import Optional, Sequence
from uuid import UUID

from fastapi import Depends
from sqlalchemy import delete, or_, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from tools_openverse.common.logger_ import setup_logger

from src.entities.user.dto import UserResponseDTO, UserUpdateDTO, to_user_response_dto
from src.entities.user.entity import User
from src.infra.repository.db.models.user import UserDBModel

from ..db.base import get_db
from .exc import (
    AttributeAlreadyExists,
    BaseUserHTTPException,
    UserNotFoundHTTPException,
)

logger = setup_logger("repository")


class UserRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(self, user: User) -> UserResponseDTO:
        logger.info("Добавление нового пользователя в базу данных: %s", user.login)
        stmt = insert(UserDBModel).values(
            id=user.id,
            login=user.login,
            name=user.name,
            email=user.email,
            password=user.password,
            created_at=user.created_at,
            updated_at=user.created_at,
        )

        await self._session.execute(stmt)
        await self._session.commit()
        logger.info("Пользователь %s успешно добавлен в базу данных", user.login)
        return to_user_response_dto(user)

    async def get_exists_user_db(self, user: User) -> bool:
        stmt = select(UserDBModel).filter(
            or_(UserDBModel.login == user.login, UserDBModel.email == user.email)
        )

        result = await self._session.execute(stmt)
        user_db = result.scalars().first()

        if user_db:
            if user.login == user_db.login:
                logger.error("Пользователь с таким логином: %s уже существует", user.login)
                raise AttributeAlreadyExists(attribute="Логин")
            if user.email == user_db.email:
                logger.error("Пользователь с таким email: %s уже существует", user.email)
                raise AttributeAlreadyExists(attribute="Email")

            return True

        return False

    async def find_user_by_id_or_login(
        self, user_id: Optional[UUID | str] = None, user_login: Optional[str] = None
    ) -> UserResponseDTO | None:
        logger.info("Поиск пользователя по ID %s или логину %s", user_id, user_login)
        if not user_login and not user_id:
            logger.error("Не указан ID пользователя или Логин для поиска")
            raise BaseUserHTTPException(message="Должен быть ID пользователя или Логин.")

        if user_id:
            if isinstance(user_id, str):
                user_id = UUID(user_id)
        stmt = select(UserDBModel)
        if user_id:
            stmt = stmt.where(UserDBModel.id == user_id)
        elif user_login:
            stmt = stmt.where(UserDBModel.login == user_login)

        result = await self._session.execute(stmt)
        db_user = result.scalar_one_or_none()

        if not db_user:
            logger.error("Пользователь не найден. ID: %s, Логин: %s", user_id, user_login)
            raise UserNotFoundHTTPException(user_id=user_id, user_login=user_login)

        logger.info("Пользователь найден: %s", db_user.login)
        return to_user_response_dto(db_user)

    async def update(self, user: UserUpdateDTO) -> UserResponseDTO:
        logger.info("Обновление данных пользователя: %s", user.login)
        if not any([user.login, user.password, user.name, user.email]):
            logger.error("Не переданы данные для обновления пользователя")
            raise BaseUserHTTPException(message="Не переданы данные для обновления.")

        stmt = (
            update(UserDBModel)
            .where(UserDBModel.login == user.login)
            .values(
                login=user.login,
                name=user.name,
                email=user.email,
                password=user.password,
                updated_at=datetime.now(),
            )
            .returning(UserDBModel)
        )

        result = await self._session.execute(stmt)
        db_user = result.scalar_one_or_none()

        if not db_user:
            logger.error("Пользователь с логином %s не найден для обновления", user.login)
            raise UserNotFoundHTTPException(user_id=None, user_login=user.login)

        logger.info("Данные пользователя %s успешно обновлены", user.login)
        return to_user_response_dto(db_user)

    async def delete(
        self, user_id: Optional[UUID] = None, user_login: Optional[str] = None
    ) -> None:
        logger.info("Удаление пользователя с ID: %s или логином: %s", user_id, user_login)
        if not user_login and not user_id:
            logger.error("Не указан ID пользователя или Логин для удаления")
            raise BaseUserHTTPException(
                message="Должен быть введен хотя бы ID пользователя либо Логин."
            )

        stmt = delete(UserDBModel).where(
            or_(UserDBModel.id == user_id, UserDBModel.login == user_login)
        )

        result = await self._session.execute(stmt)

        if result.rowcount == 0:
            logger.error(
                "Пользователь не найден для удаления. ID: %s, Логин: %s", user_id, user_login
            )
            raise UserNotFoundHTTPException(user_id=user_id, user_login=user_login)

        await self._session.commit()
        logger.info("Пользователь с ID: %s или логином: %s успешно удален", user_id, user_login)

    async def get_all_users(self) -> Sequence[UserDBModel]:
        logger.info("Получение всех пользователей из базы данных")
        stmt = select(UserDBModel)
        result = await self._session.execute(stmt)
        users = result.scalars().all()
        if users:
            logger.info("Получено %s пользователей", len(users))
            for user in users:
                print(user)
        return users


async def get_user_repository(
    session: AsyncSession = Depends(get_db),
) -> UserRepository:
    return UserRepository(session)

from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from fastapi import Depends
from tools_openverse.common.logger_ import setup_logger

from src.entities.user.dto import UserCreateDTO, UserResponseDTO, UserUpdateDTO
from src.entities.user.entity import User
from src.infra.repository.user.exc import UserNotFoundHTTPException
from src.infra.repository.user.user import UserRepository, get_user_repository

logger = setup_logger("service")


class UserService:
    def __init__(
        self,
        user_repository: UserRepository,
    ):
        self.user_repository = user_repository

    async def create_user(self, user_dto: UserCreateDTO) -> Optional[UserResponseDTO]:
        logger.info("Создание пользователя с логином: %s", user_dto.login)
        user = User(
            id=uuid4(),
            login=user_dto.login,
            name=user_dto.name,
            email=user_dto.email,
            password=user_dto.password,
            created_at=datetime.now(),
            is_active=True,
        )
        logger.info("Пользователь с данными: %s", user)
        try:
            is_exists = await self.user_repository.get_exists_user_db(user)
            if not is_exists:
                result = await self.user_repository.create(user)
                logger.info("Пользователь успешно создан: %s", result.login)
                return result
            return None
        except Exception as e:
            logger.error("Ошибка при создании пользователя %s: %s", user_dto.login, e)
            raise

    async def get_user_by_id_or_login(
        self, user_id: Optional[str | UUID] = None, user_login: Optional[str] = None
    ) -> Optional[UserResponseDTO]:
        logger.info("Получение пользователя по ID: %s или логину: %s", user_id, user_login)
        try:
            result = await self.user_repository.find_user_by_id_or_login(
                user_id=user_id, user_login=user_login
            )
            if result:
                logger.info("Пользователь найден: %s", result.login)
                return result
            return None
        except UserNotFoundHTTPException as e:
            logger.error("Пользователь не найден: %s", e)
            raise
        except Exception as e:
            logger.error("Ошибка при получении пользователя: %s", e)
            raise e

    async def update_user(self, user_dto: UserUpdateDTO) -> UserResponseDTO:
        logger.info("Обновление данных пользователя: %s", user_dto.login)
        try:
            result = await self.user_repository.update(user_dto)
            logger.info("Данные пользователя %s успешно обновлены", user_dto.login)
            return result
        except UserNotFoundHTTPException as e:
            logger.error(
                "Пользователь с логином %s не найден для обновления: %s", user_dto.login, e
            )
            raise
        except Exception as e:
            logger.error("Ошибка при обновлении данных пользователя %s: %s", user_dto.login, e)
            raise

    async def delete_user(
        self, user_id: Optional[UUID] = None, user_login: Optional[str] = None
    ) -> None:
        logger.info("Удаление пользователя с ID: %s или логином: %s", user_id, user_login)
        try:
            await self.user_repository.delete(user_id=user_id, user_login=user_login)
            logger.info("Пользователь с ID: %s или логином: %s успешно удален", user_id, user_login)
        except UserNotFoundHTTPException as e:
            logger.error(
                "Ошибка удаления пользователя. ID: %s, Логин: %s: %s", user_id, user_login, e
            )
            raise
        except Exception as e:
            logger.error("Неизвестная ошибка при удалении пользователя: %s", e)
            raise

    async def deactivate_user(self, user_id: UUID) -> UserResponseDTO | None:
        logger.info("Деактивация пользователя с ID: %s", user_id)
        try:
            user = await self.get_user_by_id_or_login(user_id=user_id)
            if user:
                updated_user_dto = UserUpdateDTO(
                    login=user.login,
                    name=user.name,
                    email=user.email,
                    is_active=False,
                )
                result = await self.update_user(updated_user_dto)
                logger.info("Пользователь с ID: %s успешно деактивирован", user_id)
                return result
            return None
        except Exception as e:
            logger.error("Ошибка при деактивации пользователя с ID: %s: %s", user_id, e)
            raise

    async def activate_user(self, user_id: UUID) -> UserResponseDTO | None:
        logger.info("Активация пользователя с ID: %s", user_id)
        try:
            user = await self.get_user_by_id_or_login(user_id=user_id)
            if user:
                updated_user_dto = UserUpdateDTO(
                    login=user.login,
                    name=user.name,
                    email=user.email,
                    is_active=True,
                )
                result = await self.update_user(updated_user_dto)
                logger.info("Пользователь с ID: %s успешно активирован", user_id)
                return result
            return None
        except Exception as e:
            logger.error("Ошибка при активации пользователя с ID: %s: %s", user_id, e)
            raise

    async def get_all_users(self) -> list[UserResponseDTO]:
        logger.info("Получение всех пользователей")
        try:
            result = await self.user_repository.get_all_users()
            response_dtos = [UserResponseDTO.model_validate(user) for user in result]
            logger.info("Все пользователи получены: %s", [user.login for user in response_dtos])
            return response_dtos
        except Exception as e:
            logger.error("Ошибка при получении всех пользователей: %s", e)
            raise


async def get_user_service(
    user_repository: UserRepository = Depends(get_user_repository),
) -> UserService:
    return UserService(user_repository)

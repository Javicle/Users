from typing import Annotated, Optional
from uuid import UUID

from fastapi import APIRouter, Depends
from tools_openverse.common.logger_ import setup_logger
from tools_openverse.common.models import LoginOAuth2PasswordRequestForm

from src.entities.user.dto import UserCreateDTO, UserResponseDTO, UserUpdateDTO
from src.infra.repository.user.exc import UserNotFoundHTTPException
from src.usecases.user import UserService, get_user_service

get_user_service_dep = Annotated[UserService, Depends(get_user_service)]

logger = setup_logger("route")


form_data_depends = Annotated[LoginOAuth2PasswordRequestForm, Depends(
    LoginOAuth2PasswordRequestForm.as_form
)]


class UserRoute:
    def __init__(self, router: APIRouter):
        self.router = router
        self.setup_routes()

    def setup_routes(self) -> None:
        self.router.add_api_route(
            "/users/create",
            self.create_user,
            methods=["POST"],
            response_model=UserResponseDTO,
            summary="Create new user",
            status_code=201,
        )
        self.router.add_api_route(
            "/users/get/{user_id}",
            self.get_user_by_id,
            methods=["GET"],
            response_model=UserResponseDTO,
            summary="Get user by ID",
        )
        self.router.add_api_route(
            "/users/login/{user_login}",
            self.get_user_by_login,
            methods=["GET"],
            response_model=UserResponseDTO,
            summary="Get user by login",
        )
        self.router.add_api_route(
            "/users/update",
            self.update_user,
            methods=["PUT"],
            response_model=UserResponseDTO,
            summary="Update user data",
        )
        self.router.add_api_route(
            "/users/get_all",
            self.get_all_users,
            methods=["GET"],
            summary="Get all users",
        )

        self.router.add_api_route(
            "/users/delete/{user_id}",
            self.delete_user_by_id,
            methods=["DELETE"],
            summary="Delete user by ID",
        )
        self.router.add_api_route(
            "/users/delete/login/{user_login}",
            self.delete_user_by_login,
            methods=["DELETE"],
            summary="Delete user by login",
        )
        self.router.add_api_route(
            "/health",
            self.health_check,
            methods=["GET"],
            summary="Health check",
        )

        self.router.add_api_route(
            "/users/log_in",
            self.log_in_user,
            methods=["POST"],
            response_model=UserResponseDTO,
            summary="Get User with login and password",
        )

    async def create_user(
        self,
        user_dto: UserCreateDTO,
        user_service: get_user_service_dep,
    ) -> Optional[UserResponseDTO]:
        logger.info("Request to create user with login: %s", user_dto.login)
        try:
            result_user = await user_service.create_user(user_dto)
        except Exception as exc:
            logger.error("Error creating user: %s", str(exc))
            raise

        if result_user:
            logger.info("User successfully created: %s", result_user)
            return result_user
        return None

    async def get_user_by_id(
        self, user_id: UUID | str, user_service: get_user_service_dep
    ) -> UserResponseDTO:
        logger.info("Request to get user by ID: %s", user_id)
        try:
            result_user = await user_service.get_user_by_id_or_login(user_id=user_id)
        except Exception as exc:
            logger.error("Error getting user: %s", str(exc))
            raise
        if not result_user:
            raise UserNotFoundHTTPException(message=f"User with ID {user_id} not found")
        logger.info("User found: %s", result_user.login)
        return result_user

    async def get_user_by_login(
        self, user_login: str, user_service: get_user_service_dep
    ) -> Optional[UserResponseDTO]:
        logger.info("Request to get user by login: %s", user_login)
        try:
            result_user = await user_service.get_user_by_id_or_login(user_login=user_login)
            if result_user:
                logger.info("User found: %s", result_user.login)
                return result_user
            return None
        except UserNotFoundHTTPException as exc:
            logger.error("User with login %s not found: %s", user_login, exc)
            raise

    async def update_user(
        self, user_dto: UserUpdateDTO, user_service: get_user_service_dep
    ) -> UserResponseDTO:
        logger.info("Request to update user data: %s", user_dto.login)
        try:
            result_user = await user_service.update_user(user_dto)
            logger.info("User data for %s successfully updated", user_dto.login)
            return result_user
        except UserNotFoundHTTPException as exc:
            logger.error("Error updating user data %s: %s", user_dto.login, exc)
            raise

    async def delete_user_by_id(self, user_id: UUID, user_service: get_user_service_dep) -> None:
        logger.info("Request to delete user with ID: %s", user_id)
        try:
            await user_service.delete_user(user_id=user_id)
            logger.info("User with ID %s successfully deleted", user_id)
        except UserNotFoundHTTPException as e:
            logger.error("Error deleting user with ID %s: %s", user_id, e)
            raise

    async def delete_user_by_login(
        self, user_login: str, user_service: get_user_service_dep
    ) -> None:
        logger.info("Request to delete user with login: %s", user_login)
        try:
            await user_service.delete_user(user_login=user_login)
            logger.info("User with login %s successfully deleted", user_login)
        except UserNotFoundHTTPException:
            logger.error("User with login %s not found", user_login)
            raise

    async def log_in_user(
        self,
        user_service: get_user_service_dep,
        form_data: form_data_depends,
    ) -> UserResponseDTO | None:
        logger.info("Request to log in user with login: %s", form_data.login)
        try:
            result_log_in = await user_service.log_in(form_data)
            if result_log_in:
                logger.info("User logged in: %s", result_log_in.login)
                return result_log_in

            return None
        except Exception as exc:
            logger.error("Error logging in user: %s", str(exc))
            raise

    async def health_check(self) -> dict[str, str]:
        return {"status": "OK"}

    async def get_all_users(self, user_service: get_user_service_dep) -> list[UserResponseDTO]:
        logger.info("Request to get all users")
        try:
            result = await user_service.get_all_users()
            logger.info("All users retrieved: %s", [user.login for user in result])
            return result
        except Exception as e:
            logger.error("Error getting all users: %s", str(e))
            raise

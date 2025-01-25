from datetime import datetime
from uuid import UUID

from pydantic import EmailStr, Field, field_validator
from tools_openverse.common.abc.user import AbstractUser
from tools_openverse.common.logger_ import setup_logger

from src.entities.user.exc import (
    BaseHTTPValidationError,
    HTTPLengthException,
    HTTPNumberException,
    HTTPSamePassword,
    HTTPSymbolException,
)
from src.entities.user.value_objects.rules import ValidationRules

logger = setup_logger("user_entity")


class User(AbstractUser):
    id: UUID | str
    login: str
    name: str
    password: str
    email: EmailStr
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    def change_password(self, new_password: str) -> None:
        if self.password == new_password:
            raise HTTPSamePassword(detail="Новый пароль совпадает со старым")
        self.validate_password(new_password)
        self.password = new_password
        self.updated_at = datetime.now()
        logger.info(f"Пароль успешно изменен для пользователя {self.login}")

    @field_validator("login", mode="before")
    @classmethod
    def validate_login(cls, value: str) -> str:
        if len(value) < 6:
            logger.warning(f"Логин '{value}' слишком короткий: {len(value)} < 6")
            raise HTTPLengthException(validation_field="Логин", length=6)

        if any(symbol in value for symbol in ValidationRules.BANNED_SYMBOLS):
            logger.warning("Логин '{value}' содержит запрещенные символы")
            raise HTTPSymbolException(
                validation_field="Логин", symbol=ValidationRules.BANNED_SYMBOLS, must_have=False
            )

        return value

    @field_validator("name", mode="before")
    @classmethod
    def validate_name(cls, value: str) -> str:
        if len(value) < 3 or len(value) > 16:
            logger.warning(f"Недопустимая длина имени '{value}': {len(value)}")
            raise HTTPLengthException(validation_field="Имя", length=3, max_length=16)

        if any(symbol in value for symbol in ValidationRules.BANNED_SYMBOLS):
            logger.warning(f"Имя '{value}' содержит запрещенные символы")
            raise HTTPSymbolException("Имя", symbol=ValidationRules.BANNED_SYMBOLS, must_have=False)

        return value

    @field_validator("password", mode="before")
    @classmethod
    def validate_password(cls, value: str) -> str:
        if len(value) <= 6:
            logger.warning(f"Пароль слишком короткий: {len(value)} <= 6")
            raise HTTPLengthException("Password", 6)

        if not any(symbol in value for symbol in ValidationRules.BANNED_SYMBOLS):
            logger.warning("Пароль не содержит специальных символов")
            raise HTTPSymbolException("Password", ValidationRules.BANNED_SYMBOLS, True)

        if not any(number in value for number in ValidationRules.NUMBERS):
            logger.warning("Пароль не содержит цифр")
            raise HTTPNumberException(validation_field="Password", number=ValidationRules.NUMBERS)

        if not any(c.isupper() for c in value):
            logger.warning(f"Пароль '{value}' не содержит заглавных букв")
            raise BaseHTTPValidationError(
                validation_field="Password",
                message="Пароль должен содержать хотя бы один заглавный символ",
            )

        if not any(c.islower() for c in value):
            logger.warning(f"Пароль '{value}' не содержит строчных букв")
            raise BaseHTTPValidationError(
                validation_field="Password",
                message="В пароле должен быть хотябы один строчный символ",
            )

        return value

from typing import ClassVar, Set


class ValidationRules:
    BANNED_SYMBOLS: ClassVar[Set[str]] = {"!", "@", "#", "$", "%", "^", "&", "*"}
    NUMBERS: ClassVar[Set[str]] = set("123456789")

    MIN_LOGIN_LENGTH: ClassVar[int] = 6
    MIN_NAME_LENGTH: ClassVar[int] = 3
    MAX_NAME_LENGTH: ClassVar[int] = 16
    MIN_PASSWORD_LENGTH: ClassVar[int] = 6

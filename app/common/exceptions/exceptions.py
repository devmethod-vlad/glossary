class LoginError(Exception):
    """Ошибка авторизации"""

    pass


class NotFoundError(Exception):
    """Объект не найден"""

    pass


class AlreadyExistsError(Exception):
    """Ошибка наличествования"""

    pass


class ConflictError(Exception):
    """Конфликт запроса"""

    pass


class RequestError(Exception):
    """Ошибка запроса"""

    pass


class RequestTimeoutError(Exception):
    """Ошибка ожидания запроса"""

    pass


class RedisConnectionError(Exception):
    """Ошибка подключения к redis"""

    pass

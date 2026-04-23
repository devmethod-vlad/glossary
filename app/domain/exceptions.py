class DomainException(Exception):
    """Базовая ошибка предметной области"""

    pass


class GlossaryUpdateFromXlsxError(DomainException):
    """Ошибка обновления элементов глоссария"""

    pass


class GlossaryCreateError(DomainException):
    """Ошибка создания элементов глоссария"""

    pass

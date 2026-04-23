import abc

from app.common.uow.interfaces import BaseAbstractUnitOfWork
from app.domain.repositories.interfaces import IGlossaryElementRepository


class IUnitOfWork(BaseAbstractUnitOfWork, abc.ABC):
    """Интерфейс единицы работы."""

    glossary_element: IGlossaryElementRepository

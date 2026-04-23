from app.common.uow.base_uow import BaseUnitOfWork
from app.domain.repositories.glossary_element import GlossaryElementRepository
from app.infrastructure.unit_of_work.interfaces import IUnitOfWork


class UnitOfWork(BaseUnitOfWork, IUnitOfWork):
    """Единица работы"""

    async def __aenter__(self) -> None:
        """Инициализация сессии и репозиториев."""
        await super().__aenter__()
        self.glossary_element = GlossaryElementRepository(session=self.session)

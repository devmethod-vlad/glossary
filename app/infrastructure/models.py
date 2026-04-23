from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.common.database import Database
from app.settings.config import settings

db = Database(config=settings.database)


Base = db.Base


class GlossaryElement(Base):
    """Элемент глоссария"""

    __tablename__ = "glossary_element"
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    abbreviation: Mapped[str]
    term: Mapped[str]
    definition: Mapped[str]


db.prepare_tables()

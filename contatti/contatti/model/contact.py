__all__ = ["PhoneBook"]

from sqlalchemy import ForeignKey, Column
from sqlalchemy.types import Unicode, Integer

from contatti.model import DeclarativeBase, metadata, DBSession

class PhoneBook(DeclarativeBase):
    __tablename__ = "phonebook"

    id = Column(Integer, autoincrement=True, primary_key=True)
    id_user = Column(Integer, ForeignKey("tg_user.user_id"))
    name = Column(Unicode, nullable=False)
    number = Column(Unicode, nullable=False)
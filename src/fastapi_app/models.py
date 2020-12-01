from sqlalchemy import Column, Integer, String

from .database import Base


class Timestamp(Base):
    __tablename__ = "timestamp"

    id = Column(Integer, primary_key=True, index=True)
    time = Column(Integer)


class Link(Base):
    __tablename__ = "links"

    id = Column(Integer, primary_key=True, autoincrement=True)
    link = Column(String, unique=True)
    modified = Column(String)

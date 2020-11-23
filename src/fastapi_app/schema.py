from typing import List, Optional

from pydantic import BaseModel


class TimestampCreate(BaseModel):
    time: int


class Timestamp(TimestampCreate):
    class Config:
        orm_mode = True


class UrlsBase(BaseModel):
    id: int


class UrlsCreate(BaseModel):
    link: str
    modified: str


class Urls(UrlsBase):
    link: str
    modified: str

    class Config:
        orm_mode = True

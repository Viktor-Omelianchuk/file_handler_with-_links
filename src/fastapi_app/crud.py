import logging

from sqlalchemy.orm import Session

from . import models, schema


def create_timestamp(db: Session, time: schema.TimestampCreate):
    db_timestamp = models.Timestamp(time=time.time)
    db.add(db_timestamp)
    db.commit()
    db.refresh(db_timestamp)
    return db_timestamp


def update_timestamp(db: Session, time: int):
    db.query(models.Timestamp).filter(models.Timestamp.id == 1).update(
        {"time": time}, synchronize_session="evaluate"
    )
    db.commit()
    return {"time": time}


def get_urls(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Link).offset(skip).limit(limit).all()


def get_url(db: Session, url_id: int):
    return db.query(models.Link).filter(models.Link.id == url_id).first()


def get_url_by_link(db: Session, link: str):
    return db.query(models.Link).filter(models.Link.link == link).first()


def create_link(db: Session, link: schema.UrlsCreate):
    db_url = models.Link(link=link.link, modified=link.modified)
    db.add(db_url)
    db.commit()
    db.refresh(db_url)
    return db_url


def delete_url(db: Session, url_id: int):
    db_url = db.query(models.Link).filter(models.Link.id == url_id).delete()
    db.commit()
    return db_url


def update_modified_date(db: Session, url_id: int, modified: str):
    db.query(models.Link).filter(models.Link.id == url_id).update(
        {"modified": modified}, synchronize_session="evaluate"
    )
    db.commit()
    return {"modified": modified}

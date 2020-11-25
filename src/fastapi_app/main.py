import logging
from typing import List

from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session

from . import crud, models, schema
from .database import SessionLocal, engine

models.Base.metadata.create_all(bind=engine)

app = FastAPI()


# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.post("/timestamp", response_model=schema.Timestamp)
def create_timestamp(
    timestamp: schema.TimestampCreate, db: Session = Depends(get_db)
):
    return crud.create_timestamp(db=db, time=timestamp)


@app.put("/timestamp", response_model=schema.Timestamp)
def update_timestamp(timestamp: int, db: Session = Depends(get_db)):
    logging.info(type(timestamp))
    return crud.update_timestamp(db=db, time=timestamp)


@app.get("/urls", response_model=List[schema.Urls])
def get_urls(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    urls = crud.get_urls(db, skip=skip, limit=limit)
    return urls


@app.get("/urls/{url_id}", response_model=schema.Urls)
def get_url(url_id: int, db: Session = Depends(get_db)):
    db_url = crud.get_url(db, url_id=url_id)
    if db_url is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_url


@app.post("/urls/", response_model=schema.Urls)
def create_url(link: schema.UrlsCreate, db: Session = Depends(get_db)):
    db_user = crud.get_url_by_link(db, link=link.link)
    if db_user:
        raise HTTPException(status_code=400, detail="Link already exist")
    return crud.create_link(db=db, link=link)


@app.delete("/urls/{url_id}")
def delete_url(url_id: int, db: Session = Depends(get_db)):
    db_url = crud.get_url(db, url_id=url_id)
    if db_url:
        crud.delete_url(db, url_id=url_id)
    else:
        raise HTTPException(status_code=404, detail="Link not found")
    return {f"url link id: {url_id}, '{db_url.link}'": "deleted"}


@app.put("/urls/{url_id}")
def update_url_modified_date(
    url_id: int, modified: str, db: Session = Depends(get_db)
):
    db_url = crud.get_url(db, url_id=url_id)
    if db_url:
        crud.update_modified_date(db, url_id=url_id, modified=modified)
    else:
        raise HTTPException(status_code=404, detail="Link not found")
    return {f"url link id: {url_id}, '{db_url.link}' {modified}": "updated"}

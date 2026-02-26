from typing import TypeVar, Generic, Type, Optional, List
from sqlalchemy.orm import Session
from app.core.database import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    def __init__(self, db, model):
        self.db = db
        self.model = model

    def get(self, id):
        return self.db.query(self.model).filter(self.model.id == id).first()

    def get_all(self, skip = 0, limit = 100):
        return self.db.query(self.model).offset(skip).limit(limit).all()

    def create(self, **kwargs):
        obj = self.model(**kwargs)
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def update(self, obj, **kwargs):
        for key, value in kwargs.items():
            setattr(obj, key, value)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def delete(self, obj):
        self.db.delete(obj)
        self.db.commit()
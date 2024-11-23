from typing import Generic, Optional, Type, TypeVar

from bson import ObjectId
from pydantic import BaseModel
from pymongo.database import Database

T = TypeVar('T', bound=BaseModel)


class BaseService:
    def __init__(self, database: Database):
        self.db = database


class CRUDService(BaseService, Generic[T]):
    def __init__(self, database: Database, collection_name: str, model_class: Type[T]):
        super().__init__(database)
        self.collection = self.db[collection_name]
        self.model_class = model_class

    async def create(self, item: T) -> str:
        item_dict = item.model_dump(exclude_unset=True)
        result = self.collection.insert_one(item_dict)
        return str(result.inserted_id)

    async def get(self, id: str) -> Optional[T]:
        item = self.collection.find_one({'_id': ObjectId(id)})
        return self.model_class(**item) if item else None

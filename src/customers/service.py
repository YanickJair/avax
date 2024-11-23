from typing import Optional

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from src.models.common import NotificationFrequency, ObjectIdField, PydanticObjectId, PyObjectId

from .models import Customer, CustomerSchema, CustomerUpdate


class CustomerService(object):
    def __init__(self, database: AsyncIOMotorDatabase) -> None:
        self._db = database
        self._collection = database.customers

    async def create(self, customer: Customer, /) -> CustomerSchema | None:
        db_customer = await self._collection.insert_one(customer.model_dump(by_alias=True))
        if db_customer:
            return CustomerSchema(**{'id': db_customer.inserted_id, **customer.model_dump(by_alias=True)})

    async def find_one(self, _id: ObjectIdField, /) -> CustomerSchema | None:
        db_customer = await self._collection.find_one({'_id': ObjectId(_id)})
        if db_customer:
            return CustomerSchema(**db_customer)

    async def delete(self, _id: ObjectIdField, /) -> bool:
        deleted = await self._collection.delete_one({'_id': ObjectId(_id)})
        return deleted.deleted_count == 1

    async def update(self, _id: ObjectIdField, /, customer: CustomerUpdate) -> CustomerSchema:
        result = await self._collection.find_one_and_update(
            {'_id': ObjectId(_id)},
            {'$set': customer.model_dump(by_alias=True, exclude_unset=True)},
            return_document=True,
        )
        return CustomerSchema(**result)

    async def list_all(
        self, skip: int = 0, limit: int = 10, search: Optional[str] = None, is_active: Optional[bool] = True
    ) -> list[CustomerSchema]:
        query = {'is_active': is_active}

        if search:
            query['$or'] = [{'name': {'$regex': search, '$options': 'i'}}]
        customers = await self._collection.find(query).skip(skip).limit(limit).to_list(length=limit)
        return [CustomerSchema(**customer) for customer in customers]

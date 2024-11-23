from typing import Optional

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from src.models.common import NotificationFrequency, ObjectIdField, PydanticObjectId

from .models import Channel, ChannelSchema, ChannelUpdateSchema


class ChannelService(object):
    def __init__(self, database: AsyncIOMotorDatabase) -> None:
        self._db = database
        self._collection = database.channels

    async def create(self, channel: Channel, /) -> ChannelSchema | None:
        result = await self._collection.insert_one(channel.model_dump(by_alias=True))
        if result:
            return ChannelSchema(**{'id': result.inserted_id, **channel.model_dump(by_alias=True)})

    async def find_one(self, _id: ObjectIdField) -> ChannelSchema | None:
        channel = await self._collection.find_one({'_id': ObjectId(_id)})
        if channel:
            return ChannelSchema(**channel)

    async def find_by(self, key: str, value: str) -> ChannelSchema | None:
        channel = await self._collection.find_one({key: value})
        if channel:
            return ChannelSchema(**channel)

    async def delete(self, _id: ObjectIdField) -> bool:
        deleted = await self._collection.delete_one({'_id': ObjectId(_id)})
        return deleted.deleted_count == 1

    async def update(self, _id: ObjectIdField, channel: ChannelUpdateSchema) -> ChannelSchema:
        result = await self._collection.find_one_and_update(
            {'_id': ObjectId(_id)}, {'$set': {**channel.model_dump(by_alias=True)}}, return_document=True
        )
        return ChannelSchema(**result)

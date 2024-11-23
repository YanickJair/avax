from datetime import datetime
from typing import Annotated, Literal

from bson import ObjectId
from pydantic import BaseModel, ConfigDict, Field
from pymongo.synchronous.database import Database
from typing_extensions import Optional

from .common import NotificationFrequency, PydanticObjectId

_CUSTOMER_COLLECTION = 'customers'


class ContactMethod(BaseModel):
    type: Literal['email', 'phone', 'sms', 'web_chat', 'facebook', 'twitter', 'whatsapp', 'telegram']
    value: str  # e.g., email address, phone number, social media handle
    is_preferred: Optional[bool] = False


class CustomerPreference(BaseModel):
    preferred_language: str = 'en'
    time_zone: str = 'UTC'
    notification_frequency: Literal['immediate', 'daily', 'weekly'] = Field(NotificationFrequency.IMMEDIATE.value)
    opt_in_marketing: bool = False


class Customer(BaseModel):
    name: str
    contact_methods: list[ContactMethod]
    preferences: CustomerPreference
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    tags: Optional[list[str]] = []

    async def create(self, client: Database):
        customer_collection = client[_CUSTOMER_COLLECTION]
        result = customer_collection.insert_one(self.model_dump())
        return CustomerSchema(**{'id': result.inserted_id, **self.model_dump()})

    @classmethod
    async def find_one(cls, _id: str, /, client: Database):
        customer_collection = client[_CUSTOMER_COLLECTION]
        db_customer = customer_collection.find_one({'_id': ObjectId(_id)})
        if db_customer:
            return CustomerSchema(**db_customer)

    @classmethod
    async def delete(cls, _id: str, client: Database) -> bool:
        collection = client[_CUSTOMER_COLLECTION]
        deleted = collection.delete_one({'_id': ObjectId(_id)})
        return deleted.deleted_count == 1


class CustomerSchema(PydanticObjectId, Customer):
    pass

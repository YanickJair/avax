from datetime import datetime
from typing import Annotated, Literal

from bson import ObjectId
from pydantic import BaseModel, ConfigDict, Field
from pymongo.synchronous.database import Database
from typing_extensions import Optional

from src.models.common import NotificationFrequency, ObjectIdField, PydanticObjectId, PyObjectId

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
    is_active: Optional[bool] = Field(True)


class CustomerUpdate(BaseModel):
    name: Optional[str] = Field(None)
    contact_methods: Optional[list[ContactMethod]] = Field(None)
    preferences: Optional[CustomerPreference] = Field(None)
    updated_at: datetime = Field(default_factory=datetime.now)
    tags: Optional[list[str]] = Field(None)
    is_active: Optional[bool | None] = Field(None)


class CustomerSchema(PydanticObjectId, Customer):
    pass

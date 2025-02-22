from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, Field

from src.models.common import NotificationFrequency, PydanticObjectId

_CUSTOMER_COLLECTION = 'customers'


class ContactMethod(BaseModel):
    type: Literal['email', 'phone', 'sms', 'web_chat', 'facebook', 'twitter', 'whatsapp', 'telegram']
    value: str  # e.g., email address, phone number, social media handle
    is_preferred: bool | None = False


class CustomerPreference(BaseModel):
    preferred_language: str = 'en'
    time_zone: str = 'UTC'
    notification_frequency: Literal['immediate', 'daily', 'weekly'] = Field(NotificationFrequency.IMMEDIATE.value)
    opt_in_marketing: bool = False


class Customer(BaseModel):
    name: str | None = Field(None, description="Customer's name")
    contact_methods: list[ContactMethod]
    preferences: Annotated[CustomerPreference, Field(..., description="Can be set accoring to incoming request")]
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    tags: list[str] | None = []
    is_active: bool | None = Field(True)


class CustomerUpdate(BaseModel):
    name: str | None = Field(None, description="Customer's name")
    contact_methods: list[ContactMethod] | None = Field(None)
    preferences: CustomerPreference | None = Field(None)
    updated_at: datetime = Field(default_factory=datetime.now)
    tags: list[str] | None = Field(None)
    is_active: bool | None | None = Field(None)


class CustomerSchema(PydanticObjectId, Customer):
    pass

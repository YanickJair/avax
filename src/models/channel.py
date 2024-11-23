from datetime import datetime
from enum import Enum
from typing import Annotated, Literal, Optional

from bson import ObjectId
from pydantic import BaseModel, ConfigDict, EmailStr, Field, HttpUrl
from pydantic_core.core_schema import str_schema
from pymongo.synchronous.database import Database

from .common import NotificationFrequency, PydanticObjectId

_CHANNEL_COLLECTION = 'channels'


class ChannelType(Enum):
    EMAIL = 'email'
    PHONE = 'phone'
    CHAT = 'chat'
    SOCIAL_MEDIA = 'social_media'


class EmailChannelConfig(BaseModel):
    smtp_server: str
    smtp_port: int
    username: EmailStr
    password: str  # In practice, use secure storage for passwords
    use_tls: bool = True

    async def notify(self, value: str, message: str): ...


class SocialMediaChannelConfig(BaseModel):
    platform: Literal['facebook', 'twitter', 'instagram', 'linkedin']
    account_name: str
    access_token: str  # In practice, use secure storage for tokens
    api_version: Optional[str] = None

    async def notify(self, value: str, message: str): ...


class ChatChannelConfig(BaseModel):
    provider: Literal['web_chat', 'whatsapp', 'telegram']
    api_key: str  # In practice, use secure storage for API keys
    webhook_url: Optional[HttpUrl] = None

    async def notify(self, value: str, message: str): ...


class PhoneChannelConfig(BaseModel):
    provider: str
    account_sid: str
    auth_token: str  # In practice, use secure storage for tokens
    phone_number: str

    async def notify(self, value: str, message: str): ...


ChannelConfig = EmailChannelConfig | SocialMediaChannelConfig | ChatChannelConfig | PhoneChannelConfig


class EmailChannel(BaseModel):
    name: ChannelType
    details: dict  # Channel-specific details
    created_at: datetime = Field(default_factory=datetime.now)


class Channel(BaseModel):
    name: str
    type: Literal['email', 'social_media', 'chat', 'phone']
    is_active: bool = True
    config: ChannelConfig = Field(...)

    async def create(self, client: Database):
        collection = client[_CHANNEL_COLLECTION]
        channel = collection.insert_one(self.model_dump())
        if channel:
            return ChannelSchema(**{'id': channel.inserted_id, **self.model_dump()})
        return None

    @classmethod
    async def find_one(cls, _id: str, client: Database):
        collection = client[_CHANNEL_COLLECTION]
        channel = collection.find_one({'_id': ObjectId(_id)})
        if channel:
            return ChannelSchema(**channel)

    @classmethod
    async def find_by(cls, key: str, value: str, client: Database):
        collection = client[_CHANNEL_COLLECTION]
        channel = collection.find_one({key: value})
        if channel:
            return ChannelSchema(**channel)

    @staticmethod
    async def delete(_id: str, client: Database) -> bool:
        collection = client[_CHANNEL_COLLECTION]
        deleted = collection.delete_one({'_id': ObjectId(_id)})
        return deleted.deleted_count == 1

    @staticmethod
    async def update(): ...


class ChannelSchema(PydanticObjectId, Channel):
    pass

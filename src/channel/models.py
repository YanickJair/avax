from datetime import datetime
from enum import Enum
from typing import Annotated, Literal

from pydantic import BaseModel, Field, HttpUrl, field_validator

from src.models.common import PydanticObjectId

_CHANNEL_COLLECTION = 'channels'


class ChannelType(Enum):
    EMAIL = 'email'
    PHONE = 'phone'
    CHAT = 'chat'
    SOCIAL_MEDIA = 'social_media'


class EmailChannelConfig(BaseModel):
    smtp_server: Annotated[str, Field(..., description="server URL or IP address")]
    smtp_port: Annotated[int, Field(..., description="server Port")]
    username: Annotated[str | None, Field(default=None, description="server username")]
    password: Annotated[str | None, Field(default=None, description="server password")]  # In practice, use secure storage for passwords
    key: Annotated[str | None, Field(default=None, description="server private key if password not provided")]
    use_tls: bool = True

    @field_validator("key")
    @classmethod
    def validate_key(cls, v) -> str:
        if not v:
            raise ValueError("please provide username and password when key not provided")
        return v

    async def notify(self, value: str, message: str): ...


class SocialMediaChannelConfig(BaseModel):
    platform: Literal['facebook', 'twitter', 'instagram', 'linkedin']
    account_name: Annotated[str, Field(..., description="social media account name")]
    access_token: Annotated[str, Field(..., description="social media access token")]  # In practice, use secure storage for tokens
    api_version: Annotated[str | None, Field(default=None, description="social api version")]

    async def notify(self, value: str, message: str): ...


class ChatChannelConfig(BaseModel):
    provider: Literal['web_chat', 'whatsapp', 'telegram']
    api_key: Annotated[str, Field(..., description="Authentication Key")]  # In practice, use secure storage for API keys
    webhook_url: HttpUrl | None = None

    async def notify(self, value: str, message: str): ...


class PhoneChannelConfig(BaseModel):
    provider: Annotated[str, Field(..., description="phone service provider")]
    account_sid: Annotated[str, Field(..., description="configuration's name")]
    auth_token: Annotated[str, Field(..., description="provider authentication token")]  # In practice, use secure storage for tokens
    phone_number: Annotated[str, Field(..., description="phone number")]

    async def notify(self, value: str, message: str): ...


ChannelConfig = EmailChannelConfig | SocialMediaChannelConfig | ChatChannelConfig | PhoneChannelConfig


class EmailChannel(BaseModel):
    name: ChannelType
    details: dict  # Channel-specific details
    created_at: datetime = Field(default_factory=datetime.now)


class ChannelUpdateSchema(BaseModel):
    name: str | None = Field(..., description='The new channel name')
    type: Literal['email', 'social_media', 'chat', 'phone'] | None
    is_active: bool | None = Field(True)
    config: ChannelConfig | None = Field(...)


class Channel(BaseModel):
    name: Annotated[str, Field(..., description="configuration's name")]
    type: Annotated[str, Literal['email', 'social_media', 'chat', 'phone']]
    is_active: Annotated[bool | None, Field(default=False, description="configuration status")]
    config: Annotated[ChannelConfig, Field(..., description="")]


class ChannelSchema(PydanticObjectId, Channel):
    pass

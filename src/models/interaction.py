from datetime import datetime
from enum import Enum
from typing import Literal, Optional

from pydantic import BaseModel, Field
from pymongo.synchronous.database import Database

from .common import PydanticObjectId

_INTERACTION_COLLECTION = 'interactions'


class InteractionStatus(str, Enum):
    OPEN = 'open'
    IN_PROGRESS = 'in_progress'
    WAITING_ON_CUSTOMER = 'waiting_on_customer'
    RESOLVED = 'resolved'
    CLOSED = 'closed'


class InteractionPriority(str, Enum):
    LOW = 'low'
    MEDIUM = 'medium'
    HIGH = 'high'
    URGENT = 'urgent'


class InteractionMessage(BaseModel):
    id: str = Field(default_factory=lambda: f'msg_{datetime.now().timestamp()}')
    sender: Literal['customer', 'agent']
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)


class Interaction(BaseModel):
    customer_id: str
    channel_id: str
    agent_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    status: InteractionStatus = InteractionStatus.OPEN
    priority: InteractionPriority = InteractionPriority.MEDIUM
    subject: str
    messages: list[InteractionMessage] = []
    tags: list[str] = []

    async def create(self, client: Database):
        collection = client[_INTERACTION_COLLECTION]
        interaction = collection.insert_one(self.model_dump())
        return InteractionSchema(**{'id': interaction.inserted_id, **self.model_dump()})


class InteractionSchema(PydanticObjectId, Interaction):
    pass

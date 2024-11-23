from datetime import datetime
from enum import Enum

from bson.objectid import ObjectId
from pydantic import BaseModel, ConfigDict, Field, field_validator
from pymongo.cursor import Optional
from pymongo.synchronous.database import Database

from src.channel.models import Channel
from src.customers.models import Customer
from src.models.common import ObjectIdField, PydanticObjectId, PyObjectId

_TICKETS_COLLECTION = 'tickets'


class TicketStatus(str, Enum):
    OPEN = 'open'
    IN_PROGRESS = 'in_progress'
    RESOLVED = 'resolved'
    CLOSED = 'closed'


class TicketPriority(str, Enum):
    LOW = 'low'
    MEDIUM = 'medium'
    HIGH = 'high'
    URGENT = 'urgent'


class TicketCategory(str, Enum):
    BILLING = 'billing'
    TECHNICAL = 'technical'
    GENERAL = 'general'
    FEATURE_REQUEST = 'feature_request'


class TicketMessage(BaseModel):
    id: Optional[ObjectIdField] = Field(
        default_factory=ObjectId, description='Unique identifier for the message', alias='_id'
    )
    content: str
    sender: str
    timestamp: datetime = Field(..., default_factory=datetime.now)
    channel_id: ObjectIdField = Field(..., description='Channel through which to contact customer')
    updated_at: datetime = Field(default_factory=datetime.now)

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: lambda v: str(v)}


class UpdateMessageSchema(BaseModel):
    content: Optional[str] = Field(..., description='message content')
    channel_id: Optional[ObjectIdField] = Field(..., description='Channel through which to contact customer')


class Ticket(BaseModel):
    customer_id: ObjectIdField
    assigned_agent_id: Optional[ObjectIdField] = Field(
        ..., description='Agent responsible for the ticket. Id will be assigned when agent is assigned'
    )
    status: TicketStatus = Field(default=TicketStatus.OPEN)
    priority: TicketPriority = Field(default=TicketPriority.MEDIUM)
    category: TicketCategory
    subject: str
    messages: list[TicketMessage]
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    resolved_at: Optional[datetime] = None
    tags: Optional[list[str]]

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        json_schema_extra={'example': {'_id': '64f3f0f8c6cedb12c93372c4'}},
        json_encoders={ObjectId: lambda v: str(v)},
    )

    @classmethod
    async def is_customer(cls, v: ObjectIdField, client: Database) -> bool:
        if customer := await Customer.find_one(v, client):
            return True
        return False

    async def create(self, client: Database):
        if not await self.is_customer(self.customer_id, client):
            raise Exception('Customer not found')

        collection = client[_TICKETS_COLLECTION]
        ticket = collection.insert_one(self.model_dump(by_alias=True))
        if ticket:
            return TicketSchema(**{'id': ticket.inserted_id, **self.model_dump()})
        return None

    @classmethod
    async def add_message(cls, ticket_id: PyObjectId, message: TicketMessage, client: Database):
        collection = client[_TICKETS_COLLECTION]
        ticket = collection.find_one_and_update(
            {'_id': ObjectId(ticket_id)}, {'$push': {'messages': message.model_dump()}}, return_document=True
        )
        return ticket

    @classmethod
    async def delete_message(cls, ticket_id: PyObjectId, message_id: PyObjectId, client: Database):
        collection = client[_TICKETS_COLLECTION]
        ticket = collection.find_one_and_update(
            {'_id': ObjectId(ticket_id)}, {'$pull': {'messages': {'_id': ObjectId(message_id)}}}, return_document=True
        )
        return ticket

    @staticmethod
    async def update_message(
        ticket_id: PyObjectId, message_id: PyObjectId, client: Database, content: UpdateMessageSchema
    ):
        collection = client[_TICKETS_COLLECTION]
        ticket = collection.find_one_and_update(
            {
                '_id': ObjectId(ticket_id),  # Find the ticket by its _id
                'messages._id': ObjectId(message_id),  # Find the specific message by its _id
            },
            {
                '$set': {
                    'messages.$.content': content.content,  # Update the content field
                    'updated_at': datetime.now(),  # Update the ticket's updated_at timestamp
                }
            },
            return_document=True,
        )
        if ticket:
            return ticket

    @staticmethod
    async def find_one(_id: PyObjectId, client: Database):
        collection = client[_TICKETS_COLLECTION]
        ticket = collection.find_one({'_id': ObjectId(_id)})
        if ticket:
            return TicketSchema(**ticket)

    @staticmethod
    async def get_tickets(client: Database):
        collection = client[_TICKETS_COLLECTION]
        tickets = [TicketSchema(**ticket) for ticket in collection.find()]
        return tickets


class TicketActivity(BaseModel):
    ticket_id: str = Field(...)
    agent_id: Optional[str]
    activity_type: str
    details: str
    timestammp: datetime = Field(default_factory=datetime.now)


class TicketActivitySchema(PydanticObjectId, TicketActivity):
    pass


class TicketSchema(PydanticObjectId, Ticket):
    pass

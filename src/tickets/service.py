from datetime import datetime

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from src.models.common import ObjectIdField
from src.utils.response import AppException, ErrorDetail, ResponseStatus

from .models import Ticket, TicketMessage, TicketSchema, UpdateMessageSchema


class TicketService(object):
    def __init__(self, database: AsyncIOMotorDatabase) -> None:
        self._db = database
        self._collection = database.tickets

    async def create(self, ticket: Ticket) -> TicketSchema:
        result = await self._collection.insert_one(ticket.model_dump(by_alias=True))
        if not result:
            raise AppException(status_code=400, message='Failed to update channel', error_code='INTERNAL_ERROR')
        return TicketSchema(**{'id': result.inserted_id, **ticket.model_dump(by_alias=True)})

    async def find_one(self, _id: ObjectIdField, /) -> TicketSchema:
        result = await self._collection.find_one({'_id': ObjectId(_id)})
        if not result:
            raise AppException(status_code=404, message=f'Failed to find ticket {_id}', error_code='TICKET_NOT_FOUND')
        return TicketSchema(**result)

    async def delete(self, _id: ObjectIdField, /) -> bool:
        deleted = await self._collection.delete_one({'_id': ObjectId(_id)})
        return deleted.deleted_count == 1

    async def add_message(self, ticket_id: ObjectIdField, message: TicketMessage) -> TicketSchema:
        ticket = await self._collection.find_one_and_update(
            {'_id': ObjectId(ticket_id)}, {'$push': {'messages': message.model_dump()}}, return_document=True
        )
        if not ticket:
            raise AppException(
                status_code=404, message=f'Failed to find ticket {ticket_id}', error_code='TICKET_NOT_FOUND'
            )
        return TicketSchema(**ticket)

    async def delete_message(self, ticket_id: ObjectIdField, message_id: ObjectIdField) -> TicketSchema:
        ticket = await self._collection.find_one_and_update(
            {'_id': ObjectId(ticket_id)}, {'$pull': {'messages': {'_id': ObjectId(message_id)}}}, return_document=True
        )
        if not ticket:
            raise AppException(
                status_code=404, message=f'Failed to find ticket {ticket_id}', error_code='TICKET_NOT_FOUND'
            )
        return TicketSchema(**ticket)

    async def update_message(
        self, ticket_id: ObjectIdField, message_id: ObjectIdField, content: UpdateMessageSchema
    ) -> TicketSchema:
        ticket = await self._collection.find_one_and_update(
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
        if not ticket:
            raise AppException(
                status_code=404, message=f'Failed to find ticket {ticket_id}', error_code='TICKET_NOT_FOUND'
            )
        return TicketSchema(**ticket)

    async def get_tickets(self):
        tickets = await self._collection.find()
        tickets = [TicketSchema(**ticket) for ticket in tickets]
        return tickets

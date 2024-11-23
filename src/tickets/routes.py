from functools import cache
from typing import Annotated

from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase

from src.db.connection import get_database
from src.models.common import ObjectIdField
from src.utils.response import AppException, BaseResponse, ErrorDetail, ResponseStatus, create_response

from .models import Ticket, TicketMessage, TicketSchema, UpdateMessageSchema
from .service import TicketService

router = APIRouter(prefix='/ticket')


@cache
def get_ticket_service(db: AsyncIOMotorDatabase = Depends(get_database)) -> TicketService:
    return TicketService(db)


TicketServiceDep = Annotated[TicketService, Depends(get_ticket_service)]


@router.post('', response_model=TicketSchema)
async def create(ticket: Ticket, service: TicketServiceDep):
    try:
        return await service.create(ticket)
    except:
        raise


@router.get('')
async def tickets(service: TicketServiceDep):
    try:
        return await service.get_tickets()
    except:
        raise


@router.put('/{ticket_id}/message', response_model=TicketSchema)
async def add_message(ticket_id: ObjectIdField, message: TicketMessage, service: TicketServiceDep):
    try:
        return await service.add_message(ticket_id=ticket_id, message=message)
    except:
        raise


@router.put('/{ticket_id}/message/{message_id}', response_model=TicketSchema)
async def update_message(
    ticket_id: ObjectIdField, message_id: ObjectIdField, content: UpdateMessageSchema, service: TicketServiceDep
):
    try:
        return await service.update_message(ticket_id=ticket_id, message_id=message_id, content=content)
    except:
        raise

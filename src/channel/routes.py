from functools import cache
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase

from src.db.connection import get_database
from src.models.common import ObjectIdField
from src.utils.response import AppException, BaseResponse, ErrorDetail, ResponseStatus, create_response

from .models import Channel, ChannelSchema, ChannelUpdateSchema
from .service import ChannelService

router = APIRouter(prefix='/channels')


@cache
def get_customer_service(db: AsyncIOMotorDatabase = Depends(get_database)) -> ChannelService:
    return ChannelService(db)


ChannelServiceDep = Annotated[ChannelService, Depends(get_customer_service)]


@router.post('', response_model=BaseResponse)
async def create(channel: Channel, service: ChannelServiceDep):
    try:
        result = await service.create(channel)
        return create_response(data=result, message='Channel successfully created', status=ResponseStatus.SUCCESS)
    except Exception as e:
        return create_response(
            message='Failed to create channel',
            status=ResponseStatus.ERROR,
            errors=[ErrorDetail(code='CHANNEL_CREATION_ERROR', message=str(e))],
            status_code=400,
        )


@router.put('/{_id}', response_model=BaseResponse)
async def update(_id: ObjectIdField, channel: ChannelUpdateSchema, service: ChannelServiceDep):
    try:
        result = await service.update(_id, channel=channel)
        if not result:
            raise AppException(status_code=400, message='Failed to update channel', error_code='INTERNAL_ERROR')

        return create_response(data=result)
    except Exception as e:
        return create_response(
            message='Failed to update channel',
            status=ResponseStatus.ERROR,
            errors=[ErrorDetail(code='INTERNAL_ERROR', message=str(e))],
            status_code=400,
        )


@router.get('/{_id}', response_model=BaseResponse)
async def find_one(_id: ObjectIdField, service: ChannelServiceDep):
    try:
        result = await service.find_one(_id)
        if not result:
            raise AppException(
                status_code=404,
                message='Channel not found',
                error_code='CHANNEL_FETCH_ERROR',
                error_details={'_id': _id},
            )
        return create_response(data=result)
    except Exception as e:
        return create_response(
            message=f'Failed to find channel {_id}',
            status=ResponseStatus.ERROR,
            errors=[ErrorDetail(code='INTERNAL_ERROR', message=str(e))],
            status_code=400,
        )

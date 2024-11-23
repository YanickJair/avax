from functools import cache
from typing import Annotated, Optional

from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase

from src.db.connection import get_database
from src.models.common import ObjectIdField, PydanticObjectId, PyObjectId
from src.utils.response import AppException, BaseResponse, create_response

from .models import Customer, CustomerSchema, CustomerUpdate
from .service import CustomerService

router = APIRouter(prefix='/customers', tags=['customers', 'customer'])


@cache
def get_customer_service(db: AsyncIOMotorDatabase = Depends(get_database)) -> CustomerService:
    return CustomerService(db)


CustomerServiceDep = Annotated[CustomerService, Depends(get_customer_service)]


@router.post('/', response_model=BaseResponse)
async def create(customer: Customer, service: CustomerServiceDep):
    try:
        db_customer = await service.create(customer)
        if not db_customer:
            pass
        return create_response(data=db_customer, message='New customer created successfully')
    except Exception as exc:
        raise exc


@router.put('/{_id}', response_model=BaseResponse)
async def update(_id: ObjectIdField, customer: CustomerUpdate, service: CustomerServiceDep):
    try:
        data = await service.update(_id, customer=customer)
        if not data:
            pass

        return create_response(data=data, message=f'Customer with {_id} updated.')
    except:
        raise


@router.delete('/{_id}')
async def delete(_id: ObjectIdField, service: CustomerServiceDep):
    try:
        data = await service.delete(_id)
        if not data:
            pass

        return create_response(data=data, message=f'Customer with {_id} deleted.')
    except Exception as exc:
        raise exc


@router.get('/{_id}', response_model=BaseResponse)
async def get_customer(_id: ObjectIdField, service: CustomerServiceDep):
    try:
        data = await service.find_one(_id)
        if not data:
            pass

        return create_response(data=data, message=f'Customer with {_id} found.')
    except Exception as exc:
        print(str(exc))


@router.get('/', response_model=BaseResponse)
async def get_customers(
    service: CustomerServiceDep,
    skip: int = 0,
    limit: int = 10,
    search: Optional[str] = None,
    is_active: Optional[bool] = True,
):
    try:
        data = await service.list_all(skip=skip, limit=limit, search=search, is_active=is_active)
        if not data:
            pass
        return create_response(data=data, message=f'Customers list.')
    except Exception as exc:
        print(str(exc))

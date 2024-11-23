import logging
import traceback
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Generic, Optional, TypeVar

from fastapi import HTTPException, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field

T = TypeVar('T')  # Generic type for response data
logger = logging.getLogger(__name__)


class ResponseStatus(str, Enum):
    SUCCESS = 'success'
    ERROR = 'error'
    WARNING = 'warning'


class ErrorDetail(BaseModel):
    code: str
    message: str
    field: Optional[str] = None
    details: Optional[dict[str, Any]] = None


class ResponseMetadata(BaseModel):
    timestamp: datetime = Field(default_factory=datetime.now)
    request_id: Optional[str] = None
    version: str = '1.0'
    params: Optional[dict[str, Any]] = None

    model_config = ConfigDict(json_encoders={datetime: lambda v: v.isoformat()})


class BaseResponse(BaseModel, Generic[T]):
    status: ResponseStatus
    message: str
    data: Optional[T] = None
    errors: Optional[list[ErrorDetail]] = None
    metadata: ResponseMetadata = Field(default_factory=ResponseMetadata)

    model_config = ConfigDict(json_encoders={datetime: lambda v: v.isoformat()})

    def to_json_response(self, status_code: int = 200) -> JSONResponse:
        return JSONResponse(
            status_code=status_code,
            content=jsonable_encoder(self),
        )


def create_response(
    data: Optional[Any] = None,
    message: str = 'Operation completed successfully',
    status: ResponseStatus = ResponseStatus.SUCCESS,
    errors: Optional[list[ErrorDetail]] = None,
    metadata: Optional[dict[str, Any]] = None,
    status_code: int = 200,
) -> BaseResponse:
    """Create a standardized response object."""
    response = BaseResponse(
        status=status, message=message, data=data, errors=errors, metadata=ResponseMetadata(**(metadata or {}))
    )
    return response


# Common error codes
class ErrorCodes:
    NOT_FOUND = 'NOT_FOUND'
    VALIDATION_ERROR = 'VALIDATION_ERROR'
    UNAUTHORIZED = 'UNAUTHORIZED'
    FORBIDDEN = 'FORBIDDEN'
    INTERNAL_ERROR = 'INTERNAL_ERROR'
    DUPLICATE_ENTRY = 'DUPLICATE_ENTRY'
    INVALID_INPUT = 'INVALID_INPUT'
    SERVICE_UNAVAILABLE = 'SERVICE_UNAVAILABLE'


class AppException(HTTPException):
    def __init__(
        self,
        status_code: int,
        message: str,
        error_code: str = ErrorCodes.INTERNAL_ERROR,
        error_details: Optional[dict[str, Any]] = None,
    ):
        super().__init__(status_code=status_code, detail=message)
        self.error_code = error_code
        self.error_details = error_details

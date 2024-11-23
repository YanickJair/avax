import logging
import traceback
from typing import Callable

from fastapi import HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from src.utils.response import ErrorCodes, ErrorDetail, create_response

logger = logging.getLogger(__name__)


async def error_handler_middleware(request: Request, call_next: Callable) -> JSONResponse:
    try:
        return await call_next(request)
    except HTTPException as exc:
        error_detail = ErrorDetail(
            code=getattr(exc, 'error_code', ErrorCodes.INTERNAL_ERROR),
            message=str(exc.detail),
            details=getattr(exc, 'error_details', None),
        )
        return create_response(
            message='Request failed', errors=[error_detail], status_code=exc.status_code
        ).to_json_response(exc.status_code)
    except RequestValidationError as exc:
        errors = [
            ErrorDetail(
                code=ErrorCodes.VALIDATION_ERROR,
                message=str(error.get('msg')),
                field='.'.join(str(x) for x in error.get('loc', [])),
                details=error,
            )
            for error in exc.errors()
        ]
        return create_response(message='Validation error', errors=errors, status_code=422).to_json_response(422)
    except Exception as exc:
        logger.error(f'Unhandled exception: {str(exc)}\n{traceback.format_exc()}')
        return create_response(
            message='Internal server error',
            errors=[
                ErrorDetail(
                    code=ErrorCodes.INTERNAL_ERROR,
                    message='An unexpected error occurred',
                    details={'type': type(exc).__name__},
                )
            ],
            status_code=500,
        ).to_json_response(500)

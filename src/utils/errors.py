from bson.errors import InvalidId
from fastapi import Request, status
from fastapi.responses import JSONResponse


async def invalid_id(request: Request, exc: InvalidId) -> JSONResponse:
    return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={'message': f'Invalid ObjectId: {str(exc)}'})

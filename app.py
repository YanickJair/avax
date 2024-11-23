from contextlib import asynccontextmanager

import uvicorn
from bson.errors import InvalidId
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.channel.routes import router as channel_router
from src.core.config import Settings
from src.core.middleware import error_handler_middleware
from src.customers.routes import router as customer_routes
from src.db.connection import close_mongodb_connection, connect_to_mongodb
from src.tickets.routes import router as ticket_router
from src.utils import errors

settings = Settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_to_mongodb()
    yield
    await close_mongodb_connection()


def create_app() -> FastAPI:
    app = FastAPI(
        title='Omnichannel Support System',
        description='API for omnichannel customer support system',
        version='1.0.0',
        lifespan=lifespan,
        exception_handlers={InvalidId: errors.invalid_id},
    )

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=['*'],
        allow_headers=['*'],
    )

    # Add error handler middleware
    app.middleware('http')(error_handler_middleware)

    # Register routers
    app.include_router(customer_routes)
    app.include_router(ticket_router)
    app.include_router(channel_router)

    return app


app = create_app()


if __name__ == '__main__':
    uvicorn.run(host='127.0.0.1', port=8000, app='app:app', reload=True)

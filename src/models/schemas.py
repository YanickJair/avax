from datetime import datetime
from typing import Annotated

from bson import ObjectId
from pydantic import BaseModel, ConfigDict, Field
from pymongo.synchronous.database import Database

from .common import ObjectIdField


class Agent(BaseModel):
    id: str = Field(default_factory=lambda: f'agent_{datetime.now().timestamp()}')
    name: str
    email: str
    skills: list[str]
    availability: bool = True


class Feedback(BaseModel):
    id: str = Field(default_factory=lambda: f'feed_{datetime.now().timestamp()}')
    interaction_id: str
    rating: int  # e.g., 1-5 star rating
    comment: str | None = None
    created_at: datetime = Field(default_factory=datetime.now)

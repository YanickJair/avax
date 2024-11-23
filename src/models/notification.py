from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field
from pymongo.synchronous.database import Database

from .channel import ChannelSchema
from .common import PydanticObjectId
from .customer import CustomerSchema
from .interaction import InteractionPriority, InteractionSchema

_NOTIFICATION_COLLECTION = 'notifications'


class NotificationType(str, Enum):
    STATUS_UPDATE = 'status_update'
    NEW_MESSAGE = 'new_message'
    ESCALATION = 'escalation'
    RESOLUTION = 'resolution'


class Notification(BaseModel):
    interaction_id: str
    customer_id: str
    type: NotificationType
    message: str
    created_at: datetime = Field(default_factory=datetime.now)
    sent: bool = False

    async def create(self, client: Database):
        collection = client[_NOTIFICATION_COLLECTION]
        notification = collection.insert_one(self.model_dump())
        return NotificationSchema(**{'id': notification.inserted_id, **self.model_dump()})

    @staticmethod
    async def should_notify(
        interaction: InteractionSchema, customer: CustomerSchema, notification_type: NotificationType
    ):
        # Implement logic to determine if a notification should be sent
        # This could be based on customer preferences, interaction priority, etc.
        if notification_type == NotificationType.STATUS_UPDATE:
            return customer.preferences.notification_frequency == 'immediate'
        elif notification_type == NotificationType.NEW_MESSAGE:
            return interaction.priority in (InteractionPriority.HIGH, InteractionPriority.URGENT)
        elif notification_type == NotificationType.ESCALATION:
            return True  # Always notify on escalation
        elif notification_type == NotificationType.RESOLUTION:
            return True  # Always notify on resolution
        return False

    @staticmethod
    async def send_notification(notification: 'NotificationSchema', client: Database):
        # Implement logic to send notification based on customer's preferred contact method

        if customer := await CustomerSchema.find_one(notification.customer_id, client):
            preferred_contact = next(
                (cm for cm in customer.contact_methods if cm.is_preferred), customer.contact_methods[0]
            )
            if channel := await ChannelSchema.find_by(value=preferred_contact.type, key='type', client=client):
                await channel.config.notify(preferred_contact.value, notification.message)

            notification.sent = True
            # Here you would typically update the notification in the database


class NotificationSchema(PydanticObjectId, Notification):
    pass

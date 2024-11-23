import pytest

from settings import DatabaseSettings
from src.db.connection import DBClient
from src.models.common import NotificationFrequency
from src.models.customer import ContactMethod, Customer, CustomerPreference


class TestDBClient:
    @pytest.mark.asyncio
    async def test_customer(self):
        client = DBClient()
        connection = client.connect()
        new_customer = Customer(
            name='John Doe',
            contact_methods=[
                ContactMethod(type='email', value='john@example.com', is_preferred=True),
                ContactMethod(type='phone', value='+1234567890'),
                ContactMethod(type='twitter', value='@john_doe'),
            ],
            preferences=CustomerPreference(
                preferred_language='en',
                time_zone='America/New_York',
                notification_frequency=NotificationFrequency.DAILY.value,
                opt_in_marketing=True,
            ),
        )
        res = await new_customer.create(client=connection)
        assert res

        res = await Customer.find_one(res.id, client=connection)
        assert res

        res = await Customer.delete(res.id, client=connection)
        assert res

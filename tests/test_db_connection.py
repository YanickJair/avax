import pytest

from src.customers.models import ContactMethod, Customer, CustomerPreference
from src.customers.service import CustomerService
from src.db.connection import get_database
from src.models.common import NotificationFrequency


class TestDBClient:
    @pytest.mark.asyncio
    async def test_customer(self):
        client = await get_database()
        service = CustomerService(database=client)

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
            is_active=True
        )
        res = await service.create(new_customer)
        assert res

        res = await service.find_one(res.id)
        assert res

        res = await service.delete(res.id)
        assert res

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import delete
from server.models import OfflineMessage

class OfflineMessageRepository:
    """Handles data access for the OfflineMessage model."""
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_for_user(self, user_id: int) -> list[OfflineMessage]:
        """Retrieves all offline messages for a given user."""
        result = await self._session.execute(
            select(OfflineMessage).where(OfflineMessage.recipient_user_id == user_id).order_by(OfflineMessage.timestamp)
        )
        return result.scalars().all()

    async def save(self, recipient_id: int, payload: str):
        """Saves a new offline message."""
        new_message = OfflineMessage(
            recipient_user_id=recipient_id,
            message_payload=payload
        )
        self._session.add(new_message)

    async def delete(self, message: OfflineMessage):
        """Deletes an offline message."""
        await self._session.delete(message)

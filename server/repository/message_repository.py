from sqlalchemy.ext.asyncio import AsyncSession
from server.models import OfflineMessage

class MessageRepository:
    """封装与消息相关的数据库操作，主要是离线消息"""
    def __init__(self, session: AsyncSession):
        self._session = session

    async def save_offline_message(self, recipient_id: int, message_payload: str):
        """保存一条离线消息"""
        offline_msg = OfflineMessage(
            recipient_user_id=recipient_id,
            message_payload=message_payload
        )
        self._session.add(offline_msg)

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import or_, and_
from server.models import UserFriend, User

class FriendRepository:
    """封装所有与好友关系 (UserFriend) 表相关的数据库操作"""
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_friend_relationship(self, user_id_1: int, user_id_2: int) -> UserFriend | None:
        """获取两个用户之间的好友关系记录，无论方向或状态。"""
        result = await self._session.execute(
            select(UserFriend).where(
                or_(
                    and_(UserFriend.user_id_a == user_id_1, UserFriend.user_id_b == user_id_2),
                    and_(UserFriend.user_id_a == user_id_2, UserFriend.user_id_b == user_id_1)
                )
            )
        )
        return result.scalars().first()

    async def add_friend_request(self, requester_id: int, target_id: int):
        """添加一条新的好友请求记录。"""
        # 注意：为了简化查询，我们只存一条记录
        # user_id_a 始终是发起者
        new_request = UserFriend(
            user_id_a=requester_id,
            user_id_b=target_id,
            requester_id=requester_id,
            status=0  # 0 表示待处理
        )
        self._session.add(new_request)

    async def list_friends(self, user_id: int) -> list[User]:
        """列出指定用户的所有已确认的好友。"""
        # 查询所有 user_id_a 或 user_id_b 是该用户，且状态为1（已接受）的关系
        result = await self._session.execute(
            select(UserFriend).where(
                or_(UserFriend.user_id_a == user_id, UserFriend.user_id_b == user_id),
                UserFriend.status == 1
            )
        )
        friend_relations = result.scalars().all()
        
        friend_ids = set()
        for rel in friend_relations:
            if rel.user_id_a != user_id:
                friend_ids.add(rel.user_id_a)
            if rel.user_id_b != user_id:
                friend_ids.add(rel.user_id_b)
        
        if not friend_ids:
            return []

        # 一次性查询所有好友的用户信息
        friend_result = await self._session.execute(select(User).where(User.id.in_(friend_ids)))
        return friend_result.scalars().all()
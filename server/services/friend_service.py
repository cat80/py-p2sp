from common.dto import Request, Response
from server.repository.user_repository import UserRepository
from server.repository.friend_repository import FriendRepository
from server.managers.connection_manager import ConnectionManager
from common.protocol import protocol


class FriendService:
    """包含好友相关操作的核心业务逻辑"""
    def __init__(self, connection_manager: ConnectionManager):
        self._connection_manager = connection_manager

    async def add_friend(self, request: Request) -> Response:
        """处理发起好友请求的逻辑"""
        requester = request.user
        target_username = request.payload.get('username')
        session = request.db_session

        if not target_username:
            return Response(is_success=False, message="必须提供要添加的好友用户名。" )

        user_repo = UserRepository(session)
        target_user = await user_repo.get_by_username(target_username)

        if not target_user:
            return Response(is_success=False, message=f"用户 '{target_username}' 不存在。" )

        if requester.id == target_user.id:
            return Response(is_success=False, message="不能添加自己为好友。" )

        friend_repo = FriendRepository(session)
        existing_relation = await friend_repo.get_friend_relationship(requester.id, target_user.id)

        if existing_relation:
            if existing_relation.status == 1:
                return Response(is_success=False, message=f"'{target_username}' 已经是您的好友。" )
            # 检查请求方向
            if existing_relation.requester_id == requester.id:
                return Response(is_success=False, message="您已发送过好友请求，请等待对方同意。" )
            else:
                return Response(is_success=False, message=f"'{target_username}' 已向您发送了好友请求，请使用 'accept_friend {target_username}' 同意。" )

        # 创建新的好友请求
        await friend_repo.add_friend_request(requester.id, target_user.id)

        # 如果对方在线，发送实时通知
        notification_msg = protocol.create_sys_notify(
            f"用户 '{requester.username}' 请求添加您为好友，请使用 'accept_friend {requester.username}' 同意。"
        )
        await self._connection_manager.send_to_user(target_user.id, notification_msg)

        return Response(is_success=True, message="好友请求已发送。" )

    async def accept_friend(self, request: Request) -> Response:
        """处理接受好友请求的逻辑"""
        accepter = request.user
        requester_username = request.payload.get('username')
        session = request.db_session

        if not requester_username:
            return Response(is_success=False, message="必须提供好友的用户名。" )

        user_repo = UserRepository(session)
        requester = await user_repo.get_by_username(requester_username)

        if not requester:
            return Response(is_success=False, message=f"用户 '{requester_username}' 不存在。" )

        friend_repo = FriendRepository(session)
        relation = await friend_repo.get_friend_relationship(accepter.id, requester.id)

        if not relation or relation.status == 1:
            return Response(is_success=False, message=f"来自 '{requester_username}' 的好友请求不存在或已处理。" )

        # 验证请求是否是对方发起的
        if relation.requester_id == accepter.id:
            return Response(is_success=False, message="不能接受自己的好友请求。" )

        relation.status = 1  # 更新状态为“已接受”

        # 如果对方在线，发送实时通知
        notification_msg = protocol.create_sys_notify(f"用户 '{accepter.username}' 已同意您的好友请求。" )
        await self._connection_manager.send_to_user(requester.id, notification_msg)

        return Response(is_success=True, message=f"您已和 '{requester_username}' 成为好友。" )

    async def list_friends(self, request: Request) -> Response:
        """处理查询好友列表的逻辑"""
        user = request.user
        session = request.db_session
        friend_repo = FriendRepository(session)
        
        friends = await friend_repo.list_friends(user.id)
        
        if not friends:
            return Response(is_success=True, message="您的好友列表为空。" )

        friend_list_str = "您的好友列表：\n"
        for friend in friends:
            status = "在线" if self._connection_manager.is_online(friend.id) else "离线"
            friend_list_str += f"- {friend.username} ({status})\n"
            
        return Response(is_success=True, message=friend_list_str)

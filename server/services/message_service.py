from common.dto import Request, Response
from server.repository.user_repository import UserRepository
from server.repository.friend_repository import FriendRepository
from server.repository.message_repository import MessageRepository
from server.managers.connection_manager import ConnectionManager
from common.protocol import protocol

class MessageService:
    """包含消息发送相关的核心业务逻辑"""
    def __init__(self, connection_manager: ConnectionManager):
        self._connection_manager = connection_manager

    async def send_private_message(self, request: Request) -> Response:
        """处理发送私聊消息的逻辑"""
        sender = request.user
        target_username = request.payload.get('username')
        message_text = request.payload.get('message')
        session = request.db_session

        if not target_username or not message_text:
            return Response(is_success=False, message="必须提供接收者用户名和消息内容。")

        user_repo = UserRepository(session)
        target_user = await user_repo.get_by_username(target_username)

        if not target_user:
            return Response(is_success=False, message=f"用户 '{target_username}' 不存在。")

        friend_repo = FriendRepository(session)
        relation = await friend_repo.get_friend_relationship(sender.id, target_user.id)

        if not relation:
            return Response(is_success=False, message=f"'{target_username}' 不是您的好友，请先使用 'add_friend {target_username}' 添加好友。")
        
        if relation.status == 0:
            return Response(is_success=False, message=f"您与 '{target_username}' 的好友请求尚未通过验证，暂时无法发送消息。")

        # 构造要发送的消息体
        message_to_send = protocol.create_client_user_send_message(sender.username, message_text)

        # 检查对方是否在线
        if self._connection_manager.is_online(target_user.id):
            await self._connection_manager.send_to_user(target_user.id, message_to_send)
            # 给发送者一个直接的成功反馈
            feedback_msg = f"你悄悄地对 '{target_username}' 说: {message_text}"
            return Response(is_success=True, message=feedback_msg)
        else:
            # 对方不在线，存储为离线消息
            msg_repo = MessageRepository(session)

            await msg_repo.save_offline_message(target_user.id, message_to_send.hex())
            return Response(is_success=True, message=f"好友 '{target_username}' 当前不在线，消息将作为离线消息发送。")

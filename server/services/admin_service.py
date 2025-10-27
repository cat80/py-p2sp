from common.dto import Request, Response
from server.managers.connection_manager import ConnectionManager
from common.protocol import protocol
from server.repository.user_repository import UserRepository
class AdminService:
    """Contains business logic for administrator-only operations."""
    def __init__(self, connection_manager: ConnectionManager):
        self._connection_manager = connection_manager

    async def broadcast_message(self, request: Request) -> Response:
        """Sends a message to all online users."""
        if not request.user or not request.user.is_admin:
            return Response(is_success=False, message="Permission denied.")

        message = request.payload.get('message')
        if not message:
            return Response(is_success=False, message="Message cannot be empty.")

        broadcast_payload = protocol.create_sys_notify(f"[Broadcast] {message}")
        await self._connection_manager.broadcast(broadcast_payload)

        return Response(is_success=True, message="Broadcast sent.")

    async def ban_user(self, request: Request) -> Response:
        """Bans a user, preventing them from logging in."""
        if not request.user or not request.user.is_admin:
            return Response(is_success=False, message="Permission denied.")

        username_to_ban = request.payload.get('username')
        if not username_to_ban:
            return Response(is_success=False, message="Username is required.")

        repo = UserRepository(request.db_session)
        user_to_ban = await repo.get_by_username(username_to_ban)

        if not user_to_ban:
            return Response(is_success=False, message=f"User '{username_to_ban}' not found.")

        if user_to_ban.is_admin:
            return Response(is_success=False, message="Cannot ban an administrator.")

        user_to_ban.status = 0  # Set status to banned
        
        # If the user is online, kick them
        if self._connection_manager.is_online(user_to_ban.id):
            kick_message = protocol.create_sys_notify("Your account has been banned. You are being disconnected.")
            await self._connection_manager.send_to_user(user_to_ban.id, kick_message)
            # The connection will be closed by the manager if send fails, or we can force it.
            # For simplicity, we'll let the send_to_user handle dead connections.
            self._connection_manager.remove_user(user_to_ban.id)


        return Response(is_success=True, message=f"User '{username_to_ban}' has been banned.")

    async def permit_user(self, request: Request) -> Response:
        # 解禁用户
        if not request.user or not request.user.is_admin:
            return Response(is_success=False, message="无操作权限.")

        username_to_ban = request.payload.get('username')
        if not username_to_ban:
            return Response(is_success=False, message="请输入要禁用的用户。")

        repo = UserRepository(request.db_session)
        user_to_ban = await repo.get_by_username(username_to_ban)

        if not user_to_ban:
            return Response(is_success=False, message=f"用户 '{username_to_ban}' 不存在.")

        user_to_ban.status = 1  # Set status to banned


        return Response(is_success=True, message=f"用户 '{username_to_ban}' 已经解禁，能正常使用.")

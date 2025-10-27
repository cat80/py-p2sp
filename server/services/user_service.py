import logging
from common.dto import Request, Response
from server.repository.user_repository import UserRepository
from server.repository.offline_message_repository import OfflineMessageRepository # Assuming this will be created
from server.models import User, UserLoginLog
from server.managers.connection_manager import ConnectionManager
from server import auth
from common import protocol

class UserService:
    """Contains business logic for user-related operations."""
    def __init__(self, connection_manager: ConnectionManager):
        self._connection_manager = connection_manager

    async def register(self, request: Request) -> Response:
        """Handles new user registration."""
        username = request.payload.get('username')
        password = request.payload.get('password')
        session = request.db_session

        if not username or not password:
            return Response(is_success=False, message="Username and password are required.")

        repo = UserRepository(session)
        if await repo.get_by_username(username):
            return Response(is_success=False, message="Username already exists.")

        salt, password_hash = auth.hash_password(password)
        full_password_hash = f"{salt}:{password_hash}"
        
        new_user = User(
            username=username,
            password_hash=full_password_hash,
            status=1,
            is_admin=False
        )
        await repo.add(new_user)
        
        return Response(is_success=True, message=f"User '{username}' registered successfully.")

    async def login(self, request: Request) -> Response:
        """Handles user login, session management, and offline message delivery."""
        username = request.payload.get('username')
        password = request.payload.get('password')
        session = request.db_session

        if not username or not password:
            return Response(is_success=False, message="Username and password are required.")

        user_repo = UserRepository(session)
        user = await user_repo.get_by_username(username)

        if not user:
            return Response(is_success=False, message="Invalid username or password.")

        try:
            salt, stored_hash = user.password_hash.split(':')
        except ValueError:
            logging.error(f"Password hash for user '{username}' is malformed.")
            return Response(is_success=False, message="Server error: authentication data is corrupt.")

        if not auth.verify_password(stored_hash, salt, password):
            return Response(is_success=False, message="Invalid username or password.")
        
        if user.status == 0:
            return Response(is_success=False, message="This user account is banned.")

        # --- Login successful ---
        auth_token = auth.generate_auth_token()
        user.auth_token = auth_token
        
        login_ip = request.writer_info.get('peername', ('unknown',))[0]
        login_log = UserLoginLog(user_id=user.id, username=user.username, login_ip=login_ip)
        session.add(login_log)
        
        # Add user to the connection manager
        self._connection_manager.add_user(user.id, request.writer)
        
        # Fetch and deliver offline messages
        offline_repo = OfflineMessageRepository(session)
        offline_messages = await offline_repo.get_for_user(user.id)
        for msg in offline_messages:
            await self._connection_manager.send_to_user(user.id, bytes.fromhex(msg.message_payload))
            await offline_repo.delete(msg)

        return Response(
            is_success=True,
            message=f"Welcome, {username}!",
            response_type='login_success',
            data={
                'message': f"Welcome, {username}!",
                'auth_token': auth_token,
                'is_admin': user.is_admin,
                'user_id': user.id
            }
        )
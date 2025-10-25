import logging
from typing import TYPE_CHECKING

from common.dto import Request, Response
from common.protocol import protocol
from server.db.session import get_session
from server.repository.user_repository import UserRepository
from server.services.user_service import UserService
from server.services.friend_service import FriendService
from server.services.message_service import MessageService
from server.services.admin_service import AdminService
from server.managers.connection_manager import ConnectionManager


if TYPE_CHECKING:
    from server.server import ChatServer

class CommandNotFoundError(Exception):
    pass

class ServerMessageHandler:
    def __init__(
        self, 
        server: "ChatServer", 
        user_service: UserService, 
        friend_service: FriendService,
        message_service: MessageService,
        admin_service: AdminService,
        connection_manager: ConnectionManager
    ):
        self.server = server
        self._user_service = user_service
        self._friend_service = friend_service
        self._message_service = message_service
        self._admin_service = admin_service
        self.connection_manager = connection_manager
        
        # Command map routes all message types to the appropriate service methods
        self.command_map = {
            # User Service
            'login': self._user_service.login,
            'reg': self._user_service.register,
            # Friend Service
            'add_friend': self._friend_service.add_friend,
            'accept_friend': self._friend_service.accept_friend,
            'myfriends': self._friend_service.list_friends,
            # Message Service
            'send': self._message_service.send_private_message,
            # Admin Service
            'broadcast': self._admin_service.broadcast_message,
            'ban_user': self._admin_service.ban_user,
        }

    async def handle_message(self, writer, message: dict):
        """
        Acts as a central dispatcher for all incoming messages.
        Orchestrates the request lifecycle: session -> request -> service -> response -> network message.
        """
        msg_type = message.get('type')
        payload = message.get('payload', {})
        
        logged_in_user_id = None

        async with get_session() as session:
            try:
                # 1. Find the service method from the command map
                service_method = self.command_map.get(msg_type)
                if not service_method:
                    raise CommandNotFoundError(f"Unknown command: {msg_type}")

                # 2. Authenticate user for non-auth commands
                user = None
                auth_token = payload.get('auth_token')
                user_repo = UserRepository(session)
                user = await user_repo.get_by_token(auth_token)

                if msg_type not in ['login', 'reg']:
                    if not user:
                        raise PermissionError("Authentication required.")
                    if user.status == 0:
                        raise PermissionError("User is banned.")

                # 3. Encapsulate all request data into a single object
                request = Request(
                    user=user,
                    payload=payload,
                    writer_info={'peername': writer.get_extra_info('peername')},
                    db_session=session,
                    writer=writer
                )

                # 4. Call the service method
                response: Response = await service_method(request)

                # 5. Process the response object
                if response.is_success:
                    # Use the response_type from the Response DTO to build the payload
                    network_message = protocol.create_payload(
                        response.response_type, 
                        response.data or {'message': response.message}
                    )
                    
                    if msg_type == 'login':
                        logged_in_user_id = response.data['user_id']
                else:
                    # Generic failure message
                    network_message = protocol.create_normal_message(response.message)

            except CommandNotFoundError as e:
                network_message = protocol.create_normal_message(str(e))
            except PermissionError as e:
                network_message = protocol.create_normal_message(str(e))
            except Exception as e:
                logging.exception(f"An unexpected error occurred while handling '{msg_type}'")
                network_message = protocol.create_normal_message(f"Server error: An internal error occurred.")

        # 6. Send the response to the client
        writer.write(network_message)
        await writer.drain()
        
        return logged_in_user_id
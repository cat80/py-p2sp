import asyncio
import logging
from server.db.session import create_db_and_tables, close_engine
from common.protocol import AsyncProtocol
from server.handler import ServerMessageHandler
from server.services.user_service import UserService
from server.services.friend_service import FriendService
from server.services.message_service import MessageService
from server.services.admin_service import AdminService
from server.managers.connection_manager import ConnectionManager

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class ChatServer:
    def __init__(self, host='127.0.0.1', port=8888):
        self.host = host
        self.port = port
        self.server = None
        
        # 1. Instantiate Managers and Services, injecting dependencies
        connection_manager = ConnectionManager()
        user_service = UserService(connection_manager)
        friend_service = FriendService(connection_manager)
        message_service = MessageService(connection_manager)
        admin_service = AdminService(connection_manager)
        
        # 2. Inject all dependencies into the handler
        self.handler = ServerMessageHandler(
            self, 
            user_service, 
            friend_service,
            message_service,
            admin_service,
            connection_manager
        )

    async def handle_client(self, reader, writer):
        addr = writer.get_extra_info('peername')
        logging.info(f"New connection from {addr}")
        buffer = b''
        user_id = None

        try:
            while True:
                message, buffer = await AsyncProtocol.deserialize_stream(reader, buffer)
                if message is None:
                    break
                
                # The handler now returns the user_id upon a successful login
                logged_in_user_id = await self.handler.handle_message(writer, message)
                if logged_in_user_id:
                    user_id = logged_in_user_id

        except asyncio.CancelledError:
            logging.info(f"Connection from {addr} cancelled.")
        except Exception as e:
            logging.error(f"An error occurred with {addr}: {e}")
        finally:
            logging.info(f"Connection from {addr} closed.")
            if user_id:
                self.handler.connection_manager.remove_user(user_id)
            writer.close()
            await writer.wait_closed()

    async def start(self):
        self.server = await asyncio.start_server(
            self.handle_client, self.host, self.port)

        addr = self.server.sockets[0].getsockname()
        logging.info(f'Serving on {addr}')

        async with self.server:
            await self.server.serve_forever()

import asyncio
import logging
from server.db import create_db_and_tables, close_engine
from common.protocol import AsyncProtocol
from server.handler import ServerMessageHandler

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class ChatServer:
    def __init__(self, host='127.0.0.1', port=8888):
        self.host = host
        self.port = port
        self.server = None
        self.online_users = {}
        self.handler = ServerMessageHandler(self)

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
                await self.handler.handle_message(writer, message)

        except asyncio.CancelledError:
            logging.info(f"Connection from {addr} cancelled.")
        except Exception as e:
            logging.error(f"An error occurred with {addr}: {e}")
        finally:
            logging.info(f"Connection from {addr} closed.")
            if user_id and user_id in self.online_users:
                del self.online_users[user_id]
            writer.close()
            await writer.wait_closed()

    async def start(self):
        self.server = await asyncio.start_server(
            self.handle_client, self.host, self.port)

        addr = self.server.sockets[0].getsockname()
        logging.info(f'Serving on {addr}')

        async with self.server:
            await self.server.serve_forever()

async def main():
    await create_db_and_tables()
    server = ChatServer()
    try:
        await server.start()
    finally:
        await close_engine()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Server is shutting down.")

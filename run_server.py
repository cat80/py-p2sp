import asyncio
import logging
from server.db.session import create_db_and_tables, close_engine
from server.server import  ChatServer
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

async def main():
    port = 18888
    await create_db_and_tables()
    server = ChatServer(port=port)
    try:
        await server.start()
    finally:
        await close_engine()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Server is shutting down.")

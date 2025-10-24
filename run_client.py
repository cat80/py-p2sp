import asyncio
import logging
from client.client import ChatClient
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

async def main():
    client = ChatClient(port='18888')
    await client.start()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Client is shutting down.")
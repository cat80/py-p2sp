import asyncio
import logging
import sys
from common.protocol import AsyncProtocol
from client.handler import ClientMessageHandler

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class ChatClient:
    def __init__(self, host='127.0.0.1', port=8888):
        self.host = host
        self.port = port
        self.reader = None
        self.writer = None
        self.handler = ClientMessageHandler(self)
        self.auth_token = None

    async def connect(self):
        try:
            self.reader, self.writer = await asyncio.open_connection(self.host, self.port)
            logging.info(f"Connected to server at {self.host}:{self.port}")
            return True
        except ConnectionRefusedError:
            logging.error("Connection refused. Is the server running?")
            return False
        except Exception as e:
            logging.error(f"Failed to connect to server: {e}")
            return False

    async def listen_for_messages(self):
        buffer = b''
        while True:
            try:
                # 从协议中解析数据
                message, buffer = await AsyncProtocol.deserialize_stream(self.reader, buffer)
                if message is None:
                    logging.info("Server closed the connection.")
                    break
                await self.handler.handle_message(message)
            except Exception as e:
                logging.error(f"Error receiving message: {e}")
                break
        await self.close()

    async def send_message(self, message: bytes):
        if self.writer:
            self.writer.write(message)
            await self.writer.drain()

    async def handle_user_input(self):
        loop = asyncio.get_running_loop()
        while True:
            line = await loop.run_in_executor(None, sys.stdin.readline)
            command_line = line.strip()
            if not command_line:
                continue

            parts = command_line.split()
            command = parts[0]

            if command == 'exit':
                break
            
            if command == 'reg':
                if len(parts) != 3:
                    print("Usage: reg <username> <password>")
                    continue
                _, username, password = parts
                reg_message = AsyncProtocol.create_payload('reg', {'username': username, 'password': password})
                await self.send_message(reg_message)
            elif command == 'login':
                if len(parts) != 3:
                    print("Usage: login <username> <password>")
                    continue
                _, username, password = parts
                login_message = AsyncProtocol.create_payload('login', {'username': username, 'password': password})
                await self.send_message(login_message)
            elif command == 'add_friend':
                if not self.auth_token:
                    print("请先登录。")
                    continue
                if len(parts) != 2:
                    print("用法: add_friend <username>")
                    continue
                username = parts[1]
                payload = {'auth_token': self.auth_token, 'username': username}
                await self.send_message(AsyncProtocol.create_payload('add_friend', payload))

            elif command == 'accept_friend':
                if not self.auth_token:
                    print("请先登录。")
                    continue
                if len(parts) != 2:
                    print("用法: accept_friend <username>")
                    continue
                username = parts[1]
                payload = {'auth_token': self.auth_token, 'username': username}
                await self.send_message(AsyncProtocol.create_payload('accept_friend', payload))

            elif command == 'myfriends':
                if not self.auth_token:
                    print("请先登录。")
                    continue
                payload = {'auth_token': self.auth_token}
                await self.send_message(AsyncProtocol.create_payload('myfriends', payload))

            elif command == 'send':
                if not self.auth_token:
                    print("请先登录。")
                    continue
                if len(parts) < 3:
                    print("用法: send <username> <message>")
                    continue
                recipient = parts[1]
                message_text = " ".join(parts[2:])
                payload = {
                    'auth_token': self.auth_token,
                    'username': recipient,
                    'message': message_text
                }
                await self.send_message(AsyncProtocol.create_payload('send', payload))

            elif command == 'logout':
                if not self.auth_token:
                    print("您当前未登录。")
                    continue
                logout_payload = {'auth_token': self.auth_token}
                logout_message = AsyncProtocol.create_payload('logout', logout_payload)
                await self.send_message(logout_message)
                self.auth_token = None
                print("您已成功登出。")
            
            else:
                print(f"未知命令: {command}")

    async def start(self):
        if not await self.connect():
            return

        listener_task = asyncio.create_task(self.listen_for_messages())
        input_task = asyncio.create_task(self.handle_user_input())

        await asyncio.gather(listener_task, input_task)

    async def close(self):
        if self.writer:
            self.writer.close()
            await self.writer.wait_closed()
            logging.info("Connection closed.")

async def main():
    client = ChatClient()
    await client.start()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Client is shutting down.")

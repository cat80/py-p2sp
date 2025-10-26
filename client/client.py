import asyncio
import logging
import sys
import time
from common.protocol import AsyncProtocol
from client.handler import ClientMessageHandler

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

CMD_MAP = {
    'reg': ['username', 'password'],
    'login': ['username', 'password'],
    'add_friend': ['username'],
    'accept_friend': ['username'],
    'myfriends': [],
    'send': ['username', 'message'],
    'broadcast': ['message'],
    'ban_user': ['username'],
    'permit_user': ['username'],
    'logout': [],
}

class ChatClient:
    def __init__(self, host='127.0.0.1', port=8888, reconnect_delay=5):
        self.host = host
        self.port = port
        self.reader = None
        self.writer = None
        self.handler = ClientMessageHandler(self)
        self.auth_token = None
        self.is_admin = False
        self._is_connected = False
        self._reconnect_delay = reconnect_delay
        self._listener_task = None

    async def connect(self):
        """Tries to connect to the server with retries."""
        logging.info(f"正在连接到服务器 {self.host}:{self.port}...")
        for attempt in range(3):
            try:
                self.reader, self.writer = await asyncio.open_connection(self.host, self.port)
                self._is_connected = True
                logging.info("成功连接到服务器。")
                # Start the message listener upon successful connection
                if self._listener_task:
                    self._listener_task.cancel()
                self._listener_task = asyncio.create_task(self.listen_for_messages())
                return True
            except ConnectionRefusedError:
                logging.warning(f"连接被拒绝。将在 {self._reconnect_delay} 秒后重试... ({attempt + 1}/3)")
                await asyncio.sleep(self._reconnect_delay)
            except Exception as e:
                logging.error(f"连接失败: {e}。将在 {self._reconnect_delay} 秒后重试... ({attempt + 1}/3)")
                await asyncio.sleep(self._reconnect_delay)
        
        logging.error("无法连接到服务器。请检查服务器地址或网络连接。")
        return False

    async def listen_for_messages(self):
        """Listens for incoming messages and handles disconnection."""
        buffer = b''
        while self._is_connected:
            try:
                message, buffer = await AsyncProtocol.deserialize_stream(self.reader, buffer)
                if message is None:
                    raise ConnectionError("服务器关闭了连接。")
                await self.handler.handle_message(message)
            except (ConnectionError, asyncio.IncompleteReadError) as e:
                logging.warning(f"与服务器的连接已断开: {e}")
                self._is_connected = False
                self.writer.close()
                await self.writer.wait_closed()
                self.writer = None
                self.reader = None
                # Do not attempt to reconnect here, let the next user action trigger it.
                print("\n[系统提示] 与服务器断开连接。下次发送消息时将尝试自动重连。")
                break # Exit the listening loop
            except Exception as e:
                logging.error(f"接收消息时发生未知错误: {e}")
                self._is_connected = False # Assume connection is dead
                break


    async def send_message(self, message: bytes):
        """Ensures connection is active before sending, attempts reconnect if not."""
        if not self._is_connected:
            print("[系统提示] 连接已断开，正在尝试重新连接...")
            if not await self.connect():
                print("[系统提示] 重连失败。请稍后再试。")
                return False
        
        try:
            self.writer.write(message)
            await self.writer.drain()
            return True
        except ConnectionError as e:
            logging.error(f"发送消息失败: {e}")
            self._is_connected = False
            return False

    async def handle_user_input(self):
        """Generic command processor driven by CMD_MAP."""
        loop = asyncio.get_running_loop()
        while True:
            line = await loop.run_in_executor(None, sys.stdin.readline)
            command_line = line.strip()
            if not command_line:
                continue

            parts = command_line.split()
            command = parts[0].lower()

            if command == 'exit':
                break

            if command not in ['login', 'reg'] and not self.auth_token:
                print("此操作需要登录，请先使用 'login' 命令登录。")
                continue

            if command not in CMD_MAP:
                print(f"未知命令: '{command}'")
                continue

            param_names = CMD_MAP[command]
            num_expected_params = len(param_names)
            user_params = parts[1:]

            if len(user_params) < num_expected_params:
                usage = f"用法: {command} " + " ".join([f"<{p}>" for p in param_names])
                print(usage)
                continue

            payload = {'auth_token': self.auth_token}
            if num_expected_params > 0:
                # Assign first N-1 parameters
                for i in range(num_expected_params - 1):
                    payload[param_names[i]] = user_params[i]
                # Assign the rest to the last parameter
                payload[param_names[-1]] = " ".join(user_params[num_expected_params - 1:])
            
            if not await self.send_message(AsyncProtocol.create_payload(command, payload)):
                continue # Don't proceed if sending failed

            if command == 'logout':
                self.auth_token = None
                self.is_admin = False
                print("您已成功登出。")

    async def start(self):
        if not await self.connect():
            # Even if initial connection fails, we start the input loop
            # so the user can try commands that will trigger reconnects.
            pass
            
        await self.handle_user_input()

    async def close(self):
        if self.writer:
            self.writer.close()
            await self.writer.wait_closed()
        if self._listener_task:
            self._listener_task.cancel()
        logging.info("客户端已关闭。")

async def main():
    client = ChatClient()
    try:
        await client.start()
    finally:
        await client.close()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("客户端正在关闭。")

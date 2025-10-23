from __future__ import annotations
from typing import TYPE_CHECKING
from common.protocol import protocol

if TYPE_CHECKING: # 避免循环引用问题
    from client.client import ChatClient


class ClientMessageHandler:
    def __init__(self, client: ChatClient):
        self.client = client

    async def handle_message(self, message: dict):
        """
        Process incoming messages from the server.
        """
        msg_type = message.get('type')
        
        # 动态获取处理方法.考虑到方法比较多，需要分层处理
        handler_method = getattr(self, f"handle_{msg_type}", self.handle_unknown_message)
        await handler_method(message)

    async def handle_login_success(self, message: dict):
        payload = message.get('payload', {})
        self.client.auth_token = payload.get('auth_token')
        print(f"[Server]: {payload.get('message')}")

    async def handle_normalmsg(self, message: dict):
        payload = message.get('payload', {})
        print(f"[Server]: {payload.get('message')}")

    async def handle_usersend(self, message: dict):
        print(protocol.show_user_msg(message))

    async def handle_sysmsg(self, message: dict):
        print(protocol.show_user_msg(message))

    async def handle_unknown_message(self, message: dict):
        print(f"Unknown message type from server: {message}")

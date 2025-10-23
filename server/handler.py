from __future__ import annotations
from typing import TYPE_CHECKING
from sqlalchemy.future import select
from server import auth
from server.db import AsyncSessionFactory
from server.models import User, UserFriend, Group, GroupMember
from common.protocol import protocol
from server.services.user_services import UserServices
if TYPE_CHECKING:
    from server.server import ChatServer


class ServerMessageHandler:
    def __init__(self, server: ChatServer):
        self.server = server
        # 流入当前的服务对象
        self.user_service = UserServices(server)

    async def handle_message(self, writer, message: dict):
        """
        Process incoming messages from clients.
        """
        msg_type = message.get('type')
        payload = message.get('payload')
        auth_token = payload.get('auth_token')

        async with AsyncSessionFactory() as session:
            user = await auth.get_user_by_token(session, auth_token)
            if not user and msg_type not in ['login', 'reg']:
                response = protocol.create_normal_message("Authentication required.")
                writer.write(response)
                await writer.drain()
                return

            handler_method = getattr(self, f"handle_{msg_type}", self.handle_unknown_message)
            await handler_method(writer, user, payload)

    async def handle_send(self, writer, user, payload: dict):
        recipient_username = payload.get('to_user')
        message_text = payload.get('message')

        if not recipient_username or not message_text:
            response = protocol.create_normal_message("Recipient and message are required.")
            writer.write(response)
            await writer.drain()
            return

        async with AsyncSessionFactory() as session:
            result = await session.execute(select(User).where(User.username == recipient_username))
            recipient = result.scalars().first()

            if not recipient:
                response = protocol.create_normal_message(f"User '{recipient_username}' not found.")
                writer.write(response)
                await writer.drain()
                return

            if recipient.id not in self.server.online_users:
                response = protocol.create_normal_message(f"User '{recipient_username}' is offline.")
                writer.write(response)
                await writer.drain()
                return

            recipient_writer = self.server.online_users[recipient.id]
            message_to_send = protocol.create_client_user_send_message(user.username, message_text)
            recipient_writer.write(message_to_send)
            await recipient_writer.drain()

    async def handle_logout(self, writer, user, payload: dict):
        if user:
            async with AsyncSessionFactory() as session:
                user.auth_token = None
                await session.commit()
            
            if user.id in self.server.online_users:
                del self.server.online_users[user.id]

        response = protocol.create_normal_message("You have been logged out.")
        writer.write(response)
        await writer.drain()

    async def write_message_with_drain(self,writer,payload,msg_type=None):
        if not isinstance(payload, (bytes,bytearray)):
            if  msg_type:
                payload = protocol.create_payload( msg_type, payload)
            else:
                payload =  protocol.create_normal_message(message=payload)
        writer.write(payload)
        await writer.drain()

    async def handle_unknown_message(self, writer, user, payload: dict):
        print(f"Unknown message type: {payload}")
        await self.write_message_with_drain(writer,'未知的命令')


    async def handle_login(self, writer, user, payload: dict):

        username = payload.get('username')
        password = payload.get('password')
        loginip = writer.get_extra_info('peername')[0] if writer.get_extra_info('peername') else ''
        login_ret,user =await self.user_service.login(username, password,loginip)
        if login_ret:
            self.server.online_users[user.id] = writer
            response_payload = {
                'message': f"欢迎, {username}!",
                'auth_token': user.auth_token,
                'is_admin': user.is_admin
            }
            await self.write_message_with_drain(writer,response_payload,'login_success')
        else:
            await self.write_message_with_drain(writer,protocol.create_sys_notify(user))


    async def handle_reg(self, writer, user, payload: dict):
        username = payload.get('username')
        password = payload.get('password')
        if not username or not password:
            response = protocol.create_normal_message("Username and password are required.")
            writer.write(response)
            await writer.drain()
            return

        async with AsyncSessionFactory() as session:
            async with session.begin():
                # Check if user already exists
                result = await session.execute(select(User).where(User.username == username))
                existing_user = result.scalars().first()
                
                if existing_user:
                    response = protocol.create_normal_message("Username already exists.")
                    writer.write(response)
                    await writer.drain()
                    return

                # Hash the password
                salt, password_hash = auth.hash_password(password)
                full_password_hash = f"{salt}:{password_hash}"
                
                # Create new user
                new_user = User(
                    username=username,
                    password_hash=full_password_hash,
                    status=1,  # Active
                    is_admin=False  # Regular user by default
                )
                
                session.add(new_user)
                await session.commit()
                
                response = protocol.create_normal_message(f"User '{username}' registered successfully.")
                writer.write(response)
                await writer.drain()

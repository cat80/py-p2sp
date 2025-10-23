from   typing import TYPE_CHECKING
from ..db import AsyncSessionFactory
from ..models import User,UserLoginLog
from server import auth
from sqlalchemy.future import select

class UserServices():

    def __init__(self,server=None,async_db_factory=None):
        pass
        self.async_db_factory = async_db_factory if async_db_factory else AsyncSessionFactory
        # self.server = server

    async def login(self,username,password,loginip=''):
        """
            处理登陆
        :return:
        """
        if not username or not password:
            return False,'用户名密码不能为空'
        async with AsyncSessionFactory() as session:
            async with session.begin():
                result = await session.execute(select(User).where(User.username == username))
                user = result.scalars().first()
                if not user:
                    return False,'用户名或密码错误'

                try:
                    salt, stored_hash = user.password_hash.split(':')
                except ValueError:
                    return False,'用户密码格式错误'
                if not auth.verify_password(stored_hash, salt, password):
                    return False,'用户名或密码错误！'
                if user.status == 0:
                    return False, '用户已经被禁用，请联系管理！'
                auth_token = auth.generate_auth_token()
                user.auth_token = auth_token
                # 这里增加登陆日志
                log = UserLoginLog()
                log.user_id = user.id
                log.username = user.username
                log.login_ip = loginip #登陆ip
                session.add(log)
                await session.commit()
                return  True,user

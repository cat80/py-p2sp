from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from server.models import User

class UserRepository:
    """
    Handles data access for the User model.
    It is initialized with a session for each request.
    """
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_username(self, username: str) -> User | None:
        """Retrieves a user by their username."""
        result = await self._session.execute(select(User).where(User.username == username))
        return result.scalars().first()

    async def add(self, user: User):
        """Adds a new user to the session."""
        self._session.add(user)

    async def get_by_token(self, token: str) -> User | None:
        """Retrieves a user by their auth token."""
        if not token:
            return None
        result = await self._session.execute(select(User).where(User.auth_token == token))
        return result.scalars().first()

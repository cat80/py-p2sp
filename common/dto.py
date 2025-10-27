from dataclasses import dataclass, field
from typing import Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
import asyncio

# Forward declaration to avoid circular imports
class User:
    pass

@dataclass
class Request:
    """Encapsulates all context for a single request."""
    user: Optional[User]
    payload: dict
    db_session: AsyncSession
    writer: asyncio.StreamWriter
    writer_info: dict = field(default_factory=dict)

@dataclass
class Response:
    """Standardized service output object."""
    is_success: bool
    message: str
    response_type: str = 'normalmsg'
    data: Any = None

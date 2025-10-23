from dataclasses import dataclass
from typing import Any, Optional

@dataclass
class RequestMessage:
    """
    Represents a request message sent from a client to the server.
    """
    auth_token: Optional[str]
    payload: Any

@dataclass
class ResponseMessage:
    """
    Represents a response message sent from the server to a client.
    """
    status_code: int  # e.g., 200 for OK, 400 for Bad Request, etc.
    data: Any

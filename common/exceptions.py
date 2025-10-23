class ChatException(Exception):
    """Base exception class for the chat application."""
    pass

class AuthenticationError(ChatException):
    """Raised when authentication fails."""
    pass

class NotFriendsError(ChatException):
    """Raised when trying to send a message to a user who is not a friend."""
    pass

class UserNotFoundError(ChatException):
    """Raised when a user is not found."""
    pass

class GroupNotFoundError(ChatException):
    """Raised when a group is not found."""
    pass

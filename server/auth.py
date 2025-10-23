import hashlib
import secrets
from sqlalchemy.future import select
from server.models import User

def hash_password(password: str, salt: str = None) -> (str, str):
    """Hashes a password with a salt. If no salt is provided, a new one is generated."""
    if salt is None:
        salt = secrets.token_hex(16)
    
    # Convert salt to bytes
    salt_bytes = salt.encode('utf-8')
    
    # Use pbkdf2_hmac for secure password hashing
    password_hash = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt_bytes,
        100000  # Recommended number of iterations
    )
    
    # Return the salt and the hex representation of the hash
    return salt, password_hash.hex()

def verify_password(stored_password_hash: str, salt: str, provided_password: str) -> bool:
    """Verifies a provided password against a stored hash and salt."""
    # Hash the provided password with the stored salt
    _, provided_password_hash = hash_password(provided_password, salt)
    
    # Compare the generated hash with the stored hash
    return provided_password_hash == stored_password_hash

def generate_auth_token() -> str:
    """Generates a secure, random authentication token."""
    return secrets.token_urlsafe(32)

async def get_user_by_token(session, token: str) -> User | None:
    """Retrieves a user from the database based on their authentication token."""
    if not token:
        return None
    result = await session.execute(select(User).where(User.auth_token == token))
    return result.scalars().first()

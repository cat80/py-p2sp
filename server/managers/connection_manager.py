import asyncio
import logging
from typing import Dict

class ConnectionManager:
    """
    Manages all active client connections.
    This class is the single source of truth for who is online.
    """
    def __init__(self):
        # Maps user_id to their StreamWriter object
        self.online_users: Dict[int, asyncio.StreamWriter] = {}

    def add_user(self, user_id: int, writer: asyncio.StreamWriter):
        """Adds a user's connection to the manager upon successful login."""
        self.online_users[user_id] = writer
        logging.info(f"User {user_id} connected. Total online: {len(self.online_users)}")

    def remove_user(self, user_id: int):
        """Removes a user's connection when they disconnect."""
        if user_id in self.online_users:
            del self.online_users[user_id]
            logging.info(f"User {user_id} disconnected. Total online: {len(self.online_users)}")

    def is_online(self, user_id: int) -> bool:
        """Checks if a user is currently online."""
        return user_id in self.online_users

    async def send_to_user(self, user_id: int, message: bytes):
        """
        Sends a message to a specific user.
        Handles connection errors gracefully by removing the dead connection.
        """
        writer = self.online_users.get(user_id)
        if writer:
            try:
                writer.write(message)
                await writer.drain()
            except (ConnectionResetError, BrokenPipeError) as e:
                logging.warning(f"Connection error for user {user_id}: {e}. Removing connection.")
                self.remove_user(user_id)
        else:
            # This is not an error, the user is just offline.
            # The service layer will handle saving offline messages.
            pass

    async def broadcast(self, message: bytes):
        """Broadcasts a message to all currently connected users."""
        if not self.online_users:
            return
        
        # Create a list of tasks to send messages concurrently
        tasks = [self.send_to_user(user_id, message) for user_id in self.online_users.keys()]
        await asyncio.gather(*tasks, return_exceptions=True) # Use return_exceptions to prevent one failure from stopping all

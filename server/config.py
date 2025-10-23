import os

# Get the absolute path of the project's root directory
# This is done by taking the directory of the current file (config.py) and going up one level
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Define the database file path relative to the project root
DB_NAME = 'chat_server.db'
# Construct the full, absolute path for the database file
DATABASE_FILE = os.path.join(BASE_DIR, DB_NAME)

# SQLAlchemy database URL for SQLite
# The `sqlite+aiosqlite:///` prefix indicates the use of the aiosqlite driver for async operations
SQLALCHEMY_DATABASE_URL = f"sqlite+aiosqlite:///{DATABASE_FILE}"

import os

POSTGRES_HOST = os.getenv("POSTGRES_HOST")
DB_STRING = "postgresql+asyncpg://intis:intis@localhost:5432/apartments"
TOKEN_SECRET = "fd1b7507705d349a2d1644e5c4b7403cb3ce9dfecc63dd074d0cac5a8317c268"
TOKEN_EXPIRATION = str(60 * 24 * 7)  # one week

# for important variables. from system environment variables or .env file
from pydantic import BaseSettings

# model that would include passwords, usernames, etc.
class Settings(BaseSettings):
    database_hostname: str
    database_port: str
    database_password: str
    database_name: str
    database_username: str
    secret_key: str
    algorithm: str
    access_token_expire_minutes: int
    # gets them from .env file
    class Config:
        env_file = ".env"

# would return the settings from .env file to user
settings = Settings()

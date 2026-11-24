from pydantic_settings import BaseSettings
import os

class Settings:
    MONGODB_URI: str = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    DB_NAME: str = os.getenv("DB_NAME", "tishrei_entry_db")
    APP_ENV: str = os.getenv("APP_ENV", "development")

settings = Settings()

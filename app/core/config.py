from pydantic_settings import BaseSettings
from typing import List
import os

# Set the service account key for Google Cloud using the relative path
# Ensure the relative path is accurate based on the current folder structure.
service_account_path = os.path.join(os.path.dirname(__file__), "../../credentials/damg7245-project2-1daeb31ccdee.json")

# Set the Google Cloud credentials path
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = service_account_path

class Settings(BaseSettings):
    PROJECT_NAME: str
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    BIGQUERY_PROJECT_ID: str
    BIGQUERY_DATASET: str
    ADOBE_API_KEY: str
    REDIS_HOST: str
    REDIS_PORT: int
    ALLOWED_ORIGINS: List[str]
    USE_ADOBE: bool
    GOOGLE_APPLICATION_CREDENTIALS: str  # Add this to the Settings class
    OPENAI_API_KEY: str
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

# Initialize settings
settings = Settings(GOOGLE_APPLICATION_CREDENTIALS=service_account_path)

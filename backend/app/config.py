import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Monitoring Domain API"
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://monitoring_user:monitoring_pass@localhost:5432/monitoring_db")
    PROMETHEUS_URL: str = os.getenv("PROMETHEUS_URL", "http://localhost:9090")
    JWT_SECRET: str = os.getenv("JWT_SECRET", "super_secret_key_change_me_in_production")
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 # 1 day
    TARGETS_FILE_PATH: str = os.getenv("TARGETS_FILE_PATH", "/shared_targets/websites.yml")

settings = Settings()

from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str = "sqlite:///./flowshield.db"
    secret_key: str = "supersecretkeythatshouldbechangedinproduction"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440 # 24 hours

    class Config:
        env_file = ".env"

settings = Settings()

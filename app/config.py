from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "sqlite:///./actionloop.db"
    ollama_host: str = "http://localhost:11434"
    ollama_model: str = "llama3"
    whisper_model_size: str = "base"
    reports_dir: str = "reports"

    class Config:
        env_file = ".env"


settings = Settings()

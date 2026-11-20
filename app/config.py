from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # LLM Configuration
    llm_provider: str = "gemini"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.0-flash"
    
    # Crawler and Security Limits
    request_timeout_seconds: float = 15.0
    max_pages: int = 5
    max_content_chars: int = 24000
    max_response_bytes: int = 2 * 1024 * 1024  # 2MB safety threshold per page
    max_redirects: int = 5

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()

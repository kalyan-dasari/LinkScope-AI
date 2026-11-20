from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # LLM Configuration
    llm_provider: str = "gemini"  # "gemini" or "groq"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.0-flash"
    
    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"
    
    # Crawler and Security Limits
    request_timeout_seconds: float = 15.0
    max_pages: int = 5
    max_content_chars: int = 24000
    max_response_bytes: int = 2 * 1024 * 1024  # 2MB safety threshold per page
    max_redirects: int = 5

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def active_model(self) -> str:
        if self.active_provider == "groq":
            return self.groq_model
        return self.gemini_model

    @property
    def active_provider(self) -> str:
        provider = self.llm_provider.lower().strip()
        # Auto-detect Groq if Groq key is set and Gemini is not
        if (not self.gemini_api_key or self.gemini_api_key == "replace_with_your_key") and self.groq_api_key:
            return "groq"
        return provider

settings = Settings()

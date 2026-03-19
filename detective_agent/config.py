from pydantic_settings import BaseSettings, SettingsConfigDict
from .prompts import DEFAULT_SYSTEM_PROMPT

class Settings(BaseSettings):
    llm_base_url: str = "http://localhost:1234/v1"
    llm_model: str = "local-model"
    system_prompt: str = DEFAULT_SYSTEM_PROMPT
    max_context_tokens: int = 4096
    
    # Allows environment variables like DETECTIVE_SYSTEM_PROMPT to override
    model_config = SettingsConfigDict(env_prefix="detective_")

settings = Settings()

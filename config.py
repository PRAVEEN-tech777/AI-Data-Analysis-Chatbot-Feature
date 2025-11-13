"""
Configuration Management Module


Centralized configuration for the AI-powered database view generator.
Supports environment variables and provides sensible defaults.
"""


import os
from typing import Optional
from pydantic import BaseModel, Field




class DatabaseConfig(BaseModel):
    """Database connection configuration"""
    host: str = Field(default_factory=lambda: os.getenv("DB_HOST", ""))
    port: int = Field(default_factory=lambda: int(os.getenv("DB_PORT", "")))
    dbname: str = Field(default_factory=lambda: os.getenv("DB_NAME", ""))
    user: str = Field(default_factory=lambda: os.getenv("DB_USER", ""))
    password: str = Field(default_factory=lambda: os.getenv("DB_PASSWORD", ""))




class LLMConfig(BaseModel):
    """LLM provider configuration"""
    provider: str = Field(default_factory=lambda: os.getenv("LLM_PROVIDER", "ollama"))
   
    # Ollama settings
    ollama_url: str = Field(default_factory=lambda: os.getenv("OLLAMA_URL", ""))
    ollama_model: str = Field(default_factory=lambda: os.getenv("OLLAMA_MODEL", ""))
    ollama_timeout: int = Field(default_factory=lambda: int(os.getenv("OLLAMA_TIMEOUT", "180")))
   
    # LiteLLM settings
    litellm_model: str = Field(default_factory=lambda: os.getenv("LITELLM_MODEL", "claude-sonnet-4-20250514"))
   
    # API Keys (for LiteLLM providers)
    openai_api_key: Optional[str] = Field(default_factory=lambda: os.getenv("OPENAI_API_KEY"))
    anthropic_api_key: Optional[str] = Field(default_factory=lambda: os.getenv("ANTHROPIC_API_KEY"))
   
    # Generation settings
    temperature: float = Field(default_factory=lambda: float(os.getenv("LLM_TEMPERATURE", "0.0")))
    max_retries: int = Field(default_factory=lambda: int(os.getenv("LLM_MAX_RETRIES", "3")))
    retry_backoff: float = Field(default_factory=lambda: float(os.getenv("LLM_RETRY_BACKOFF", "2.0")))




class AppConfig(BaseModel):
    """Application configuration"""
    log_level: str = Field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))
    output_dir: str = Field(default_factory=lambda: os.getenv("OUTPUT_DIR", "./output"))
    schema_cache_dir: str = Field(default_factory=lambda: os.getenv("SCHEMA_CACHE_DIR", "./schema_cache"))
   
    # Validation settings
    min_semantic_score: float = Field(default_factory=lambda: float(os.getenv("MIN_SEMANTIC_SCORE", "0.05")))
    enable_semantic_validation: bool = Field(default_factory=lambda: os.getenv("ENABLE_SEMANTIC_VALIDATION", "true").lower() == "true")
   
    # View generation settings
    default_num_views: int = Field(default_factory=lambda: int(os.getenv("DEFAULT_NUM_VIEWS", "5")))
    max_views: int = Field(default_factory=lambda: int(os.getenv("MAX_VIEWS", "20")))




class Config(BaseModel):
    """Master configuration object"""
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    llm: LLMConfig = Field(default_factory=LLMConfig)
    app: AppConfig = Field(default_factory=AppConfig)
   
    @classmethod
    def load(cls) -> "Config":
        """Load configuration from environment variables"""
        return cls(
            database=DatabaseConfig(),
            llm=LLMConfig(),
            app=AppConfig()
        )




# Global configuration instance
config = Config.load()




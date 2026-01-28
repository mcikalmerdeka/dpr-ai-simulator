"""Application settings and configuration."""

from pydantic_settings import BaseSettings
from pydantic import Field
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # OpenAI Configuration
    openai_api_key: str = Field(default="", description="OpenAI API Key")
    openai_model: str = Field(default="gpt-4.1-nano", description="OpenAI model to use")

    # Cost Configuration (per 1k tokens)
    prompt_cost_per_1k: float = Field(default=0.0001, description="Cost per 1k prompt tokens")
    completion_cost_per_1k: float = Field(default=0.0004, description="Cost per 1k completion tokens")

    # Simulation Configuration
    default_member_count: int = Field(default=50, description="Default number of DPR members to simulate")
    batch_size: int = Field(default=10, description="Batch size for processing members")
    rate_limit_delay: float = Field(default=1.0, description="Delay between batches in seconds")

    # UI Configuration
    gradio_server_name: str = Field(default="127.0.0.1", description="Gradio server host")
    gradio_server_port: int = Field(default=7860, description="Gradio server port")
    gradio_share: bool = Field(default=False, description="Share Gradio app publicly")

    model_config = {
        "extra": "ignore",
    }


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()

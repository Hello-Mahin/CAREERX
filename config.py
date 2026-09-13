
"""
CAREERX – Central configuration loaded from environment variables.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # IBM watsonx.ai
    watsonx_api_key: str = Field(default="", description="IBM Cloud API key")
    watsonx_project_id: str = Field(default="", description="watsonx.ai project ID")
    watsonx_url: str = Field(
        default="https://us-south.ml.cloud.ibm.com",
        description="watsonx.ai endpoint URL",
    )

    # Model IDs
    granite_llm_model: str = Field(
        default="ibm/granite-13b-instruct-v2",
        description="Granite LLM model ID",
    )
    granite_embedding_model: str = Field(
        default="ibm/slate-125m-english-rtrvr",
        description="Granite embedding model ID",
    )

    # Storage
    chroma_persist_dir: str = Field(
        default="./data/chroma_db",
        description="ChromaDB persistence directory",
    )
    kb_data_path: str = Field(
        default="./data/knowledge_base.json",
        description="Path to knowledge-base JSON file",
    )

    # Server
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    app_debug: bool = True
    log_level: str = "INFO"

    # Safety
    disclaimer_text: str = (
        "Career recommendations are AI-generated guidance only "
        "and do not guarantee employment outcomes."
    )


settings = Settings()

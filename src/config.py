from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class DefaultSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf_8",
        extra="ignore",
        env_nested_delimiter="__",
        frozen=True,  # Config settings immutable
    )


class ArxivSettings(DefaultSettings):
    """arXiv API client settings."""

    base_url: str = "https://export.arxiv.org/api/query"
    namespaces: dict = Field(
        {
            "atom": "http://www.w3.org/2005/Atom",
            "opensearch": "http://a9.com/-/spec/opensearch/1.1/",
            "arxiv": "http://arxiv.org/schemas/atom",
        }
    )  # For parse XML Response
    rate_limit_delay: float = 3.0  # Seconds between requests
    timeout_seconds: int = 30
    max_results: int = 100
    search_category: str = "cs.AI"  # Default category to search
    pdf_cache_dir: str = "./data/arxiv_pdfs"


class Settings(DefaultSettings):
    """Application settings."""

    app_version: str = "0.1.0"
    debug: bool = True
    environment: str = "dev"
    service_name: str = "rag-api"

    # arXiv settings
    arxiv: ArxivSettings = Field(default_factory=ArxivSettings)


def get_settings() -> Settings:
    """Get application settings."""
    return Settings()

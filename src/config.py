from pydantic import BaseModel, Field, PostgresDsn
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


class PDFParserSettings(DefaultSettings):
    """PDF parser service settings."""

    max_pages: int = 30
    max_file_size_mb: int = 20
    do_ocr: bool = False
    do_table_structure: bool = True


class PostgresSettings(BaseModel):
    db_url: PostgresDsn = "postgresql+psycopg2://rag_user:rag_password@localhost:5432/rag_db"
    echo_sql: bool = False
    pool_size: int = 20
    max_overflow: int = 0


class Settings(DefaultSettings):
    """Application settings."""

    app_version: str = "0.1.0"
    debug: bool = True
    environment: str = "dev"
    service_name: str = "rag-api"

    # arXiv settings
    arxiv: ArxivSettings = Field(default_factory=ArxivSettings)
    # PDF parser settings
    pdf_parser: PDFParserSettings = Field(default_factory=PDFParserSettings)
    # Postgres SQL settings
    postgres: PostgresSettings = Field(default_factory=PostgresSettings)


def get_settings() -> Settings:
    """Get application settings."""
    return Settings()

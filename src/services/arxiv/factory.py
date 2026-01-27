from src.config import get_settings

from .client import ArxivClient


def make_arxiv_client() -> ArxivClient:
    """Create an arXiv client instance.

    Returns:
        An instance of arXiv client.
    """

    settings = get_settings()
    return ArxivClient(settings=settings.arxiv)

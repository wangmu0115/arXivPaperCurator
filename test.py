import asyncio

from src.config import ArxivSettings
from src.services.arxiv.client import ArxivClient

settings = ArxivSettings()
client = ArxivClient(settings)

print(settings)

result = asyncio.run(client.fetch_papers(10))

print(result)

import asyncio

from src.config import ArxivSettings
from src.services.arxiv.client import ArxivClient

settings = ArxivSettings()
client = ArxivClient(settings)

print(settings)

result = asyncio.run(client.fetch_papers_with_query("ti:transformer AND cat:cs.AI", 3))

for paper in result:
    print(paper)
    # asyncio.run(client.download_pdf(paper))

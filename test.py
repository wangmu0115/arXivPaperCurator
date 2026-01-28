import asyncio
from pathlib import Path

from services.pdf_parser._docling import PDFParser
from src.config import ArxivSettings
from src.services.arxiv.client import ArxivClient

settings = ArxivSettings()
client = ArxivClient(settings)

print(settings)

# result = asyncio.run(client.fetch_papers_with_query("ti:transformer AND cat:cs.AI", 3))

# for paper in result:
#     print(paper)
#     asyncio.run(client.download_pdf(paper))

parser = PDFParser()

print(asyncio.run(parser.parse(Path("./data/arxiv_pdfs/2601.18858v1.pdf"))).sections[:2])

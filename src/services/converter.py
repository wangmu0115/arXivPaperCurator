from src.schemas.arxiv.paper import ArxivPaper
from src.schemas.pdf_parser.models import ArxivMetadata


def conv_arxiv_metadata(paper: ArxivPaper) -> ArxivMetadata:
    return ArxivMetadata(
        arxiv_id=paper.arxiv_id,
        title=paper.title,
        authors=paper.authors,
        summary=paper.summary,
        categories=paper.categories,
        published_date=paper.published_date,
        pdf_url=paper.pdf_url,
    )

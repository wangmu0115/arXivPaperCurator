import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import Optional

from sqlalchemy.orm import Session

from src.exceptions import MetadataFetchingException
from src.schemas.arxiv.paper import ArxivPaper
from src.schemas.pdf_parser.models import ParsedPaper
from src.services.arxiv.client import ArxivClient
from src.services.pdf_parser.parser import PDFParserService

from .converter import conv_arxiv_metadata

logger = logging.getLogger(__name__)


@dataclass
class ProcessingStat:
    papers_fetched: int = 0
    pdfs_downloaded: int = 0
    pdfs_parsed: int = 0
    papers_stored: int = 0
    processing_elapsed: float = 0.0
    errors: list = field(default_factory=list)


class MetadataFetcher:
    """Fetching arXiv papers with PDF processing and database storage.

    This service orchestrates the complete pipeline:
    1. Fetch paper metadata from arXiv API
    2. Download PDFs with caching
    3. Parse PDFs with Docling
    4. Store complete paper data in PostgreSQL
    """

    def __init__(
        self,
        arxiv_client: ArxivClient,
        pdf_parser: PDFParserService,
        max_concurrent_downloads: int = 5,
        max_concurrent_parsing: int = 3,
    ):
        self.arxiv_client = arxiv_client
        self.pdf_parser = pdf_parser
        self.max_concurrent_downloads = max_concurrent_downloads
        self.max_concurrent_parsing = max_concurrent_parsing

    async def fetch_and_process_papers(
        self,
        max_results: Optional[int] = None,
        date_range: Optional[tuple[str, str]] = None,
        process_pdfs: bool = True,
        store_to_db: bool = True,
        db_session: Optional[Session] = None,
    ) -> ProcessingStat:
        """Fetch papers from arXiv, process PDFs, and store to database.

        Args:
            max_results: Maximum papers to fetch
            date_range: Filter papers between date range (YYYYMMDD, YYYYMMDD)
            process_pdfs: Whether to download and parse PDFs
            store_to_db: Whether to store results in database
            db_session: Database session (required if store_to_db=True)

        Returns:
            Processing results and statistics
        """
        processing_stat = ProcessingStat()

        start = time.perf_counter()

        try:
            # Step 1: Fetch paper metadata from arXiv
            arxiv_papers = await self.arxiv_client.fetch_papers(max_results=max_results, date_range=date_range)
            processing_stat.papers_fetched = len(arxiv_papers)
            if not arxiv_papers:
                logger.warning("No papers found.")
                return processing_stat

            # Step 2: Process PDFs if `process_pdfs=True`
            if process_pdfs:
                ...

        except Exception:
            pass

    async def _batch_process_pdfs(self, papers: list[ArxivPaper]):
        """Process PDFs for a batch of papers with async concurrency."""

        logger.info("Starting async pipeline for %d PDFs...", len(papers))
        logger.info("Concurrent: downloads=%d, parsing=%d", self.max_concurrent_downloads, self.max_concurrent_parsing)
        # Create semaphores for controlled concurrency
        download_semaphore = asyncio.Semaphore(self.max_concurrent_downloads)
        parse_semaphore = asyncio.Semaphore(self.max_concurrent_parsing)
        # Start all download+parse pipelines concurrently
        pipeline_tasks = [self._download_parse_pipeline(paper, download_semaphore, parse_semaphore) for paper in papers]
        # Wait for all pipelines to complete
        pipeline_results = await asyncio.gather(*pipeline_tasks, return_exceptions=True)

        # Process results with detailed error tracking
        for paper, result in zip(papers, pipeline_results):
            if isinstance(result, Exception):
                ...
            else:
                download_success, parsed_paper = result
                ...

    async def _download_parse_pipeline(
        self,
        paper: ArxivPaper,
        download_semaphore: asyncio.Semaphore,
        parse_semaphore: asyncio.Semaphore,
    ) -> tuple[bool, Optional[ParsedPaper]]:
        """Complete download+parse pipeline for a single paper with true parallelism.
        Downloads PDF, then immediately starts parsing while other downloads continue.

        Returns:
            Tuple of (download_success: bool, parsed_paper: Optional[ParsedPaper])
        """
        download_success = False
        parsed_paper = None
        try:
            # Step 1: Download PDF
            async with download_semaphore:
                logger.info("Starting download: %s", paper.arxiv_id)
                pdf_path = self.arxiv_client.download_pdf(paper, False)
                if pdf_path:
                    download_success = True
                    logger.info("Download complete: %s", paper.arxiv_id)
                else:
                    logger.error("Download failed: %s", paper.arxiv_id)
                    return (False, None)  # Immediate fail
            # Step 2: Parse PDF
            async with parse_semaphore:
                logger.info("Starting parse: %s", paper.arxiv_id)
                pdf_content = await self.pdf_parser.parse(pdf_path)
                if pdf_content:
                    arxiv_metadata = conv_arxiv_metadata(paper)  # Convert object
                    parsed_paper = ParsedPaper(arxiv_metadata=arxiv_metadata, pdf_content=pdf_content)
                    logger.info("Parse complete: %s - %d chars extracted", paper.arxiv_id, len(pdf_content.raw_text))
                else:
                    logger.warning("PDF parsing failed for %s, continuing with metadata only", paper.arxiv_id)

            return (download_success, parsed_paper)
        except Exception as e:
            logger.exception("Pipeline error for %s: ", paper.arxiv_id, e)
            raise MetadataFetchingException(f"Pipeline error for {paper.arxiv_id}: {e}") from e

"""The arXiv client used to fetch and download papers.

- https://info.arxiv.org/help/api/index.html
- https://info.arxiv.org/help/api/user-manual.html
"""

import asyncio
import logging
import time
from functools import cached_property
from pathlib import Path
from typing import Literal, Optional
from urllib.parse import quote_plus, urlencode

import httpx

from src.config import ArxivSettings
from src.exceptions import ArxivAPIException, PDFDownloadException
from src.schemas.arxiv.paper import ArxivPaper

from .parser import parse_arxiv_xml_data

logger = logging.getLogger(__name__)


class ArxivClient:
    """Client for fetching papers from arXiv API (https://info.arxiv.org/help/api/index.html)."""

    def __init__(self, settings: ArxivSettings):
        self._settings = settings
        self._last_request_time: Optional[float] = None  # Rate limits with arXiv API

    @cached_property
    def pdf_cache_dir(self) -> Path:
        cache_dir = Path(self._settings.pdf_cache_dir)
        cache_dir.mkdir(parents=True, exist_ok=True)
        return cache_dir

    @property
    def search_category(self) -> str:
        return self._settings.search_category

    async def fetch_papers(
        self,
        max_results: Optional[int] = None,
        start: int = 0,
        sort_by: Literal["relevance", "lastUpdatedDate", "submittedDate"] = "submittedDate",
        sort_order: Literal["ascending", "descending"] = "descending",
        date_range: Optional[tuple[str, str]] = None,
    ) -> list[ArxivPaper]:
        """Fetch papers from arXiv by configured category.

        Args:
            max_results: Maximum number of papers to fetch (uses settings default if None)
            start: Starting index of pagination
            sort_by: Sort criteria (relevance, lastUpdatedDate, submittedDate)
            sort_order: Sort order (ascending, descending)
            date_range: Filter papers submitted between the date range(format: YYYYMMDD)

        Returns:
            A list of ArxivPaper objects for the configured category.
        """
        # Build search query
        search_query = f"cat:{self._settings.search_category}"
        if date_range:
            search_query += f" AND submittedDate:[{date_range[0]}0000 TO {date_range[1]}2359]"

        return await self.fetch_papers_with_query(
            search_query,
            max_results,
            start,
            sort_by,
            sort_order,
        )

    async def fetch_papers_with_query(
        self,
        search_query: str,
        max_results: Optional[int] = None,
        start: int = 0,
        sort_by: Literal["relevance", "lastUpdatedDate", "submittedDate"] = "submittedDate",
        sort_order: Literal["ascending", "descending"] = "descending",
    ) -> list[ArxivPaper]:
        """Fetch papers from arXiv by a custom search query.

        Args:
            search_query: Custom arXiv search query (e.g., "cat:cs.AI AND submittedDate:[202401010000 TO 202412312359]")
            max_results: Maximum number of papers to fetch (uses settings default if None)
            start: Starting index of pagination
            sort_by: Sort criteria (relevance, lastUpdatedDate, submittedDate)
            sort_order: Sort order (ascending, descending)

        Returns:
            A list of ArxivPaper objects matching the search query.

        Examples:
            # Papers from last 30 days
            "cat:cs.AI AND submittedDate:[202401010000 TO 202401312359]"

            # Papers by specific author
            "au:LeCun AND cat:cs.AI"

            # Papers with specific keywords in title
            "ti:transformer AND cat:cs.AI"
        """
        if max_results is None:
            max_results = self._settings.max_results

        # Query params
        params = {
            "search_query": search_query,
            "start": start,
            "max_results": min(max_results, 2000),
            "sortBy": sort_by,
            "sortOrder": sort_order,
        }

        # Query URL, exclude encode `:+[]` characters, which used for arXiv queries
        url = f"{self._settings.base_url}?{urlencode(params, quote_via=quote_plus, safe=':+[]')}"

        try:
            logger.info("Fetching %d %s papers from arXiv.", max_results, self.search_category)
            # Rate limiting, arXiv recommends 3 seconds.
            if self._last_request_time is not None:
                time_since_last = time.time() - self._last_request_time
                if time_since_last < self._settings.rate_limit_delay:
                    sleep_time = self._settings.rate_limit_delay - time_since_last
                    await asyncio.sleep(sleep_time)
            # Reset request time
            self._last_request_time = time.time()
            # Fetch xml response
            async with httpx.AsyncClient(timeout=self._settings.timeout_seconds) as client:
                response = await client.get(url)
                response.raise_for_status()
                xml_data = response.text

            papers = parse_arxiv_xml_data(xml_data, self._settings.namespaces)
            logger.info("Query returned %d papers.", len(papers))
            return papers
        except Exception as e:
            logger.exception("Failed to fetch papers from arXiv: ", e)
            raise ArxivAPIException(f"Fetching papers from arXiv failed: {e}")

    async def download_pdf(self, paper: ArxivPaper, force_download: bool = True) -> Optional[Path]:
        """Download PDF for a given paper to local cache.
        Args:
            paper: ArxivPaper object containing PDF URL
            force_download: Force re-download even if file exists

        Returns:
            Path to downloaded PDF file or None if download failed
        """
        if not paper.pdf_url:
            logger.warning("No PDF URL for arXiv paper: %s", paper.arxiv_id)
            return None
        # arXiv paper PDF file
        pdf_path = self.pdf_cache_dir / (paper.arxiv_id.replace("/", "_") + ".pdf")
        # PDF file exists
        if pdf_path.exists() and not force_download:
            logger.info("File %s exists, using cached PDF.", pdf_path.name)
            return pdf_path
        # Download with retry
        if await self._download_with_retry(paper.pdf_url, pdf_path):
            return pdf_path
        else:
            return None

    async def _download_with_retry(self, url: str, path: Path, max_retries: int = 3) -> bool:
        """Download a file with retry logic.

        Args:
            url: Download pdf file link
            path: Path to save the file
            max_retries: Maximum number of retries

        Returns:
            True if successful, False otherwise
        """
        logger.info("Download PDF from %s", url)
        # Rate limits
        await asyncio.sleep(self._settings.rate_limit_delay)

        for retry in range(max_retries):
            try:
                async with httpx.AsyncClient(timeout=self._settings.timeout_seconds) as client:
                    async with client.stream("GET", url) as response:
                        response.raise_for_status()
                        with path.open(mode="wb") as f:
                            async for chunk in response.aiter_bytes():
                                f.write(chunk)
                logger.info("Success download to %s", path.name)
                return True

            except httpx.TimeoutException | httpx.HTTPError as e:
                if retry < max_retries - 1:
                    logger.warning("Download PDF failed(%d/%d): %s", retry + 1, max_retries, str(e))
                    # Wait 5,10,... seconds, try again.
                    await asyncio.sleep(5 * (retry + 1))
                else:
                    logger.exception("Download PDF failed after %d retries: ", max_retries, e)
                    raise PDFDownloadException(f"Download PDF failed after {max_retries} retries: {e}")
            except Exception as e:
                logger.exception("Unexpected download error: ", e)
                raise PDFDownloadException(f"Unexpected download error: {e}")

        # Download failed, clean up
        if path.exists():
            path.unlink()
        return False

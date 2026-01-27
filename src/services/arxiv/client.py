import asyncio
import logging
import time
import xml.etree.ElementTree as ET
from typing import Literal, Optional
from urllib.parse import quote_plus, urlencode

import httpx

from src.config import ArxivSettings
from src.exceptions import ArxivAPIException, ArxivAPITimeoutError, ArxivParseError
from src.schemas.arxiv.paper import ArxivPaper

logger = logging.getLogger(__name__)


class ArxivClient:
    """Client for fetching papers from arXiv API (https://info.arxiv.org/help/api/index.html)."""

    def __init__(self, settings: ArxivSettings):
        self._settings = settings
        self._last_request_time: Optional[float] = None  # Rate limits with arXiv API

    @property
    def base_url(self) -> str:
        return self._settings.base_url

    @property
    def rate_limit_delay(self) -> float:
        return self._settings.rate_limit_delay

    @property
    def timeout_seconds(self) -> int:
        return self._settings.timeout_seconds

    @property
    def max_results(self) -> int:
        return self._settings.max_results

    @property
    def search_category(self) -> str:
        return self._settings.search_category

    @property
    def namespaces(self) -> dict:
        return self._settings.namespaces

    async def fetch_papers(
        self,
        max_results: Optional[int] = None,
        start: int = 0,
        sort_by: Literal["relevance", "lastUpdatedDate", "submittedDate"] = "submittedDate",
        sort_order: Literal["ascending", "descending"] = "descending",
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
    ) -> list[ArxivPaper]:
        """Fetch papers from arXiv by configured category.

        Args:
            max_results: Maximum number of papers to fetch (uses settings default if None)
            start: Starting index of pagination
            sort_by: Sort criteria (relevance, lastUpdatedDate, submittedDate)
            sort_order: Sort order (ascending, descending)
            from_date: Filter papers submitted after this date (format: YYYYMMDD), `from_date` and `to_date` must be all not none.
            to_date: Filter papers submitted before this date (format: YYYYMMDD), `from_date` and `to_date` must be all not none.

        Returns:
            A list of ArxivPaper objects for the configured category.
        """
        if max_results is None:
            max_results = self.max_results

        # Build search query: https://info.arxiv.org/help/api/user-manual.html#51-details-of-query-construction
        search_query = f"cat:{self.search_category}"
        if from_date and to_date:
            search_query += f" AND submittedDate:[{from_date}0000 TO {to_date}2359]"

        # Query params: https://info.arxiv.org/help/api/user-manual.html#3-structure-of-the-api
        params = {
            "search_query": search_query,
            "start": start,
            "max_results": min(max_results, 2000),
            "sortBy": sort_by,
            "sortOrder": sort_order,
        }
        # Decode. Exclude `:+[]` characters, used for arXiv queries
        url = f"{self.base_url}?{urlencode(params, quote_via=quote_plus, safe=':+[]*')}"

        try:
            logger.info("Fetching %d %s papers from arXiv.", max_results, self.search_category)

            # Rate limiting, arXiv recommends 3 seconds.
            if self._last_request_time is not None:
                time_since_last = time.time() - self._last_request_time
                if time_since_last < self.rate_limit_delay:
                    await asyncio.sleep(self.rate_limit_delay - time_since_last)

            self._last_request_time = time.time()  # Reset request time

            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.get(url)
                response.raise_for_status()
                xml_data = response.text

            papers = self._parse_response(xml_data)
            logger.info("Query returned %d papers.", len(papers))
            return papers

        except httpx.TimeoutException as e:
            logger.exception("arXiv API timeout: ", e)
            raise ArxivAPITimeoutError(f"arXiv API request timeout: {e}")
        except httpx.HTTPStatusError as e:
            logger.exception("arXiv API HTTP error: ", e)
            raise ArxivAPIException(f"arXiv API returned error {e.response.status_code}: {e}")
        except Exception as e:
            logger.exception("Failed to fetch papers from arXiv: ", e)
            raise ArxivAPIException(f"Unexpected error fetching papers from arXiv: {e}")

    def _parse_response(self, xml_data: str) -> list[ArxivPaper]:
        """Parse arXiv API XML response into `ArxivPaper` objects."""
        try:
            # https://info.arxiv.org/help/api/user-manual.html#32-the-api-response
            root = ET.fromstring(xml_data)
            entries = root.findall("atom:entry", self.namespaces)

            papers = []
            for entry in entries:
                paper = self._parse_single_entry(entry)
                if paper:
                    papers.append(paper)
            return papers

        except ET.ParseError as e:
            logger.exception("Failed to parse arXiv XML response: ", e)
            raise ArxivParseError(f"Failed to parse arXiv XML response: {e}")
        except Exception as e:
            logger.exception("Unexpected error parsing arXiv response: ", e)
            raise ArxivParseError(f"Unexpected error parsing arXiv response: {e}")

    def _parse_single_entry(self, entry: ET.Element) -> Optional[ArxivPaper]:
        """Parse a single entry from arXiv XML response."""
        try:
            arxiv_id = self._get_arxiv_id(entry)
            if arxiv_id is None:
                return None

            title = self._get_arxiv_title(entry)
            authors = self._get_arxiv_authors(entry)
            summary = self._get_arxiv_summary(entry)
            published = self._get_arxiv_published(entry)
            categories = self._get_arxiv_categories(entry)
            pdf_url = self._get_arxiv_pdf_url(entry)

            return ArxivPaper(
                arxiv_id=arxiv_id,
                title=title,
                authors=authors,
                summary=summary,
                published_date=published,
                categories=categories,
                pdf_url=pdf_url,
            )
        except Exception as e:
            logger.exception("Failed to parse arxiv paper response single entry: ", e)
            return None

    def _get_arxiv_id(self, entry: ET.Element) -> Optional[str]:
        id_element = entry.find("atom:id", self.namespaces)
        if id_element is None or id_element.text is None:
            return None
        else:
            return id_element.text.split("/")[-1]

    def _get_arxiv_title(self, entry: ET.Element) -> str:
        return self._get_text(entry, "atom:title", clean_newlines=True)

    def _get_arxiv_authors(self, entry: ET.Element) -> list[str]:
        author_names = []
        for author_element in entry.findall("atom:author", self.namespaces):
            name = self._get_text(author_element, "atom:name")
            if name:
                author_names.append(name)
        return author_names

    def _get_arxiv_summary(self, entry: ET.Element) -> str:
        return self._get_text(entry, "atom:summary", clean_newlines=True)

    def _get_arxiv_published(self, entry: ET.Element) -> str:
        return self._get_text(entry, "atom:published")

    def _get_arxiv_categories(self, entry: ET.Element) -> list[str]:
        categories = []
        for category_element in entry.findall("atom:category", self.namespaces):
            term = category_element.get("term")
            if term:
                categories.append(term)
        return categories

    def _get_arxiv_pdf_url(self, entry: ET.Element) -> str:
        for link_element in entry.findall("atom:link", self.namespaces):
            if link_element.get("type") == "application/pdf":
                url = link_element.get("href", "")
                # Convert HTTP to HTTPS for arXiv URLs
                if url.startswith("http://arxiv.org/"):
                    url = url.replace("http://arxiv.org/", "https://arxiv.org/")
                return url
        return ""

    def _get_text(self, entry: ET.Element, path: str, clean_newlines: bool = False) -> str:
        element = entry.find(path, self.namespaces)
        if element is None or element.text is None:
            return ""
        text = element.text.strip()
        return text.replace("\n", " ") if clean_newlines else text

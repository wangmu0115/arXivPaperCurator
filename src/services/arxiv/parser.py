import logging
import xml.etree.ElementTree as ET
from typing import Optional

from src.exceptions import ArxivParseError
from src.schemas.arxiv.paper import ArxivPaper

logger = logging.getLogger(__name__)


def parse_arxiv_xml_data(xml_data: str, namespaces: dict) -> list[ArxivPaper]:
    """Parse arXiv API XML response into `ArxivPaper` objects."""
    try:
        # https://info.arxiv.org/help/api/user-manual.html#32-the-api-response
        root = ET.fromstring(xml_data)
        entries = root.findall("atom:entry", namespaces)

        papers = []
        for entry in entries:
            paper = __parse_arxiv_paper(entry, namespaces)
            if paper:
                papers.append(paper)
        return papers

    except ET.ParseError | Exception as e:
        logger.exception("Failed to parse arXiv XML data: ", e)
        raise ArxivParseError(f"Failed to parse arXiv XML data: {e}")


def __parse_arxiv_paper(entry: ET.Element, namespaces: dict) -> ArxivPaper:
    try:
        arxiv_id = __arxiv_id(entry, namespaces)
        if arxiv_id is None:
            return None

        return ArxivPaper(
            arxiv_id=arxiv_id,
            title=__el_text(entry, "atom:title", namespaces, clean_newlines=True),
            authors=__arxiv_authors(entry, namespaces),
            summary=__el_text(entry, "atom:summary", namespaces, clean_newlines=True),
            published_date=__el_text(entry, "atom:published", namespaces, clean_newlines=False),
            categories=__arxiv_categories(entry, namespaces),
            pdf_url=__arxiv_pdf_url(entry, namespaces),
        )
    except Exception as e:
        logger.exception("Failed to parse arxiv paper by single entry: ", e)
        return None


def __arxiv_id(entry: ET.Element, namespaces: dict) -> Optional[str]:
    id = __el_text(entry, "atom:id", namespaces, clean_newlines=True)

    return None if len(id) == 0 else id.split("/")[-1]


def __arxiv_authors(entry: ET.Element, namespaces: dict) -> list[str]:
    authors = []
    for author_el in entry.findall("atom:author", namespaces):
        name = __el_text(author_el, "atom:name", namespaces, clean_newlines=True)
        if name:
            authors.append(name)
    return authors


def __arxiv_categories(entry: ET.Element, namespaces: dict) -> list[str]:
    categories = []
    for category_el in entry.findall("atom:category", namespaces):
        term = category_el.get("term")
        if term:
            categories.append(term)
    return categories


def __arxiv_pdf_url(entry: ET.Element, namespaces: dict) -> str:
    for link_element in entry.findall("atom:link", namespaces):
        if link_element.get("type") == "application/pdf":
            url = link_element.get("href", "")
            # Convert HTTP to HTTPS for arXiv URLs
            if url.startswith("http://arxiv.org/"):
                url = url.replace("http://arxiv.org/", "https://arxiv.org/")
            return url
    return ""


def __el_text(entry: ET.Element, path: str, namespaces: dict, clean_newlines: bool = False) -> str:
    el = entry.find(path, namespaces)
    if el is None or el.text is None:
        return ""
    text = el.text.strip()
    return text.replace("\n", " ") if clean_newlines else text

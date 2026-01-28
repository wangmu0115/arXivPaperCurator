from enum import StrEnum
from typing import Any, Optional

from pydantic import BaseModel, Field


class ParserType(StrEnum):
    """PDF parser types."""

    DOCLING = "docling"
    GROBID = "grobid"


class PaperSection(BaseModel):
    """Represents a section of a paper."""

    title: str = Field(..., description="Section title")
    content: str = Field(..., description="Section content")
    level: int = Field(1, description="Section hierarchy level")


class PaperFigure(BaseModel):
    """Represents a figure in a paper."""

    id: str = Field(..., description="Figure identifier")
    caption: str = Field(..., description="Figure caption")


class PaperTable(BaseModel):
    """Represents a table in a paper."""

    id: str = Field(..., description="Table identifier")
    caption: str = Field(..., description="Table caption")


class PdfContent(BaseModel):
    """PDF-specific content extracted by parsers like Docling."""

    sections: list[PaperSection] = Field(default_factory=list, description="Paper sections")
    figures: list[PaperFigure] = Field(default_factory=list, description="Figures")
    tables: list[PaperTable] = Field(default_factory=list, description="Tables")
    raw_text: str = Field(..., description="Full extracted text")
    references: list[str] = Field(default_factory=list, description="References")
    parser_used: ParserType = Field(..., description="Parser used for extraction")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Parser metadata")


class ArxivMetadata(BaseModel):
    """Paper metadata from arXiv API."""

    arxiv_id: str = Field(..., description="arXiv identifier")
    title: str = Field(..., description="Paper title from arXiv")
    authors: list[str] = Field(..., description="List of author names")
    summary: str = Field(..., description="Paper summary")
    categories: list[str] = Field(..., description="Paper categories")
    published_date: str = Field(..., description="Date published on arXiv (ISO format)")
    pdf_url: str = Field(..., description="URL to PDF")


class ParsedPaper(BaseModel):
    """Complete paper data combining arXiv metadata and PDF content."""

    arxiv_metadata: ArxivMetadata = Field(..., description="Metadata from arXiv API")
    pdf_content: Optional[PdfContent] = Field(None, description="Content extracted from PDF")

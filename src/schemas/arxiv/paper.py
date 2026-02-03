from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class ArxivPaper(BaseModel):
    """Schema for arXiv API response data."""

    arxiv_id: str = Field(..., description="arXiv paper ID")
    title: str = Field(..., description="Paper title")
    authors: list[str] = Field(..., description="List of author names")
    summary: str = Field(..., description="Paper summary")
    categories: list[str] = Field(..., description="Paper categories")
    published_date: str = Field(..., description="Date published on arXiv (ISO format)")
    pdf_url: str = Field(..., description="URL to PDF")


class PaperBase(BaseModel):
    """arXiv paper metadata."""

    arxiv_id: str = Field(..., description="arXiv paper ID")
    title: str = Field(..., description="Paper title")
    authors: list[str] = Field(..., description="List of author names")
    summary: str = Field(..., description="Paper summary")
    categories: list[str] = Field(..., description="Paper categories")
    published_date: str = Field(..., description="Date published on arXiv (ISO format)")
    pdf_url: str = Field(..., description="URL to PDF")


class PaperCreate(PaperBase):
    """Schema for creating a paper with optional parsed content."""

    # Parsed PDF content (optional - added when PDF is processed)
    raw_text: Optional[str] = Field(None, description="Full raw text extracted from PDF")
    sections: Optional[list[dict[str, Any]]] = Field(None, description="List of sections with titles and content")
    references: Optional[list[dict[str, Any]]] = Field(None, description="List of references if extracted")

    # PDF processing metadata (optional)
    parser_used: Optional[str] = Field(None, description="Which parser was used (DOCLING, GROBID, etc.)")
    parser_metadata: Optional[dict[str, Any]] = Field(None, description="Additional parser metadata")
    pdf_processed: Optional[bool] = Field(False, description="Whether PDF was successfully processed")
    pdf_processing_date: Optional[datetime] = Field(None, description="When PDF was processed")

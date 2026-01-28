import logging
from pathlib import Path
from typing import Optional

import pypdfium2 as pdfium
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.document_converter import DocumentConverter, PdfFormatOption

from src.exceptions import PDFValidationError
from src.schemas.pdf_parser.models import PaperSection, ParserType, PdfContent

logger = logging.getLogger(__name__)


class PDFParser:
    def __init__(
        self,
        max_pages: int = 20,
        max_file_size_mb: int = 20,
        do_ocr: bool = False,
        do_table_structure: bool = True,
    ):
        """Initialize DocumentConverter with optimized pipeline options.

        Args:
            max_pages: Maximum number of pages to process (default: 20)
            max_file_size_mb: Maximum file size in MB (default: 20MB)
            do_ocr: Enable OCR for scanned PDFs (default: False, very slow)
            do_table_structure: Extract table structures (default: True)
        """
        pipeline_options = PdfPipelineOptions(do_table_structure=do_table_structure, do_ocr=do_ocr)
        self.converter = DocumentConverter(format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)})
        self.warmed_up = False
        self.max_pages = max_pages
        self.max_file_size_bytes = max_file_size_mb * 1024 * 1024

    async def parse(self, pdf_path: Path) -> Optional[PdfContent]:
        """Parse PDF using Docling. Limited to 20 pages to avoid memory issues with large papers.

        Args:
            pdf_path: Path to PDF file

        Returns:
            PdfContent object or None if parsing failed
        """
        # Validate PDF size and page limits
        valid, err = self._validate_pdf(pdf_path)
        if not valid:
            raise PDFValidationError(err)

        # Convert PDF using the modern API
        result = self.converter.convert(pdf_path, max_num_pages=self.max_pages, max_file_size=self.max_file_size_bytes)
        # Extract structured content
        doc = result.document

        # Extract sections from document structure
        sections = []
        current_section = {"title": "Content", "content": ""}

        for element in doc.texts:
            if hasattr(element, "label") and element.label in ["title", "section_header"]:
                # Save previous section if it has content
                if current_section["content"].strip():
                    sections.append(PaperSection(title=current_section["title"], content=current_section["content"].strip()))
                # Start new section
                current_section = {"title": element.text.strip(), "content": ""}
            else:
                # Add content to current section
                if hasattr(element, "text") and element.text:
                    current_section["content"] += element.text + "\n"

        # Add final section
        if current_section["content"].strip():
            sections.append(PaperSection(title=current_section["title"], content=current_section["content"].strip()))

        # Focus on what arXiv API doesn't provide: structured full text content only
        return PdfContent(
            sections=sections,
            figures=[],  # Removed: basic metadata not useful
            tables=[],  # Removed: basic metadata not useful
            raw_text=doc.export_to_text(),
            references=[],
            parser_used=ParserType.DOCLING,
            metadata={"source": "docling", "note": "Content extracted from PDF, metadata comes from arXiv API"},
        )

    def _validate_pdf(self, pdf_path: Path) -> tuple[bool, str | Exception | None]:
        try:
            # Check file exists and not empty
            if not pdf_path.exists():
                logger.error("PDF file %s not exist.", pdf_path)
                return (False, "NotExist")

            # Check file size limit
            file_size = pdf_path.stat().st_size
            if file_size == 0:
                logger.error("PDF file %s is empty.", pdf_path)
                return (False, "EmptyFile")
            elif file_size > self.max_file_size_bytes:
                logger.error("PDF file %s size(%.2f MB) out of limit(%.2f MB).", pdf_path, (file_size / 1048576), (self.max_file_size_bytes / 1048576))
                return (False, "FileSizeOutLimits")

            # Check file starts with PDF header
            with pdf_path.open("rb") as f:
                header = f.read(8)
                if not header.startswith(b"%PDF-"):
                    logger.error("File %s does not have PDF header.", pdf_path)
                    return (False, "FileMissingPDFHeader")

            # Check file page limit
            pdf_doc = pdfium.PdfDocument(pdf_path)
            actual_pages = len(pdf_doc)
            pdf_doc.close()
            if actual_pages > self.max_pages:
                logger.error("PDF file %s has %d pages, out of limit(%d).", pdf_path, actual_pages, self.max_pages)
                return (False, "FilePageOutLimits")

            # All passed
            return (True, None)
        except Exception as e:
            logger.exception("Unexpected error while validate PDF file %s: ", pdf_path, e)
            return (False, e)

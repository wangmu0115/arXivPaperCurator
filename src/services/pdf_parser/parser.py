import logging
from pathlib import Path
from typing import Optional

from src.schemas.pdf_parser.models import PdfContent
from src.services.pdf_parser._docling import PDFParser as DoclingPDFParser

logger = logging.getLogger(__name__)


class PDFParserService:
    def __init__(
        self,
        max_pages: int = 30,
        max_file_size_mb: int = 20,
        do_ocr: bool = False,
        do_table_structure: bool = True,
    ):
        # Initialize Docling PDF parser
        self.parser = DoclingPDFParser(max_pages, max_file_size_mb, do_ocr, do_table_structure)

    async def parse(self, pdf_path: Path) -> Optional[PdfContent]:
        """Parse PDF using Docling parser

        Args:
            pdf_path: Path to PDF file

        Returns:
            PdfContent object or None if parsing failed
        """
        try:
            parsed_result = await self.parser.parse(pdf_path)
            if parsed_result:
                logger.info("Parse file %s completed.", pdf_path)
                return parsed_result
            else:
                logger.error("Docling parsing returned no result for: %s", pdf_path)

            pass
        except Exception as e:
            pass

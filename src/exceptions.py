class ArxivAPIException(Exception):
    """Base exception for arXiv API-related errors."""


class ArxivParseError(ArxivAPIException):
    """Exception raised when arXiv API response parsing fails."""


class PDFDownloadException(Exception):
    """Base exception for PDF download-related errors."""


class ParsingException(Exception):
    """Base exception for parsing-related errors."""


class PDFParsingException(ParsingException):
    """Base exception for PDF parsing-related errors."""


class PDFValidationError(PDFParsingException):
    """Exception raised when PDF file validation fails."""


class MetadataFetchingException(Exception):
    """Base exception for metadata fetching pipeline errors."""

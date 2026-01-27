class ArxivAPIException(Exception):
    """Base exception for arXiv API-related errors."""


class ArxivParseError(ArxivAPIException):
    """Exception raised when arXiv API response parsing fails."""


class PDFDownloadException(Exception):
    """Base exception for PDF download-related errors."""

"""
PDF processing utilities for text extraction.
Handles core PDF operations with clean separation of concerns.
"""

import pdfplumber
from pathlib import Path
from typing import List, Optional
from src.logger_config import pipeline_logger


def validate_pdf_path(pdf_path: str) -> bool:
    """
    Validate that PDF file exists and is accessible.

    Args:
        pdf_path: Path to the PDF file

    Returns:
        True if file is valid, False otherwise
    """
    pdf_file = Path(pdf_path)

    if not pdf_file.exists():
        pipeline_logger.error(f"PDF file not found at {pdf_path}")
        return False

    if not pdf_file.is_file():
        pipeline_logger.error(f"Path exists but is not a file: {pdf_path}")
        return False

    if pdf_file.suffix.lower() != '.pdf':
        pipeline_logger.warning(f"File does not have .pdf extension: {pdf_path}")

    return True


def extract_pages_text(pdf_path: str) -> List[str]:
    """
    Extract text from all pages of a PDF file.

    Args:
        pdf_path: Path to the PDF file

    Returns:
        List of text strings, one per page

    Raises:
        Exception: If PDF processing fails
    """
    try:
        pipeline_logger.info(f"📄 Processing PDF: {pdf_path}")
        page_texts = []

        with pdfplumber.open(pdf_path) as pdf:
            total_pages = len(pdf.pages)
            pipeline_logger.info(f"📋 Total pages to process: {total_pages}")

            for i, page in enumerate(pdf.pages, 1):
                pipeline_logger.progress(i, total_pages, "pages", f"Extracting page {i}")

                text = page.extract_text()
                if text:
                    page_texts.append(text.strip())
                else:
                    pipeline_logger.warning(f"No text found on page {i}")

        pipeline_logger.info(f"✅ Successfully extracted text from {len(page_texts)} pages")
        return page_texts

    except Exception as e:
        pipeline_logger.error(f"Failed to extract text from PDF: {e}")
        raise


def format_extracted_text(page_texts: List[str], include_page_markers: bool = True) -> str:
    """
    Format extracted page texts into a single document.

    Args:
        page_texts: List of text from each page
        include_page_markers: Whether to include page break markers

    Returns:
        Formatted text document
    """
    if not page_texts:
        return ""

    if include_page_markers:
        formatted_sections = []
        for i, text in enumerate(page_texts, 1):
            formatted_sections.append(text)
            formatted_sections.append(f"\n--- Page {i} ---\n")

        full_text = "\n".join(formatted_sections)
    else:
        full_text = "\n\n".join(page_texts)

    pipeline_logger.info(f"📊 Formatted text: {len(full_text):,} characters")
    return full_text


def save_text_file(text: str, output_path: Path) -> bool:
    """
    Save text content to a file safely.

    Args:
        text: Text content to save
        output_path: Path where to save the file

    Returns:
        True if save was successful, False otherwise
    """
    try:
        # Ensure parent directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(text)

        pipeline_logger.info(f"💾 Text saved to: {output_path}")
        pipeline_logger.info(f"📊 File size: {output_path.stat().st_size:,} bytes")

        return True

    except Exception as e:
        pipeline_logger.error(f"Failed to save text file: {e}")
        return False


def get_pdf_info(pdf_path: str) -> dict:
    """
    Get basic information about a PDF file.

    Args:
        pdf_path: Path to the PDF file

    Returns:
        Dictionary with PDF metadata
    """
    try:
        with pdfplumber.open(pdf_path) as pdf:
            return {
                "total_pages": len(pdf.pages),
                "file_size": Path(pdf_path).stat().st_size,
                "metadata": pdf.metadata or {}
            }
    except Exception as e:
        pipeline_logger.error(f"Failed to get PDF info: {e}")
        return {"total_pages": 0, "file_size": 0, "metadata": {}}
"""
Step 1: PDF to Text Conversion Module
Clean orchestrator for PDF to text conversion using utility functions.
This is the first step in the pipeline for processing UK sanctions data.
"""

from typing import Optional
from src.logger_config import pipeline_logger
from src.utils.pdf_processor import (
    validate_pdf_path,
    extract_pages_text,
    format_extracted_text,
    save_text_file,
    get_pdf_info
)
from src.utils.path_utils import (
    resolve_pdf_path,
    create_output_path,
    get_file_info
)


def extract_text_from_pdf(pdf_path: str, output_dir: str = "output") -> Optional[str]:
    """
    Extract text from a PDF file and save it to a text file.

    Clean orchestrator that coordinates the extraction workflow:
    1. Validate PDF file
    2. Extract text from pages
    3. Format and save results
    4. Report metrics

    Args:
        pdf_path: Path to the input PDF file
        output_dir: Directory to save the extracted text file

    Returns:
        Extracted text as a string, or None if extraction fails
    """
    try:
        # Step 1: Validate PDF file
        if not validate_pdf_path(pdf_path):
            return None

        # Show file info for transparency
        file_info = get_file_info(pdf_path)
        pipeline_logger.info(f"📊 PDF file: {file_info['size_mb']} MB, {file_info['name']}")

        # Step 2: Extract text from pages
        page_texts = extract_pages_text(pdf_path)

        if not page_texts:
            pipeline_logger.warning("No text content extracted from PDF")
            return None

        # Step 3: Format text and prepare output
        full_text = format_extracted_text(page_texts, include_page_markers=True)
        output_path = create_output_path(pdf_path, output_dir, "_text", ".txt")

        # Step 4: Save results and report metrics
        if save_text_file(full_text, output_path):
            pipeline_logger.info("✅ Text extraction completed successfully!")
            return full_text
        else:
            return None

    except Exception as e:
        pipeline_logger.error(f"PDF extraction workflow failed: {e}")
        return None


def process_sanctions_pdf(pdf_filename: str = "Cyber.pdf") -> Optional[str]:
    """
    Process the UK sanctions PDF file specifically.

    Simple entry point for processing sanctions PDFs from the standard directory.

    Args:
        pdf_filename: Name of the PDF file in the pdf directory

    Returns:
        Extracted text or None if processing fails
    """
    # Resolve the full path to the PDF file
    pdf_path = resolve_pdf_path(pdf_filename, base_dir="pdf")

    # Log the processing start
    pipeline_logger.info(f"🎯 Processing UK sanctions PDF: {pdf_filename}")

    # Process the PDF using the main extraction function
    return extract_text_from_pdf(pdf_path)


if __name__ == "__main__":
    text = process_sanctions_pdf()
    if text:
        print("\nStep 1 Complete: PDF successfully converted to text")
        print("Ready for Step 2: LLM parsing and data extraction")
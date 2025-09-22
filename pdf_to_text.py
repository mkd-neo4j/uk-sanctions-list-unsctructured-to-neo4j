"""
Step 1: PDF to Text Conversion Module
This module handles the conversion of PDF files to text format.
It's the first step in the pipeline for processing UK sanctions data.
"""

import pdfplumber
import os
from pathlib import Path
from typing import Optional
from logger_config import pipeline_logger


def extract_text_from_pdf(pdf_path: str, output_dir: str = "output") -> Optional[str]:
    """
    Extract text from a PDF file and save it to a text file.

    Args:
        pdf_path: Path to the input PDF file
        output_dir: Directory to save the extracted text file

    Returns:
        Extracted text as a string, or None if extraction fails
    """
    try:
        Path(output_dir).mkdir(parents=True, exist_ok=True)

        pdf_file = Path(pdf_path)
        if not pdf_file.exists():
            pipeline_logger.error(f"PDF file not found at {pdf_path}")
            return None

        pipeline_logger.info(f"📄 Processing PDF: {pdf_path}")

        extracted_text = []

        with pdfplumber.open(pdf_path) as pdf:
            total_pages = len(pdf.pages)
            pipeline_logger.info(f"📋 Total pages to process: {total_pages}")

            for i, page in enumerate(pdf.pages, 1):
                pipeline_logger.progress(i, total_pages, "pages", f"Extracting page {i}")
                text = page.extract_text()
                if text:
                    extracted_text.append(text)
                    extracted_text.append(f"\n--- Page {i} ---\n")

        full_text = "\n".join(extracted_text)

        output_filename = pdf_file.stem + "_text.txt"
        output_path = Path(output_dir) / output_filename

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(full_text)

        pipeline_logger.info(f"✅ Text extraction successful!")
        pipeline_logger.info(f"💾 Saved to: {output_path}")
        pipeline_logger.info(f"📊 Total characters extracted: {len(full_text):,}")

        return full_text

    except Exception as e:
        pipeline_logger.error(f"Error extracting text from PDF: {e}")
        return None


def process_sanctions_pdf(pdf_filename: str = "Cyber.pdf") -> Optional[str]:
    """
    Process the UK sanctions PDF file specifically.

    Args:
        pdf_filename: Name of the PDF file in the pdf directory

    Returns:
        Extracted text or None if processing fails
    """
    pdf_path = f"pdf/{pdf_filename}"
    return extract_text_from_pdf(pdf_path)


if __name__ == "__main__":
    text = process_sanctions_pdf()
    if text:
        print("\nStep 1 Complete: PDF successfully converted to text")
        print("Ready for Step 2: LLM parsing and data extraction")
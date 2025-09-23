"""
Path handling utilities for file operations.
Provides clean path resolution, validation, and manipulation functions.
"""

from pathlib import Path
from typing import Optional
from src.logger_config import pipeline_logger


def ensure_output_directory(output_dir: str) -> Path:
    """
    Ensure output directory exists and return Path object.

    Args:
        output_dir: Directory path as string

    Returns:
        Path object for the directory

    Raises:
        Exception: If directory cannot be created
    """
    try:
        dir_path = Path(output_dir)
        dir_path.mkdir(parents=True, exist_ok=True)

        pipeline_logger.info(f"📁 Output directory ready: {dir_path}")
        return dir_path

    except Exception as e:
        pipeline_logger.error(f"Failed to create output directory {output_dir}: {e}")
        raise


def generate_output_filename(input_path: str, suffix: str = "_text", extension: str = ".txt") -> str:
    """
    Generate output filename based on input file.

    Args:
        input_path: Path to input file
        suffix: Suffix to add to the filename
        extension: File extension for output

    Returns:
        Generated filename string
    """
    input_file = Path(input_path)
    output_filename = input_file.stem + suffix + extension

    # pipeline_logger.debug(f"Generated output filename: {output_filename}")
    return output_filename


def resolve_pdf_path(filename: str, base_dir: str = "pdf") -> str:
    """
    Resolve full path to PDF file in base directory.

    Args:
        filename: Name of the PDF file
        base_dir: Base directory containing PDF files

    Returns:
        Full path to the PDF file
    """
    if Path(filename).is_absolute():
        # Already an absolute path
        resolved_path = filename
    else:
        # Relative path - combine with base directory
        resolved_path = str(Path(base_dir) / filename)

    # pipeline_logger.debug(f"Resolved PDF path: {filename} -> {resolved_path}")
    return resolved_path


def validate_file_path(file_path: str, expected_extension: Optional[str] = None) -> bool:
    """
    Validate that a file path exists and optionally has the expected extension.

    Args:
        file_path: Path to validate
        expected_extension: Expected file extension (e.g., ".pdf")

    Returns:
        True if file is valid, False otherwise
    """
    path = Path(file_path)

    if not path.exists():
        pipeline_logger.error(f"File not found: {file_path}")
        return False

    if not path.is_file():
        pipeline_logger.error(f"Path exists but is not a file: {file_path}")
        return False

    if expected_extension and path.suffix.lower() != expected_extension.lower():
        pipeline_logger.warning(f"File does not have expected extension {expected_extension}: {file_path}")
        return False

    return True


def get_file_info(file_path: str) -> dict:
    """
    Get basic information about a file.

    Args:
        file_path: Path to the file

    Returns:
        Dictionary with file information
    """
    try:
        path = Path(file_path)
        stat = path.stat()

        return {
            "exists": path.exists(),
            "is_file": path.is_file(),
            "size_bytes": stat.st_size,
            "size_mb": round(stat.st_size / (1024 * 1024), 2),
            "extension": path.suffix,
            "name": path.name,
            "stem": path.stem
        }

    except Exception as e:
        pipeline_logger.error(f"Failed to get file info for {file_path}: {e}")
        return {"exists": False, "error": str(e)}


def create_output_path(input_path: str, output_dir: str, suffix: str = "_text", extension: str = ".txt") -> Path:
    """
    Create full output path for processed file.

    Args:
        input_path: Original input file path
        output_dir: Output directory
        suffix: Suffix to add to filename
        extension: File extension for output file

    Returns:
        Complete Path object for output file
    """
    output_directory = ensure_output_directory(output_dir)
    output_filename = generate_output_filename(input_path, suffix, extension)
    output_path = output_directory / output_filename

    # pipeline_logger.debug(f"Created output path: {output_path}")
    return output_path
"""
Text parsing utilities for UK sanctions data.
Handles splitting and cleaning of raw text into individual records.
"""

import re
from typing import List
from src.logger_config import pipeline_logger


def split_individuals_text(text: str) -> List[str]:
    """
    Split the text into individual person records.

    Args:
        text: The full sanctions text

    Returns:
        List of individual person text chunks
    """
    # Find the INDIVIDUALS section
    individuals_match = re.search(r'INDIVIDUALS\s*\n', text, re.IGNORECASE)
    if not individuals_match:
        return []

    # Extract text from INDIVIDUALS section onwards
    individuals_start = individuals_match.end()

    # Find where ENTITIES section starts (end of individuals)
    entities_match = re.search(r'ENTITIES\s*\n', text[individuals_start:], re.IGNORECASE)
    if entities_match:
        individuals_text = text[individuals_start:individuals_start + entities_match.start()]
    else:
        individuals_text = text[individuals_start:]

    # Split on pattern: number. Name 6: (with optional newline before)
    pattern = r'(?:^|\n)(\d+\.\s*Name\s*6:)'
    splits = re.split(pattern, individuals_text, flags=re.MULTILINE)

    if len(splits) <= 1:
        return []

    individuals = []
    # First item might be empty or whitespace, skip if so
    # Then we have alternating: (match, content, match, content, ...)
    start_idx = 1 if splits[0].strip() == '' else 0

    for i in range(start_idx, len(splits), 2):
        if i + 1 < len(splits):
            # Combine the pattern match with its content
            individual_text = splits[i] + splits[i + 1]
            individuals.append(individual_text.strip())

    pipeline_logger.info(f"📄 Split text into {len(individuals)} individual records")
    return individuals


def split_entities_text(text: str) -> List[str]:
    """
    Split the text into individual entity records.

    Args:
        text: The full sanctions text

    Returns:
        List of individual entity text chunks
    """
    # Find the ENTITIES section
    entities_match = re.search(r'ENTITIES\s*\n', text, re.IGNORECASE)
    if not entities_match:
        return []

    # Extract text from ENTITIES section onwards
    entities_start = entities_match.end()
    entities_text = text[entities_start:]

    # Split on pattern: number. Organisation Name: (with optional newline before)
    pattern = r'(?:^|\n)(\d+\.\s*Organisation\s*Name:)'
    splits = re.split(pattern, entities_text, flags=re.MULTILINE)

    if len(splits) <= 1:
        return []

    entities = []
    # First item might be empty or whitespace, skip if so
    # Then we have alternating: (match, content, match, content, ...)
    start_idx = 1 if splits[0].strip() == '' else 0

    for i in range(start_idx, len(splits), 2):
        if i + 1 < len(splits):
            # Combine the pattern match with its content
            entity_text = splits[i] + splits[i + 1]
            entities.append(entity_text.strip())

    pipeline_logger.info(f"🏢 Split text into {len(entities)} entity records")
    return entities
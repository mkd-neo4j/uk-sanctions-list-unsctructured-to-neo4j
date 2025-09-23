"""
File I/O utilities for sanctions data processing.
Handles JSON file operations, incremental saving, and output management.
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any
from src.models import IndividualsList, EntitiesList
from src.logger_config import pipeline_logger


class FileManager:
    """Manages file operations for sanctions data extraction output."""

    def __init__(self, output_dir: str = "output"):
        """
        Initialize file manager with output directory.

        Args:
            output_dir: Directory to create output files in
        """
        self.output_dir = Path(output_dir)
        self.individuals_output_path = None
        self.entities_output_path = None
        self.files_initialized = False

    def initialize_output_files(self, append_mode: bool = False) -> None:
        """
        Initialize JSON array files for incremental saving.
        Creates output directory if it doesn't exist.

        Args:
            append_mode: If True, append to existing files. If False, start fresh.
        """
        # Skip if already initialized (unless explicitly requested)
        if self.files_initialized and not append_mode:
            return

        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.individuals_output_path = self.output_dir / "individuals_extracted.json"
        self.entities_output_path = self.output_dir / "entities_extracted.json"

        # Check if files exist and handle accordingly
        if append_mode:
            # In append mode, create files only if they don't exist
            if not self.individuals_output_path.exists():
                with open(self.individuals_output_path, 'w', encoding='utf-8') as f:
                    json.dump([], f)
                pipeline_logger.info(f"📄 Created new individuals file: {self.individuals_output_path}")
            else:
                pipeline_logger.info(f"📄 Appending to existing individuals file: {self.individuals_output_path}")

            if not self.entities_output_path.exists():
                with open(self.entities_output_path, 'w', encoding='utf-8') as f:
                    json.dump([], f)
                pipeline_logger.info(f"📄 Created new entities file: {self.entities_output_path}")
            else:
                pipeline_logger.info(f"📄 Appending to existing entities file: {self.entities_output_path}")
        else:
            # In fresh mode, always create empty files
            with open(self.individuals_output_path, 'w', encoding='utf-8') as f:
                json.dump([], f)

            with open(self.entities_output_path, 'w', encoding='utf-8') as f:
                json.dump([], f)

            pipeline_logger.info(f"📁 Initialized fresh output files:")
            pipeline_logger.info(f"   • {self.individuals_output_path}")
            pipeline_logger.info(f"   • {self.entities_output_path}")

        self.files_initialized = True

    def get_existing_record_counts(self) -> Dict[str, int]:
        """
        Get counts of existing records in output files.

        Returns:
            Dictionary with 'individuals' and 'entities' counts
        """
        counts = {"individuals": 0, "entities": 0}

        if self.individuals_output_path and self.individuals_output_path.exists():
            try:
                with open(self.individuals_output_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    counts["individuals"] = len(data) if isinstance(data, list) else 0
            except:
                counts["individuals"] = 0

        if self.entities_output_path and self.entities_output_path.exists():
            try:
                with open(self.entities_output_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    counts["entities"] = len(data) if isinstance(data, list) else 0
            except:
                counts["entities"] = 0

        return counts

    def check_existing_files(self) -> Dict[str, bool]:
        """
        Check if output files exist.

        Returns:
            Dictionary indicating which files exist
        """
        return {
            "individuals_file_exists": self.individuals_output_path.exists() if self.individuals_output_path else False,
            "entities_file_exists": self.entities_output_path.exists() if self.entities_output_path else False
        }

    def append_to_json_file(self, file_path: Path, new_record: Dict[str, Any]) -> None:
        """
        Safely append a new record to a JSON array file.

        Args:
            file_path: Path to the JSON file
            new_record: Record to append

        Raises:
            Exception: If file operations fail
        """
        try:
            # Read existing data
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Append new record
            data.append(new_record)

            # Write back to file
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

        except Exception as e:
            pipeline_logger.error(f"Error appending to {file_path}: {e}")
            raise

    def save_individual_record(self, individual) -> None:
        """
        Save an individual record to the individuals JSON file.

        Args:
            individual: Individual model instance to save
        """
        if self.individuals_output_path:
            self.append_to_json_file(self.individuals_output_path, individual.model_dump())

    def save_entity_record(self, entity) -> None:
        """
        Save an entity record to the entities JSON file.

        Args:
            entity: Entity model instance to save
        """
        if self.entities_output_path:
            self.append_to_json_file(self.entities_output_path, entity.model_dump())

    def save_final_results(self, individuals: IndividualsList, entities: EntitiesList,
                          output_path: str = "output/extracted_data.json") -> None:
        """
        Save final combined extraction results.
        Individual files are already saved incrementally.

        Args:
            individuals: Extracted individuals data
            entities: Extracted entities data
            output_path: Path to save the main JSON file
        """
        # Ensure output directory exists
        output_dir = Path(output_path).parent
        output_dir.mkdir(parents=True, exist_ok=True)

        # Save main combined file (for compatibility and final summary)
        output_data = {
            "extractionDate": datetime.now().isoformat(),
            "source": "UK Sanctions List - Cyber Regime",
            "individuals": {
                "totalCount": individuals.totalCount,
                "data": [ind.model_dump() for ind in individuals.individuals]
            },
            "entities": {
                "totalCount": entities.totalCount,
                "data": [ent.model_dump() for ent in entities.entities]
            }
        }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)

        # Report final file status (individual files already saved incrementally)
        pipeline_logger.info(f"💾 Final extraction summary:")
        pipeline_logger.info(f"   • Combined summary: {output_path}")
        pipeline_logger.info(f"   • Individuals: {self.individuals_output_path} (saved incrementally)")
        pipeline_logger.info(f"   • Entities: {self.entities_output_path} (saved incrementally)")


def read_text_file(file_path: str) -> str:
    """
    Read text content from a file.

    Args:
        file_path: Path to the text file to read

    Returns:
        Content of the text file

    Raises:
        FileNotFoundError: If file doesn't exist
        Exception: If file reading fails
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        pipeline_logger.info(f"📄 Reading text from {file_path}")
        pipeline_logger.info(f"📊 Text file loaded: {len(content):,} characters")

        return content

    except Exception as e:
        pipeline_logger.error(f"Error reading file {file_path}: {e}")
        raise
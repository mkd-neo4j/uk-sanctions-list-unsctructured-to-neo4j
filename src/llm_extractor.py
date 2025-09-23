"""
LLM-based extraction module for UK sanctions data.
Clean, customer-friendly orchestrator for AI-powered entity extraction.
"""

import time
from typing import Tuple
from datetime import datetime
from dotenv import load_dotenv

from src.models import IndividualsList, EntitiesList
from src.logger_config import pipeline_logger
from src.utils import (
    split_individuals_text,
    split_entities_text,
    OpenAIClient,
    FileManager,
    ProgressTracker,
    read_text_file
)

# Load environment variables
load_dotenv()


class LLMExtractor:
    """
    Clean orchestrator for AI-powered sanctions data extraction.

    This class coordinates the extraction process using specialized utility modules,
    making it easy to understand and walk through with customers.
    """

    def __init__(self, api_key: str = None, output_dir: str = "output"):
        """
        Initialize the LLM extractor with required components.

        Args:
            api_key: OpenAI API key. If not provided, reads from environment.
            output_dir: Directory for output files.
        """
        # Initialize core components
        self.openai_client = OpenAIClient(api_key)
        self.file_manager = FileManager(output_dir)
        self.progress_tracker = ProgressTracker()

    def reset_output_files(self):
        """
        Reset output files to start fresh extraction.
        This will clear any existing incremental data.
        """
        self.file_manager.files_initialized = False
        self.file_manager.initialize_output_files(append_mode=False)
        pipeline_logger.info("🔄 Output files reset for fresh extraction")

    def extract_individuals(self, text: str) -> IndividualsList:
        """
        Extract sanctioned individuals from text using AI.

        This method orchestrates the complete individual extraction workflow:
        1. Split text into individual records
        2. Process each record with AI
        3. Save results incrementally
        4. Track progress and metrics

        Args:
            text: The raw text containing sanctions data

        Returns:
            IndividualsList containing all extracted individuals
        """
        # Step 1: Parse text into individual records
        individual_texts = split_individuals_text(text)

        if not individual_texts:
            pipeline_logger.warning("No individual records found in text")
            return IndividualsList(individuals=[], totalCount=0, extractionDate=datetime.now().isoformat())

        # Step 2: Initialize processing
        pipeline_logger.info(f"🤖 Starting AI extraction for {len(individual_texts)} individuals")
        pipeline_logger.info(f"🔧 Using model: {self.openai_client.model}")

        # Initialize output files with smart append mode
        existing_counts = self.file_manager.get_existing_record_counts()
        if existing_counts["individuals"] > 0 or existing_counts["entities"] > 0:
            pipeline_logger.info(f"📊 Found existing data: {existing_counts['individuals']} individuals, {existing_counts['entities']} entities")
            self.file_manager.initialize_output_files(append_mode=True)
        else:
            self.file_manager.initialize_output_files(append_mode=False)

        self.progress_tracker.start_processing()

        # Step 3: Process each individual record
        all_individuals = []
        successful_extractions = 0

        for i, individual_text in enumerate(individual_texts, 1):
            record_start_time = time.time()

            # Track progress
            self.progress_tracker.report_progress(i, len(individual_texts), "individuals",
                                                f"Processing and saving record {i}")

            try:
                # AI extraction using OpenAI client
                result = self.openai_client.extract_individual_structured(individual_text)

                # Process results
                all_individuals.extend(result.individuals)
                successful_extractions += 1

                # Save each individual immediately
                for individual in result.individuals:
                    self.file_manager.save_individual_record(individual)

                # Track timing
                processing_time = self.progress_tracker.track_record_processing(record_start_time)

                # Show examples for first few records
                if i <= 3 and result.individuals:
                    individual = result.individuals[0]
                    structured_data = {
                        "Name": f"{individual.firstName or ''} {individual.lastName or ''}".strip(),
                        "Sanction ID": individual.sanctionId,
                        "Nationality": individual.nationality,
                        "Date of Birth": individual.dateOfBirth or "Not provided",
                        "Group ID": individual.groupId
                    }
                    self.progress_tracker.show_example_output(i, individual_text, structured_data,
                                                           processing_time, is_individual=True)

            except Exception as e:
                self.progress_tracker.increment_errors()
                pipeline_logger.error(f"Error extracting individual {i}: {str(e)}")
                continue

        # Step 4: Create final result and report metrics
        final_result = IndividualsList(
            individuals=all_individuals,
            totalCount=len(all_individuals),
            extractionDate=datetime.now().isoformat()
        )

        # Report final metrics
        metrics = self.progress_tracker.calculate_final_metrics(len(individual_texts), successful_extractions)
        metrics["API calls made"] = f"{self.openai_client.api_calls_made}"
        self.progress_tracker.report_metrics("Individual Extraction Metrics", metrics)

        pipeline_logger.info(f"✅ Individual extraction completed: {final_result.totalCount} individuals extracted")
        return final_result

    def extract_entities(self, text: str) -> EntitiesList:
        """
        Extract sanctioned entities from text using AI.

        This method orchestrates the complete entity extraction workflow:
        1. Split text into entity records
        2. Process each record with AI
        3. Save results incrementally
        4. Track progress and metrics

        Args:
            text: The raw text containing sanctions data

        Returns:
            EntitiesList containing all extracted entities
        """
        # Step 1: Parse text into entity records
        entity_texts = split_entities_text(text)

        if not entity_texts:
            pipeline_logger.warning("No entity records found in text")
            return EntitiesList(entities=[], totalCount=0, extractionDate=datetime.now().isoformat())

        # Step 2: Initialize processing
        pipeline_logger.info(f"🏢 Starting AI extraction for {len(entity_texts)} entities")

        # Ensure file manager is initialized for entities (may have been done already for individuals)
        if not self.file_manager.files_initialized:
            existing_counts = self.file_manager.get_existing_record_counts()
            if existing_counts["individuals"] > 0 or existing_counts["entities"] > 0:
                pipeline_logger.info(f"📊 Found existing data: {existing_counts['individuals']} individuals, {existing_counts['entities']} entities")
                self.file_manager.initialize_output_files(append_mode=True)
            else:
                self.file_manager.initialize_output_files(append_mode=False)

        # Reset progress tracker for entities
        entity_progress_tracker = ProgressTracker()
        entity_progress_tracker.start_processing()

        # Step 3: Process each entity record
        all_entities = []
        successful_extractions = 0

        for i, entity_text in enumerate(entity_texts, 1):
            record_start_time = time.time()

            # Track progress
            entity_progress_tracker.report_progress(i, len(entity_texts), "entities",
                                                  f"Processing and saving entity {i}")

            try:
                # AI extraction using OpenAI client
                result = self.openai_client.extract_entity_structured(entity_text)

                # Process results
                all_entities.extend(result.entities)
                successful_extractions += 1

                # Save each entity immediately
                for entity in result.entities:
                    self.file_manager.save_entity_record(entity)

                # Track timing
                processing_time = entity_progress_tracker.track_record_processing(record_start_time)

                # Show examples for first few records
                if i <= 2 and result.entities:
                    entity = result.entities[0]
                    structured_data = {
                        "Organization": entity.organizationName,
                        "Entity Type": entity.entityType,
                        "Sanction ID": entity.sanctionId,
                        "Group ID": entity.groupId
                    }
                    entity_progress_tracker.show_example_output(i, entity_text, structured_data,
                                                             processing_time, is_individual=False)

            except Exception as e:
                entity_progress_tracker.increment_errors()
                pipeline_logger.error(f"Error extracting entity {i}: {str(e)}")
                continue

        # Step 4: Create final result and report metrics
        final_result = EntitiesList(
            entities=all_entities,
            totalCount=len(all_entities),
            extractionDate=datetime.now().isoformat()
        )

        # Report final metrics
        metrics = entity_progress_tracker.calculate_final_metrics(len(entity_texts), successful_extractions)
        metrics["Additional API calls"] = f"{successful_extractions}"
        entity_progress_tracker.report_metrics("Entity Extraction Metrics", metrics)

        pipeline_logger.info(f"✅ Entity extraction completed: {final_result.totalCount} entities extracted")
        return final_result

    def extract_all(self, text: str) -> Tuple[IndividualsList, EntitiesList]:
        """
        Extract both individuals and entities from the sanctions text.

        This is the main entry point for complete data extraction.

        Args:
            text: The raw text containing sanctions data

        Returns:
            Tuple of (IndividualsList, EntitiesList)
        """
        individuals = self.extract_individuals(text)
        entities = self.extract_entities(text)
        return individuals, entities

    def get_cost_estimate(self):
        """
        Get cost estimate from the OpenAI client.

        Returns:
            Cost estimate dictionary with usage statistics
        """
        return self.openai_client.get_cost_estimate()

    def save_results(self, individuals: IndividualsList, entities: EntitiesList,
                    output_path: str = "output/extracted_data.json"):
        """
        Save final combined extraction results.

        Args:
            individuals: Extracted individuals data
            entities: Extracted entities data
            output_path: Path to save the main JSON file
        """
        self.file_manager.save_final_results(individuals, entities, output_path)


def process_sanctions_with_llm(text_file_path: str = "output/Cyber_text.txt") -> Tuple[IndividualsList, EntitiesList]:
    """
    Main function to process sanctions text with LLM extraction.

    This is a simple, clean entry point that demonstrates the complete workflow.

    Args:
        text_file_path: Path to the text file to process

    Returns:
        Tuple of extracted individuals and entities
    """
    # Step 1: Read the input text
    text = read_text_file(text_file_path)

    # Step 2: Initialize the extractor
    extractor = LLMExtractor()

    # Step 3: Extract data with progress tracking
    individuals, entities = extractor.extract_all(text)

    # Step 4: Get cost estimates and save results
    cost_info = extractor.get_cost_estimate()
    extractor.save_results(individuals, entities)

    # Step 5: Report final metrics
    pipeline_logger.metrics("💰 OpenAI API Usage & Cost Estimate", cost_info)

    # Step 6: Print summary
    pipeline_logger.info("")
    pipeline_logger.info("🎯 Final Extraction Summary:")
    pipeline_logger.info(f"   • Individuals extracted: {individuals.totalCount}")
    pipeline_logger.info(f"   • Entities extracted: {entities.totalCount}")
    pipeline_logger.info(f"   • Total API calls: {cost_info['total_api_calls']}")
    pipeline_logger.info(f"   • Estimated cost: {cost_info['estimated_cost']}")

    return individuals, entities


if __name__ == "__main__":
    # Run extraction when module is executed directly
    try:
        individuals, entities = process_sanctions_with_llm()
    except Exception as e:
        pipeline_logger.error(f"Extraction failed: {e}")
        exit(1)
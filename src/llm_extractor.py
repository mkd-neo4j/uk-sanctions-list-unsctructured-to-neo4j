"""
LLM-based extraction module for UK sanctions data.
Uses OpenAI's structured output feature with Pydantic models.
"""

import os
import json
import re
import time
from typing import Tuple, Optional, List
from datetime import datetime
from pathlib import Path

from openai import OpenAI
from pydantic import BaseModel
from dotenv import load_dotenv

from src.models import SanctionedIndividual, IndividualsList, SanctionedEntity, EntitiesList
from src.logger_config import pipeline_logger


# Load environment variables
load_dotenv()


class LLMExtractor:
    """Handles extraction of structured data from sanctions text using LLM."""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the LLM extractor.

        Args:
            api_key: OpenAI API key. If not provided, will look for OPENAI_API_KEY env var.
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key must be provided or set in OPENAI_API_KEY environment variable")

        self.client = OpenAI(api_key=self.api_key)
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

        # Performance and cost tracking
        self.api_calls_made = 0
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.processing_times = []
        self.extraction_errors = 0

        # Output file paths for incremental saving
        self.individuals_output_path = None
        self.entities_output_path = None

    def _split_individuals_text(self, text: str) -> List[str]:
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

    def _split_entities_text(self, text: str) -> List[str]:
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

    def _initialize_output_files(self, output_dir: str = "output"):
        """
        Initialize empty JSON array files for incremental saving.

        Args:
            output_dir: Directory to create output files in
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        self.individuals_output_path = output_path / "individuals_extracted.json"
        self.entities_output_path = output_path / "entities_extracted.json"

        # Initialize empty JSON arrays
        with open(self.individuals_output_path, 'w', encoding='utf-8') as f:
            json.dump([], f)

        with open(self.entities_output_path, 'w', encoding='utf-8') as f:
            json.dump([], f)

        pipeline_logger.info(f"📁 Initialized output files:")
        pipeline_logger.info(f"   • {self.individuals_output_path}")
        pipeline_logger.info(f"   • {self.entities_output_path}")

    def _append_to_json_file(self, file_path: Path, new_record: dict):
        """
        Safely append a new record to a JSON array file.

        Args:
            file_path: Path to the JSON file
            new_record: Record to append
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

    def extract_individuals(self, text: str) -> IndividualsList:
        """
        Extract sanctioned individuals from text using structured output.
        Processes one individual record at a time for better accuracy.

        Args:
            text: The raw text containing sanctions data

        Returns:
            IndividualsList containing all extracted individuals
        """
        # Split text into individual records
        individual_texts = self._split_individuals_text(text)

        if not individual_texts:
            pipeline_logger.warning("No individual records found in text")
            return IndividualsList(individuals=[], totalCount=0, extractionDate=datetime.now().isoformat())

        pipeline_logger.info(f"🤖 Starting LLM extraction for {len(individual_texts)} individuals")
        pipeline_logger.info(f"🔧 Using model: {self.model}")

        # Initialize output files for incremental saving
        self._initialize_output_files()

        system_prompt = """You are a data extraction specialist for UK sanctions lists.
        Extract the INDIVIDUAL from the provided text record. This text contains exactly ONE individual record.

        Extract:
        - All name components (name1-name6 as they appear)
        - Parse names into firstName, middleName, lastName where possible
        - Date and place of birth
        - Nationality and passport information
        - All aliases (AKAs)
        - Address information (parse into structured components)
        - Group ID, listing dates, and UK sanctions reference
        - Complete statement of reasons
        - Any other relevant information

        For addresses, always provide both:
        - rawAddress: The complete address string as it appears
        - Structured components: Parse into addressLine1, addressLine2, postTown, region, country where possible

        Address parsing examples:
        - "Moscow, Russia" → postTown: "Moscow", country: "Russia"
        - "Room 1102, Guanfu Mansion, 46 Xinkai Road, Hedong District, Tianjin, China" →
          addressLine1: "46 Xinkai Road", addressLine2: "Room 1102, Guanfu Mansion",
          postTown: "Tianjin", region: "Hedong District", country: "China"

        Important:
        - This record contains exactly ONE individual
        - Extract ONLY individuals, not entities/organizations
        - Preserve the exact format of dates as they appear
        - Include all aliases in the aliases array
        - The sanctionId should combine the UK ref and group ID (e.g., "CYB0071-16753")
        - Always preserve the full rawAddress string
        """

        all_individuals = []
        successful_extractions = 0
        start_time = time.time()

        for i, individual_text in enumerate(individual_texts, 1):
            record_start_time = time.time()

            # Progress tracking
            pipeline_logger.progress(i, len(individual_texts), "individuals", f"Processing and saving record {i}")

            user_prompt = f"""Extract the sanctioned INDIVIDUAL from the following single record.
            Return structured data for this one individual.

            INDIVIDUAL RECORD:
            {individual_text}
            """

            try:
                response = self.client.beta.chat.completions.parse(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    response_format=IndividualsList,
                    # temperature=0,  # Use deterministic output
                    # max_tokens=16000
                )

                # Track API usage
                self.api_calls_made += 1
                if hasattr(response, 'usage'):
                    self.total_input_tokens += response.usage.prompt_tokens
                    self.total_output_tokens += response.usage.completion_tokens

                result = response.choices[0].message.parsed
                # Add individuals from this extraction to our master list
                all_individuals.extend(result.individuals)
                successful_extractions += 1

                # Save each individual to file immediately
                for individual in result.individuals:
                    self._append_to_json_file(self.individuals_output_path, individual.model_dump())

                # Track processing time
                record_time = time.time() - record_start_time
                self.processing_times.append(record_time)

                # Show detailed example for the first record (raw input vs structured output)
                if i == 1 and result.individuals:
                    individual = result.individuals[0]

                    # Show raw input
                    pipeline_logger.info("")
                    pipeline_logger.info("🔍 EXAMPLE: Raw Input vs Structured Output")
                    pipeline_logger.info("=" * 60)
                    pipeline_logger.info("📄 RAW INPUT TEXT:")
                    # Show first 300 characters of raw input
                    raw_preview = individual_text[:300] + "..." if len(individual_text) > 300 else individual_text
                    pipeline_logger.info(f"   {raw_preview}")

                    pipeline_logger.info("")
                    pipeline_logger.info("🤖 AI STRUCTURED OUTPUT:")
                    structured_data = {
                        "Name": f"{individual.firstName or ''} {individual.lastName or ''}".strip(),
                        "Sanction ID": individual.sanctionId,
                        "Nationality": individual.nationality,
                        "Date of Birth": individual.dateOfBirth or "Not provided",
                        "Passport Number": individual.passportNumber or "Not provided",
                        "Group ID": individual.groupId,
                        "Aliases": f"{len(individual.aliases)} aliases" if individual.aliases else "No aliases",
                        "Address": individual.address.rawAddress if individual.address else "No address",
                        "Statement Length": f"{len(individual.statementOfReasons)} characters" if individual.statementOfReasons else "No statement"
                    }

                    for key, value in structured_data.items():
                        pipeline_logger.info(f"   • {key}: {value}")

                    pipeline_logger.info(f"   • Processing time: {record_time:.2f}s")
                    pipeline_logger.info("=" * 60)

                # Show brief data for other early records
                elif i <= 3 and result.individuals:
                    individual = result.individuals[0]
                    sample_data = {
                        "Name": f"{individual.firstName or ''} {individual.lastName or ''}".strip(),
                        "Sanction ID": individual.sanctionId,
                        "Processing time": f"{record_time:.2f}s"
                    }
                    pipeline_logger.data_sample(f"Individual {i} Extracted", sample_data)

            except Exception as e:
                self.extraction_errors += 1
                pipeline_logger.error(f"Error extracting individual {i}: {str(e)}")
                continue

        # Calculate final metrics
        total_time = time.time() - start_time
        avg_time_per_record = sum(self.processing_times) / len(self.processing_times) if self.processing_times else 0

        # Create final result
        final_result = IndividualsList(
            individuals=all_individuals,
            totalCount=len(all_individuals),
            extractionDate=datetime.now().isoformat()
        )

        # Report extraction metrics
        pipeline_logger.metrics("Individual Extraction Metrics", {
            "Records processed": f"{len(individual_texts)}",
            "Successful extractions": f"{successful_extractions}",
            "Failed extractions": f"{self.extraction_errors}",
            "Success rate": f"{(successful_extractions/len(individual_texts)*100):.1f}%",
            "Total processing time": f"{total_time:.1f}s",
            "Average time per record": f"{avg_time_per_record:.2f}s",
            "API calls made": f"{self.api_calls_made}"
        })

        pipeline_logger.info(f"✅ Individual extraction completed: {final_result.totalCount} individuals extracted")
        return final_result

    def extract_entities(self, text: str) -> EntitiesList:
        """
        Extract sanctioned entities/organizations from text using structured output.
        Processes one entity record at a time for better accuracy.

        Args:
            text: The raw text containing sanctions data

        Returns:
            EntitiesList containing all extracted entities
        """
        # Split text into individual entity records
        entity_texts = self._split_entities_text(text)

        if not entity_texts:
            pipeline_logger.warning("No entity records found in text")
            return EntitiesList(entities=[], totalCount=0, extractionDate=datetime.now().isoformat())

        pipeline_logger.info(f"🏢 Starting LLM extraction for {len(entity_texts)} entities")

        # Initialize output files for incremental saving
        self._initialize_output_files()

        system_prompt = """You are a data extraction specialist for UK sanctions lists.
        Extract the ENTITY/ORGANIZATION from the provided text record. This text contains exactly ONE entity record.

        Extract:
        - Organization name
        - All aliases (AKAs)
        - Entity type (MILITARY, BUSINESS, GOVERNMENT, etc.) - infer if not explicit
        - Address information (parse into structured components)
        - Group ID, listing dates, and UK sanctions reference
        - Complete statement of reasons
        - Parent organization if mentioned
        - Any related entities or units
        - Any other relevant information

        For addresses, always provide both:
        - rawAddress: The complete address string as it appears
        - Structured components: Parse into addressLine1, addressLine2, postTown, region, country where possible

        Address parsing examples:
        - "22 Kirova Street, Moscow, Russia" → addressLine1: "22 Kirova Street", postTown: "Moscow", country: "Russia"
        - "2nd Floor, No. 16, Huashiyuan North Road, East Lake New Technology Development Zone, Hubei Province, Wuhan, China" →
          addressLine1: "No. 16, Huashiyuan North Road", addressLine2: "2nd Floor",
          postTown: "Wuhan", region: "East Lake New Technology Development Zone, Hubei Province", country: "China"

        Important:
        - This record contains exactly ONE entity/organization
        - Extract ONLY entities/organizations, not individuals
        - Preserve the exact format of dates as they appear
        - Include all aliases in the aliases array
        - The sanctionId should combine the UK ref and group ID (e.g., "CYB0097-16991")
        - Identify parent organizations from the statement of reasons when mentioned
        - Always preserve the full rawAddress string
        """

        all_entities = []
        entity_successful_extractions = 0
        entity_start_time = time.time()

        for i, entity_text in enumerate(entity_texts, 1):
            entity_record_start_time = time.time()

            # Progress tracking
            pipeline_logger.progress(i, len(entity_texts), "entities", f"Processing and saving entity {i}")

            user_prompt = f"""Extract the sanctioned ENTITY/ORGANIZATION from the following single record.
            Return structured data for this one entity.

            ENTITY RECORD:
            {entity_text}
            """

            try:
                response = self.client.beta.chat.completions.parse(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    response_format=EntitiesList,
                    # temperature=0,  # Use deterministic output
                    # max_tokens=16000
                )

                # Track API usage
                self.api_calls_made += 1
                if hasattr(response, 'usage'):
                    self.total_input_tokens += response.usage.prompt_tokens
                    self.total_output_tokens += response.usage.completion_tokens

                result = response.choices[0].message.parsed
                # Add entities from this extraction to our master list
                all_entities.extend(result.entities)
                entity_successful_extractions += 1

                # Save each entity to file immediately
                for entity in result.entities:
                    self._append_to_json_file(self.entities_output_path, entity.model_dump())

                # Track processing time
                entity_record_time = time.time() - entity_record_start_time
                self.processing_times.append(entity_record_time)

                # Show detailed example for the first entity record (raw input vs structured output)
                if i == 1 and result.entities:
                    entity = result.entities[0]

                    # Show raw input
                    pipeline_logger.info("")
                    pipeline_logger.info("🔍 ENTITY EXAMPLE: Raw Input vs Structured Output")
                    pipeline_logger.info("=" * 60)
                    pipeline_logger.info("📄 RAW INPUT TEXT:")
                    # Show first 300 characters of raw input
                    entity_raw_preview = entity_text[:300] + "..." if len(entity_text) > 300 else entity_text
                    pipeline_logger.info(f"   {entity_raw_preview}")

                    pipeline_logger.info("")
                    pipeline_logger.info("🤖 AI STRUCTURED OUTPUT:")
                    entity_structured_data = {
                        "Organization Name": entity.organizationName,
                        "Entity Type": entity.entityType,
                        "Sanction ID": entity.sanctionId,
                        "Group ID": entity.groupId,
                        "Aliases": f"{len(entity.aliases)} aliases" if entity.aliases else "No aliases",
                        "Address": entity.address.rawAddress if entity.address else "No address",
                        "Parent Company": entity.parentCompany or "None identified",
                        "Statement Length": f"{len(entity.statementOfReasons)} characters" if entity.statementOfReasons else "No statement"
                    }

                    for key, value in entity_structured_data.items():
                        pipeline_logger.info(f"   • {key}: {value}")

                    pipeline_logger.info(f"   • Processing time: {entity_record_time:.2f}s")
                    pipeline_logger.info("=" * 60)

                # Show brief data for other early records
                elif i <= 2 and result.entities:
                    entity = result.entities[0]
                    sample_data = {
                        "Organization": entity.organizationName,
                        "Entity Type": entity.entityType,
                        "Sanction ID": entity.sanctionId,
                        "Processing time": f"{entity_record_time:.2f}s"
                    }
                    pipeline_logger.data_sample(f"Entity {i} Extracted", sample_data)

            except Exception as e:
                self.extraction_errors += 1
                pipeline_logger.error(f"Error extracting entity {i}: {str(e)}")
                continue

        # Calculate final metrics
        entity_total_time = time.time() - entity_start_time

        # Create final result
        final_result = EntitiesList(
            entities=all_entities,
            totalCount=len(all_entities),
            extractionDate=datetime.now().isoformat()
        )

        # Report extraction metrics
        pipeline_logger.metrics("Entity Extraction Metrics", {
            "Records processed": f"{len(entity_texts)}",
            "Successful extractions": f"{entity_successful_extractions}",
            "Failed extractions": f"{len(entity_texts) - entity_successful_extractions}",
            "Success rate": f"{(entity_successful_extractions/len(entity_texts)*100):.1f}%",
            "Total processing time": f"{entity_total_time:.1f}s",
            "Additional API calls": f"{entity_successful_extractions}"
        })

        pipeline_logger.info(f"✅ Entity extraction completed: {final_result.totalCount} entities extracted")
        return final_result

    def extract_all(self, text: str) -> Tuple[IndividualsList, EntitiesList]:
        """
        Extract both individuals and entities from the sanctions text.

        Args:
            text: The raw text containing sanctions data

        Returns:
            Tuple of (IndividualsList, EntitiesList)
        """
        individuals = self.extract_individuals(text)
        entities = self.extract_entities(text)
        return individuals, entities

    def get_cost_estimate(self) -> dict:
        """
        Calculate estimated OpenAI API costs based on token usage.
        Uses configurable pricing from environment variables.
        """
        # Get pricing from environment variables with defaults
        input_cost_per_million = float(os.getenv("OPENAI_INPUT_COST_PER_MILLION", "0.150"))
        output_cost_per_million = float(os.getenv("OPENAI_OUTPUT_COST_PER_MILLION", "0.600"))

        input_cost = (self.total_input_tokens / 1_000_000) * input_cost_per_million
        output_cost = (self.total_output_tokens / 1_000_000) * output_cost_per_million
        total_cost = input_cost + output_cost

        return {
            "model_used": self.model,
            "total_api_calls": self.api_calls_made,
            "input_tokens": f"{self.total_input_tokens:,}",
            "output_tokens": f"{self.total_output_tokens:,}",
            "input_cost_per_1M": f"${input_cost_per_million:.3f}",
            "output_cost_per_1M": f"${output_cost_per_million:.3f}",
            "estimated_cost": f"${total_cost:.4f}",
            "input_cost": f"${input_cost:.4f}",
            "output_cost": f"${output_cost:.4f}"
        }

    def save_results(self, individuals: IndividualsList, entities: EntitiesList, output_path: str = "output/extracted_data.json"):
        """
        Save final combined extraction results. Individual files already saved incrementally.

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


def process_sanctions_with_llm(text_file_path: str = "output/Cyber_text.txt") -> Tuple[IndividualsList, EntitiesList]:
    """
    Main function to process sanctions text with LLM extraction.

    Args:
        text_file_path: Path to the text file to process

    Returns:
        Tuple of extracted individuals and entities
    """
    # Read the text file
    pipeline_logger.info(f"📄 Reading text from {text_file_path}")
    with open(text_file_path, 'r', encoding='utf-8') as f:
        text = f.read()

    pipeline_logger.info(f"📊 Text file loaded: {len(text):,} characters")

    # Initialize extractor
    extractor = LLMExtractor()

    # Extract data with progress tracking
    individuals, entities = extractor.extract_all(text)

    # Get cost estimates
    cost_info = extractor.get_cost_estimate()

    # Save results
    extractor.save_results(individuals, entities)

    # Report final API usage and costs
    pipeline_logger.metrics("💰 OpenAI API Usage & Cost Estimate", cost_info)

    # Print summary
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
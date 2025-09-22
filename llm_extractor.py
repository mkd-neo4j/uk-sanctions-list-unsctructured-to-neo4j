"""
LLM-based extraction module for UK sanctions data.
Uses OpenAI's structured output feature with Pydantic models.
"""

import os
import json
import re
from typing import Tuple, Optional, List
from datetime import datetime
from pathlib import Path

from openai import OpenAI
from pydantic import BaseModel
from dotenv import load_dotenv

from models import SanctionedIndividual, IndividualsList, SanctionedEntity, EntitiesList


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
        self.model = "gpt-4o-mini"  # Using the recommended model for structured outputs

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

        print(f"Split text into {len(individuals)} individual records")
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

        print(f"Split text into {len(entities)} entity records")
        return entities

    def extract_individuals(self, text: str) -> IndividualsList:
        """
        Extract sanctioned individuals from text using structured output.
        Processes one individual record at a time for better accuracy.

        Args:
            text: The raw text containing sanctions data

        Returns:
            IndividualsList containing all extracted individuals
        """
        print("Extracting individuals using LLM...")

        # Split text into individual records
        individual_texts = self._split_individuals_text(text)

        if not individual_texts:
            print("No individual records found in text")
            return IndividualsList(individuals=[], totalCount=0, extractionDate=datetime.now().isoformat())

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

        for i, individual_text in enumerate(individual_texts, 1):
            print(f"Processing individual record {i}/{len(individual_texts)}")

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
                    temperature=0,  # Use deterministic output
                    max_tokens=16000
                )

                result = response.choices[0].message.parsed
                # Add individuals from this extraction to our master list
                all_individuals.extend(result.individuals)

            except Exception as e:
                print(f"Error extracting individual {i}: {e}")
                continue

        # Create final result
        final_result = IndividualsList(
            individuals=all_individuals,
            totalCount=len(all_individuals),
            extractionDate=datetime.now().isoformat()
        )

        print(f"Successfully extracted {final_result.totalCount} individuals")
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
        print("Extracting entities using LLM...")

        # Split text into individual entity records
        entity_texts = self._split_entities_text(text)

        if not entity_texts:
            print("No entity records found in text")
            return EntitiesList(entities=[], totalCount=0, extractionDate=datetime.now().isoformat())

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

        for i, entity_text in enumerate(entity_texts, 1):
            print(f"Processing entity record {i}/{len(entity_texts)}")

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
                    temperature=0,  # Use deterministic output
                    max_tokens=16000
                )

                result = response.choices[0].message.parsed
                # Add entities from this extraction to our master list
                all_entities.extend(result.entities)

            except Exception as e:
                print(f"Error extracting entity {i}: {e}")
                continue

        # Create final result
        final_result = EntitiesList(
            entities=all_entities,
            totalCount=len(all_entities),
            extractionDate=datetime.now().isoformat()
        )

        print(f"Successfully extracted {final_result.totalCount} entities")
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

    def save_results(self, individuals: IndividualsList, entities: EntitiesList, output_path: str = "output/extracted_data.json"):
        """
        Save extraction results to a JSON file.

        Args:
            individuals: Extracted individuals data
            entities: Extracted entities data
            output_path: Path to save the JSON file
        """
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

        # Ensure output directory exists
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)

        print(f"Results saved to {output_path}")


def process_sanctions_with_llm(text_file_path: str = "output/Cyber_text.txt") -> Tuple[IndividualsList, EntitiesList]:
    """
    Main function to process sanctions text with LLM extraction.

    Args:
        text_file_path: Path to the text file to process

    Returns:
        Tuple of extracted individuals and entities
    """
    # Read the text file
    print(f"Reading text from {text_file_path}")
    with open(text_file_path, 'r', encoding='utf-8') as f:
        text = f.read()

    # Initialize extractor
    extractor = LLMExtractor()

    # Extract data
    individuals, entities = extractor.extract_all(text)

    # Save results
    extractor.save_results(individuals, entities)

    # Print summary
    print("\n=== Extraction Summary ===")
    print(f"Individuals extracted: {individuals.totalCount}")
    print(f"Entities extracted: {entities.totalCount}")

    return individuals, entities


if __name__ == "__main__":
    # Run extraction when module is executed directly
    try:
        individuals, entities = process_sanctions_with_llm()
    except Exception as e:
        print(f"Extraction failed: {e}")
        exit(1)
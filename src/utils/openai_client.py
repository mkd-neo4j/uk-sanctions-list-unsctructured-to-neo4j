"""
OpenAI API utilities for structured data extraction.
Handles client configuration, API calls, and cost tracking.
"""

import os
from typing import Dict, Any, Optional
from openai import OpenAI
from src.models import IndividualsList, EntitiesList
from src.logger_config import pipeline_logger


class OpenAIClient:
    """Manages OpenAI API interactions with cost and usage tracking."""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize OpenAI client with API key and model configuration.

        Args:
            api_key: OpenAI API key. If not provided, reads from OPENAI_API_KEY env var.
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key must be provided or set in OPENAI_API_KEY environment variable")

        self.client = OpenAI(api_key=self.api_key)
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

        # Usage tracking
        self.api_calls_made = 0
        self.total_input_tokens = 0
        self.total_output_tokens = 0

    def extract_individual_structured(self, individual_text: str) -> IndividualsList:
        """
        Extract structured individual data from text using OpenAI API.

        Args:
            individual_text: Text containing individual sanctions record

        Returns:
            IndividualsList with extracted data
        """
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

        user_prompt = f"""Extract the sanctioned INDIVIDUAL from the following single record.
        Return structured data for this one individual.

        INDIVIDUAL RECORD:
        {individual_text}
        """

        return self._make_structured_api_call(system_prompt, user_prompt, IndividualsList)

    def extract_entity_structured(self, entity_text: str) -> EntitiesList:
        """
        Extract structured entity data from text using OpenAI API.

        Args:
            entity_text: Text containing entity sanctions record

        Returns:
            EntitiesList with extracted data
        """
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

        user_prompt = f"""Extract the sanctioned ENTITY/ORGANIZATION from the following single record.
        Return structured data for this one entity.

        ENTITY RECORD:
        {entity_text}
        """

        return self._make_structured_api_call(system_prompt, user_prompt, EntitiesList)

    def _make_structured_api_call(self, system_prompt: str, user_prompt: str, response_format):
        """
        Make a structured API call to OpenAI with usage tracking.

        Args:
            system_prompt: System instructions for the model
            user_prompt: User query/data to process
            response_format: Pydantic model for structured response

        Returns:
            Parsed response object
        """
        try:
            response = self.client.beta.chat.completions.parse(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format=response_format
            )

            # Track API usage
            self.api_calls_made += 1
            if hasattr(response, 'usage'):
                self.total_input_tokens += response.usage.prompt_tokens
                self.total_output_tokens += response.usage.completion_tokens

            return response.choices[0].message.parsed

        except Exception as e:
            pipeline_logger.error(f"OpenAI API call failed: {str(e)}")
            raise

    def get_cost_estimate(self) -> Dict[str, Any]:
        """
        Calculate estimated OpenAI API costs based on token usage.
        Uses configurable pricing from environment variables.

        Returns:
            Dictionary with cost breakdown and usage statistics
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
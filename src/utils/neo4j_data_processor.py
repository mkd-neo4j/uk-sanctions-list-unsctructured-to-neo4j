"""
Data processing utilities for Neo4j loading.
Handles data transformation, validation, and filtering for sanctions data.
"""

import json
import uuid
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
import re

from src.logger_config import pipeline_logger
from src.models import SanctionedIndividual, SanctionedEntity, Address


class Neo4jDataProcessor:
    """
    Processor for transforming JSON sanctions data into Neo4j-compatible format.

    Handles filtering of null/empty values, data validation, and preparation
    of data for Cypher query execution.
    """

    def __init__(self):
        """Initialize the data processor."""
        self.processed_individuals = 0
        self.processed_entities = 0
        self.filtered_properties = 0

    @staticmethod
    def is_empty_value(value: Any) -> bool:
        """
        Check if a value should be considered empty and filtered out.

        Args:
            value: The value to check

        Returns:
            True if value should be filtered out, False otherwise
        """
        if value is None:
            return True

        if isinstance(value, str):
            # Check for various empty/null representations
            cleaned = value.strip().lower()
            empty_patterns = ["", "null", "n/a", "na", "none", "undefined"]
            return cleaned in empty_patterns

        if isinstance(value, (list, dict)):
            return len(value) == 0

        return False

    @staticmethod
    def filter_empty_values(data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Filter out empty values from a dictionary.

        Args:
            data: Input dictionary

        Returns:
            Dictionary with empty values removed
        """
        filtered = {}

        for key, value in data.items():
            if not Neo4jDataProcessor.is_empty_value(value):
                if isinstance(value, dict):
                    # Recursively filter nested dictionaries
                    filtered_nested = Neo4jDataProcessor.filter_empty_values(value)
                    if filtered_nested:  # Only include if not empty after filtering
                        filtered[key] = filtered_nested
                elif isinstance(value, list):
                    # Filter lists, removing empty items
                    filtered_list = [
                        item for item in value
                        if not Neo4jDataProcessor.is_empty_value(item)
                    ]
                    if filtered_list:  # Only include if not empty after filtering
                        filtered[key] = filtered_list
                else:
                    filtered[key] = value

        return filtered

    @staticmethod
    def normalize_date(date_string: str) -> Optional[str]:
        """
        Normalize date strings to ISO format.

        Args:
            date_string: Date in various formats (DD/MM/YYYY, etc.)

        Returns:
            ISO formatted date string or None if invalid
        """
        if not date_string or Neo4jDataProcessor.is_empty_value(date_string):
            return None

        try:
            # Clean the date string first
            cleaned = date_string.strip()

            # Remove common trailing punctuation
            cleaned = cleaned.rstrip('.,;:')

            # Handle complex date strings with multiple dates
            # e.g., "(1) 21/02/1961. (2) 21/01/1961." - take the first date
            if '(' in cleaned and ')' in cleaned:
                # Extract first date pattern found
                date_match = re.search(r'\d{2}/\d{2}/\d{4}', cleaned)
                if date_match:
                    cleaned = date_match.group(0)

            # Handle DD/MM/YYYY format
            if re.match(r'^\d{2}/\d{2}/\d{4}$', cleaned):
                day, month, year = cleaned.split('/')
                # Validate components
                if 1 <= int(day) <= 31 and 1 <= int(month) <= 12:
                    return f"{year}-{month.zfill(2)}-{day.zfill(2)}"

            # Handle YYYY-MM-DD format (already ISO)
            if re.match(r'^\d{4}-\d{2}-\d{2}$', cleaned):
                return cleaned

            # If we can't parse it, return None instead of bad data
            pipeline_logger.warning(f"Could not normalize date: {date_string}")
            return None

        except Exception as e:
            pipeline_logger.warning(f"Date normalization failed for '{date_string}': {e}")
            return None

    @staticmethod
    def normalize_alias(alias_name: str) -> str:
        """
        Normalize alias names for consistent matching.

        Args:
            alias_name: Original alias name

        Returns:
            Normalized alias ID for matching
        """
        if not alias_name:
            return ""

        # Convert to lowercase
        normalized = alias_name.lower()

        # Trim whitespace
        normalized = normalized.strip()

        # Collapse multiple spaces to single space
        normalized = re.sub(r'\s+', ' ', normalized)

        # Remove special characters (keep only alphanumeric and spaces)
        normalized = re.sub(r'[^a-z0-9\s]', '', normalized)

        # Basic Unicode normalization (remove accents)
        # This could be enhanced with proper Unicode normalization
        accent_map = {
            'é': 'e', 'è': 'e', 'ê': 'e', 'ë': 'e',
            'á': 'a', 'à': 'a', 'â': 'a', 'ä': 'a',
            'í': 'i', 'ì': 'i', 'î': 'i', 'ï': 'i',
            'ó': 'o', 'ò': 'o', 'ô': 'o', 'ö': 'o',
            'ú': 'u', 'ù': 'u', 'û': 'u', 'ü': 'u',
            'ñ': 'n', 'ç': 'c'
        }

        for accented, plain in accent_map.items():
            normalized = normalized.replace(accented, plain)

        return normalized

    @staticmethod
    def generate_unique_id(prefix: str = "") -> str:
        """
        Generate a unique identifier.

        Args:
            prefix: Optional prefix for the ID

        Returns:
            Unique identifier string
        """
        unique_id = str(uuid.uuid4())
        return f"{prefix}_{unique_id}" if prefix else unique_id

    def process_individual(self, individual_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process individual sanctions data for Neo4j loading.

        Args:
            individual_data: Raw individual data dictionary

        Returns:
            Processed data ready for Neo4j insertion
        """
        # Filter out empty values
        filtered_data = self.filter_empty_values(individual_data)

        # Normalize dates
        for date_field in ['dateOfBirth', 'listedOn', 'dateDesignated', 'lastUpdated', 'dateTrustServicesSanctionsImposed']:
            if date_field in filtered_data:
                normalized_date = self.normalize_date(filtered_data[date_field])
                if normalized_date:
                    filtered_data[date_field] = normalized_date
                else:
                    filtered_data.pop(date_field, None)

        # Process aliases
        if 'aliases' in filtered_data and filtered_data['aliases']:
            processed_aliases = []
            for alias in filtered_data['aliases']:
                if not self.is_empty_value(alias):
                    processed_aliases.append({
                        'aliasName': alias,
                        'aliasId': self.normalize_alias(alias),
                        'aliasType': 'UNKNOWN'  # Could be enhanced with alias type detection
                    })
            filtered_data['processed_aliases'] = processed_aliases

        # Process address if present
        if 'address' in filtered_data and filtered_data['address']:
            address_data = self.filter_empty_values(filtered_data['address'])
            if address_data:
                address_data['addressId'] = self.generate_unique_id('addr')
                # Validate and clean country field
                if 'country' in address_data:
                    validated_country = self.extract_country_from_location(address_data['country'])
                    if validated_country:
                        address_data['country'] = validated_country
                    else:
                        # Remove invalid country to prevent bad Country nodes
                        pipeline_logger.warning(f"Removing invalid country value: {address_data['country']}")
                        address_data.pop('country', None)
                filtered_data['address'] = address_data

        self.processed_individuals += 1
        return filtered_data

    def process_entity(self, entity_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process entity sanctions data for Neo4j loading.

        Args:
            entity_data: Raw entity data dictionary

        Returns:
            Processed data ready for Neo4j insertion
        """
        # Filter out empty values
        filtered_data = self.filter_empty_values(entity_data)

        # Normalize dates
        for date_field in ['listedOn', 'dateDesignated', 'lastUpdated']:
            if date_field in filtered_data:
                normalized_date = self.normalize_date(filtered_data[date_field])
                if normalized_date:
                    filtered_data[date_field] = normalized_date
                else:
                    filtered_data.pop(date_field, None)

        # Process aliases
        if 'aliases' in filtered_data and filtered_data['aliases']:
            processed_aliases = []
            for alias in filtered_data['aliases']:
                if not self.is_empty_value(alias):
                    processed_aliases.append({
                        'aliasName': alias,
                        'aliasId': self.normalize_alias(alias),
                        'aliasType': 'TRADENAME'  # Entities typically have trade names
                    })
            filtered_data['processed_aliases'] = processed_aliases

        # Process address if present
        if 'address' in filtered_data and filtered_data['address']:
            address_data = self.filter_empty_values(filtered_data['address'])
            if address_data:
                address_data['addressId'] = self.generate_unique_id('addr')
                # Validate and clean country field
                if 'country' in address_data:
                    validated_country = self.extract_country_from_location(address_data['country'])
                    if validated_country:
                        address_data['country'] = validated_country
                    else:
                        # Remove invalid country to prevent bad Country nodes
                        pipeline_logger.warning(f"Removing invalid country value: {address_data['country']}")
                        address_data.pop('country', None)
                filtered_data['address'] = address_data

        self.processed_entities += 1
        return filtered_data

    def load_individuals_json(self, json_file_path: str) -> List[Dict[str, Any]]:
        """
        Load and process individuals from JSON file.

        Args:
            json_file_path: Path to individuals JSON file

        Returns:
            List of processed individual dictionaries
        """
        try:
            with open(json_file_path, 'r', encoding='utf-8') as file:
                individuals_data = json.load(file)

            processed_individuals = []
            for individual in individuals_data:
                processed = self.process_individual(individual)
                if processed:  # Only include if processing was successful
                    processed_individuals.append(processed)

            pipeline_logger.info(f"📊 Processed {len(processed_individuals)} individuals from {json_file_path}")
            return processed_individuals

        except Exception as e:
            pipeline_logger.error(f"Failed to load individuals from {json_file_path}: {e}")
            return []

    def load_entities_json(self, json_file_path: str) -> List[Dict[str, Any]]:
        """
        Load and process entities from JSON file.

        Args:
            json_file_path: Path to entities JSON file

        Returns:
            List of processed entity dictionaries
        """
        try:
            with open(json_file_path, 'r', encoding='utf-8') as file:
                entities_data = json.load(file)

            processed_entities = []
            for entity in entities_data:
                processed = self.process_entity(entity)
                if processed:  # Only include if processing was successful
                    processed_entities.append(processed)

            pipeline_logger.info(f"🏢 Processed {len(processed_entities)} entities from {json_file_path}")
            return processed_entities

        except Exception as e:
            pipeline_logger.error(f"Failed to load entities from {json_file_path}: {e}")
            return []

    @staticmethod
    def get_valid_countries() -> Dict[str, Dict[str, str]]:
        """
        Get comprehensive mapping of valid countries.

        Returns:
            Dictionary mapping country names/variants to country info
        """
        return {
            'russia': {'code': 'RU', 'name': 'Russia'},
            'russian federation': {'code': 'RU', 'name': 'Russia'},
            'russian': {'code': 'RU', 'name': 'Russia'},
            'china': {'code': 'CN', 'name': 'China'},
            "people's republic of china": {'code': 'CN', 'name': 'China'},
            'chinese': {'code': 'CN', 'name': 'China'},
            'iran': {'code': 'IR', 'name': 'Iran'},
            'islamic republic of iran': {'code': 'IR', 'name': 'Iran'},
            'iranian': {'code': 'IR', 'name': 'Iran'},
            'north korea': {'code': 'KP', 'name': 'North Korea'},
            'democratic people\'s republic of korea': {'code': 'KP', 'name': 'North Korea'},
            'dprk': {'code': 'KP', 'name': 'North Korea'},
            'united kingdom': {'code': 'GB', 'name': 'United Kingdom'},
            'uk': {'code': 'GB', 'name': 'United Kingdom'},
            'great britain': {'code': 'GB', 'name': 'United Kingdom'},
            'britain': {'code': 'GB', 'name': 'United Kingdom'},
            'united states': {'code': 'US', 'name': 'United States'},
            'united states of america': {'code': 'US', 'name': 'United States'},
            'usa': {'code': 'US', 'name': 'United States'},
            'america': {'code': 'US', 'name': 'United States'},
            'ukraine': {'code': 'UA', 'name': 'Ukraine'},
            'kyrgyzstan': {'code': 'KG', 'name': 'Kyrgyzstan'},
            'kyrgyz republic': {'code': 'KG', 'name': 'Kyrgyzstan'},
            'kazakhstan': {'code': 'KZ', 'name': 'Kazakhstan'},
            'republic of kazakhstan': {'code': 'KZ', 'name': 'Kazakhstan'},
            'belarus': {'code': 'BY', 'name': 'Belarus'},
            'republic of belarus': {'code': 'BY', 'name': 'Belarus'},
            'syria': {'code': 'SY', 'name': 'Syria'},
            'syrian arab republic': {'code': 'SY', 'name': 'Syria'},
            'myanmar': {'code': 'MM', 'name': 'Myanmar'},
            'burma': {'code': 'MM', 'name': 'Myanmar'},
            'venezuela': {'code': 'VE', 'name': 'Venezuela'},
            'bolivia': {'code': 'BO', 'name': 'Bolivia'},
            'nicaragua': {'code': 'NI', 'name': 'Nicaragua'},
            'libya': {'code': 'LY', 'name': 'Libya'},
            'mali': {'code': 'ML', 'name': 'Mali'},
            'zimbabwe': {'code': 'ZW', 'name': 'Zimbabwe'},
            'serbia': {'code': 'RS', 'name': 'Serbia'},
            'turkey': {'code': 'TR', 'name': 'Turkey'},
            'turkiye': {'code': 'TR', 'name': 'Turkey'},
            'afghanistan': {'code': 'AF', 'name': 'Afghanistan'},
            'lebanon': {'code': 'LB', 'name': 'Lebanon'},
            'iraq': {'code': 'IQ', 'name': 'Iraq'},
            'somalia': {'code': 'SO', 'name': 'Somalia'},
            'sudan': {'code': 'SD', 'name': 'Sudan'},
            'yemen': {'code': 'YE', 'name': 'Yemen'},
            'cuba': {'code': 'CU', 'name': 'Cuba'},
            'moldova': {'code': 'MD', 'name': 'Moldova'},
            'georgia': {'code': 'GE', 'name': 'Georgia'},
            'armenia': {'code': 'AM', 'name': 'Armenia'},
            'azerbaijan': {'code': 'AZ', 'name': 'Azerbaijan'},
            'uzbekistan': {'code': 'UZ', 'name': 'Uzbekistan'},
            'tajikistan': {'code': 'TJ', 'name': 'Tajikistan'},
            'turkmenistan': {'code': 'TM', 'name': 'Turkmenistan'}
        }

    @staticmethod
    def extract_country_from_location(location_string: str) -> Optional[str]:
        """
        Extract country name from location string, handling comma-separated formats.

        Args:
            location_string: Location string that may contain region, city, country

        Returns:
            Valid country name or None if no valid country found
        """
        if not location_string or Neo4jDataProcessor.is_empty_value(location_string):
            return None

        # Get valid countries mapping
        valid_countries = Neo4jDataProcessor.get_valid_countries()

        # Clean the input
        cleaned = location_string.strip().lower()

        # If it contains commas, try extracting country from the last part
        if ',' in cleaned:
            parts = [part.strip() for part in cleaned.split(',')]
            # Try the last part first (most likely to be country)
            for part in reversed(parts):
                if part in valid_countries:
                    return valid_countries[part]['name']

        # If no commas or comma-based extraction failed, check the whole string
        if cleaned in valid_countries:
            return valid_countries[cleaned]['name']

        # No valid country found
        return None

    def extract_country_from_nationality(self, nationality: str) -> Optional[Dict[str, str]]:
        """
        Extract country information from nationality string.

        Args:
            nationality: Nationality string

        Returns:
            Dictionary with country code and name, or None
        """
        if not nationality or self.is_empty_value(nationality):
            return None

        valid_countries = self.get_valid_countries()
        normalized_nationality = nationality.lower().strip()
        return valid_countries.get(normalized_nationality)

    def get_processing_stats(self) -> Dict[str, int]:
        """
        Get processing statistics.

        Returns:
            Dictionary with processing statistics
        """
        return {
            'processed_individuals': self.processed_individuals,
            'processed_entities': self.processed_entities,
            'filtered_properties': self.filtered_properties
        }
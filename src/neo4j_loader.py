"""
Step 3: Neo4j Loading Module for UK sanctions data.
Clean orchestrator for loading JSON sanctions data into Neo4j database.
"""

import os
import time
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from dotenv import load_dotenv

from src.logger_config import pipeline_logger
from src.utils import (
    Neo4jClient,
    Neo4jDataProcessor,
    ProgressTracker,
    read_text_file
)

# Load environment variables
load_dotenv()


class Neo4jSanctionsLoader:
    """
    Clean orchestrator for loading sanctions data into Neo4j database.

    This class coordinates the Neo4j loading process using specialized utility modules,
    making it easy to understand and walk through with customers.
    """

    def __init__(self, neo4j_uri: str = None, neo4j_username: str = None,
                 neo4j_password: str = None, neo4j_database: str = None):
        """
        Initialize the Neo4j sanctions loader.

        Args:
            neo4j_uri: Neo4j connection URI (defaults to environment variable)
            neo4j_username: Neo4j username (defaults to environment variable)
            neo4j_password: Neo4j password (defaults to environment variable)
            neo4j_database: Neo4j database name (defaults to environment variable)
        """
        # Initialize core components
        self.neo4j_client = Neo4jClient(neo4j_uri, neo4j_username, neo4j_password, neo4j_database)
        self.data_processor = Neo4jDataProcessor()
        self.progress_tracker = ProgressTracker()

        # Load Cypher queries
        self.cypher_queries = self._load_cypher_queries()

    def _load_cypher_queries(self) -> Dict[str, str]:
        """
        Load Cypher queries from files.

        Returns:
            Dictionary mapping query names to query strings
        """
        cypher_dir = "cypher"
        query_files = {
            "load_individuals": "load_individuals.cypher",
            "load_individuals_aliases": "load_individuals_aliases.cypher",
            "load_individuals_address": "load_individuals_address.cypher",
            "load_entities": "load_entities.cypher",
            "load_entities_aliases": "load_entities_aliases.cypher",
            "load_entities_address": "load_entities_address.cypher",
            "load_entities_relationships": "load_entities_relationships.cypher"
        }

        queries = {}
        for name, filename in query_files.items():
            try:
                file_path = os.path.join(cypher_dir, filename)
                queries[name] = read_text_file(file_path)
                # Use info level logging instead of debug for better visibility
                pipeline_logger.info(f"📄 Loaded Cypher query: {name}")
            except Exception as e:
                pipeline_logger.warning(f"Could not load Cypher query {name} from {filename}: {e}")
                queries[name] = None

        return queries

    def setup_database(self) -> bool:
        """
        Set up Neo4j database connection and schema.

        Returns:
            True if setup successful, False otherwise
        """
        try:
            # Step 1: Connect to database
            if not self.neo4j_client.connect():
                return False

            # Step 2: Create constraints and indices
            pipeline_logger.info("🔧 Setting up database schema (constraints and indices)")
            if not self.neo4j_client.create_constraints_and_indices():
                pipeline_logger.warning("Database schema setup had issues but continuing...")

            pipeline_logger.info("✅ Neo4j database setup completed")
            return True

        except Exception as e:
            pipeline_logger.error(f"Database setup failed: {e}")
            return False

    def clear_existing_data(self) -> bool:
        """
        Clear existing sanctions data from the database.

        Returns:
            True if successful, False otherwise
        """
        try:
            pipeline_logger.info("🗑️ Clearing existing sanctions data")
            return self.neo4j_client.clear_sanctions_data()
        except Exception as e:
            pipeline_logger.error(f"Failed to clear existing data: {e}")
            return False

    def load_individuals(self, individuals_json_path: str = "output/individuals_extracted.json") -> int:
        """
        Load sanctioned individuals from JSON file into Neo4j.

        Args:
            individuals_json_path: Path to individuals JSON file

        Returns:
            Number of individuals loaded successfully
        """
        # Step 1: Load and process individuals data
        individuals_data = self.data_processor.load_individuals_json(individuals_json_path)

        if not individuals_data:
            pipeline_logger.warning("No individuals data to load")
            return 0

        # Step 2: Initialize processing
        pipeline_logger.info(f"👥 Starting Neo4j loading for {len(individuals_data)} individuals")
        self.progress_tracker.start_processing()

        loaded_count = 0
        failed_count = 0

        # Step 3: Process each individual
        for i, individual in enumerate(individuals_data, 1):
            record_start_time = time.time()

            # Track progress
            self.progress_tracker.report_progress(i, len(individuals_data), "individuals",
                                                f"Loading individual {i} into Neo4j")

            try:
                # Load main individual record
                if self._load_individual_record(individual):
                    loaded_count += 1

                    # Show example for first few records
                    if i <= 3:
                        processing_time = self.progress_tracker.track_record_processing(record_start_time)
                        example_data = {
                            "Sanction ID": individual.get("sanctionId"),
                            "Full Name": individual.get("fullName"),
                            "Nationality": individual.get("nationality"),
                            "Aliases": len(individual.get("processed_aliases", [])),
                            "Has Address": "Yes" if individual.get("address") else "No"
                        }
                        self.progress_tracker.show_example_output(i, f"Individual {i}", example_data,
                                                               processing_time, is_individual=True)
                else:
                    failed_count += 1

            except Exception as e:
                failed_count += 1
                self.progress_tracker.increment_errors()
                pipeline_logger.error(f"Failed to load individual {i}: {e}")
                continue

        # Step 4: Report metrics
        metrics = {
            "Total individuals": len(individuals_data),
            "Successfully loaded": loaded_count,
            "Failed to load": failed_count,
            "Success rate": f"{(loaded_count/len(individuals_data)*100):.1f}%" if individuals_data else "0%"
        }
        self.progress_tracker.report_metrics("Individual Loading Metrics", metrics)

        pipeline_logger.info(f"✅ Individual loading completed: {loaded_count}/{len(individuals_data)} loaded")
        return loaded_count

    def load_entities(self, entities_json_path: str = "output/entities_extracted.json") -> int:
        """
        Load sanctioned entities from JSON file into Neo4j.

        Args:
            entities_json_path: Path to entities JSON file

        Returns:
            Number of entities loaded successfully
        """
        # Step 1: Load and process entities data
        entities_data = self.data_processor.load_entities_json(entities_json_path)

        if not entities_data:
            pipeline_logger.warning("No entities data to load")
            return 0

        # Step 2: Initialize processing
        pipeline_logger.info(f"🏢 Starting Neo4j loading for {len(entities_data)} entities")
        entity_progress_tracker = ProgressTracker()
        entity_progress_tracker.start_processing()

        loaded_count = 0
        failed_count = 0

        # Step 3: Process each entity
        for i, entity in enumerate(entities_data, 1):
            record_start_time = time.time()

            # Track progress
            entity_progress_tracker.report_progress(i, len(entities_data), "entities",
                                                  f"Loading entity {i} into Neo4j")

            try:
                # Load main entity record
                if self._load_entity_record(entity):
                    loaded_count += 1

                    # Show example for first few records
                    if i <= 2:
                        processing_time = entity_progress_tracker.track_record_processing(record_start_time)
                        example_data = {
                            "Sanction ID": entity.get("sanctionId"),
                            "Organisation": entity.get("organisationName"),
                            "Entity Type": entity.get("entityType"),
                            "Aliases": len(entity.get("processed_aliases", [])),
                            "Has Address": "Yes" if entity.get("address") else "No"
                        }
                        entity_progress_tracker.show_example_output(i, f"Entity {i}", example_data,
                                                                 processing_time, is_individual=False)
                else:
                    failed_count += 1

            except Exception as e:
                failed_count += 1
                entity_progress_tracker.increment_errors()
                pipeline_logger.error(f"Failed to load entity {i}: {e}")
                continue

        # Step 4: Report metrics
        metrics = {
            "Total entities": len(entities_data),
            "Successfully loaded": loaded_count,
            "Failed to load": failed_count,
            "Success rate": f"{(loaded_count/len(entities_data)*100):.1f}%" if entities_data else "0%"
        }
        entity_progress_tracker.report_metrics("Entity Loading Metrics", metrics)

        pipeline_logger.info(f"✅ Entity loading completed: {loaded_count}/{len(entities_data)} loaded")
        return loaded_count

    def _load_individual_record(self, individual: Dict[str, Any]) -> bool:
        """
        Load a single individual record with all relationships.

        Args:
            individual: Processed individual data dictionary

        Returns:
            True if successful, False otherwise
        """
        try:
            # Ensure all required parameters are present with defaults
            individual_params = {
                'sanctionId': individual.get('sanctionId'),
                'ukSanctionsRef': individual.get('ukSanctionsRef'),
                'fullName': individual.get('fullName'),
                'firstName': individual.get('firstName'),
                'middleName': individual.get('middleName'),
                'lastName': individual.get('lastName'),
                'nameNonLatinScript': individual.get('nameNonLatinScript'),
                'dateOfBirth': individual.get('dateOfBirth'),
                'placeOfBirth': individual.get('placeOfBirth'),
                'gender': individual.get('gender'),
                'position': individual.get('position'),
                'passportNumber': individual.get('passportNumber'),
                'nationalIdentificationNumber': individual.get('nationalIdentificationNumber'),
                'nationality': individual.get('nationality'),
                'listedOn': individual.get('listedOn'),
                'dateDesignated': individual.get('dateDesignated'),
                'lastUpdated': individual.get('lastUpdated'),
                'dateTrustServicesSanctionsImposed': individual.get('dateTrustServicesSanctionsImposed'),
                'statementOfReasons': individual.get('statementOfReasons'),
                'otherInformation': individual.get('otherInformation'),
                'groupId': individual.get('groupId')
            }

            # Load main individual with prepared parameters
            main_query = self.cypher_queries.get("load_individuals")
            if main_query:
                self.neo4j_client.execute_query(main_query, individual_params)

            # Load aliases if present
            if individual.get("processed_aliases"):
                aliases_query = self.cypher_queries.get("load_individuals_aliases")
                if aliases_query:
                    self.neo4j_client.execute_query(aliases_query, {
                        "sanctionId": individual["sanctionId"],
                        "aliases": individual["processed_aliases"]
                    })

            # Load address if present
            if individual.get("address"):
                address_query = self.cypher_queries.get("load_individuals_address")
                if address_query:
                    self.neo4j_client.execute_query(address_query, {
                        "sanctionId": individual["sanctionId"],
                        "address": individual["address"]
                    })

            return True

        except Exception as e:
            pipeline_logger.error(f"Failed to load individual record {individual.get('sanctionId')}: {e}")
            return False

    def _load_entity_record(self, entity: Dict[str, Any]) -> bool:
        """
        Load a single entity record with all relationships.

        Args:
            entity: Processed entity data dictionary

        Returns:
            True if successful, False otherwise
        """
        try:
            # Ensure all required parameters are present with defaults
            entity_params = {
                'sanctionId': entity.get('sanctionId'),
                'ukSanctionsRef': entity.get('ukSanctionsRef'),
                'organisationName': entity.get('organisationName', entity.get('organizationName')),  # Handle both spellings
                'nameNonLatinScript': entity.get('nameNonLatinScript'),
                'entityType': entity.get('entityType'),
                'typeOfEntity': entity.get('typeOfEntity'),
                'registrationNumber': entity.get('registrationNumber'),
                'parentCompany': entity.get('parentCompany'),
                'listedOn': entity.get('listedOn'),
                'dateDesignated': entity.get('dateDesignated'),
                'lastUpdated': entity.get('lastUpdated'),
                'statementOfReasons': entity.get('statementOfReasons'),
                'otherInformation': entity.get('otherInformation'),
                'groupId': entity.get('groupId'),
                'subsidiaries': entity.get('subsidiaries', []),
                'relatedEntities': entity.get('relatedEntities', [])
            }

            # Load main entity with prepared parameters
            main_query = self.cypher_queries.get("load_entities")
            if main_query:
                self.neo4j_client.execute_query(main_query, entity_params)

            # Load aliases if present
            if entity.get("processed_aliases"):
                aliases_query = self.cypher_queries.get("load_entities_aliases")
                if aliases_query:
                    self.neo4j_client.execute_query(aliases_query, {
                        "sanctionId": entity["sanctionId"],
                        "aliases": entity["processed_aliases"]
                    })

            # Load address if present
            if entity.get("address"):
                address_query = self.cypher_queries.get("load_entities_address")
                if address_query:
                    self.neo4j_client.execute_query(address_query, {
                        "sanctionId": entity["sanctionId"],
                        "address": entity["address"]
                    })

            # Load entity relationships if present
            if entity.get("subsidiaries") or entity.get("relatedEntities"):
                relationships_query = self.cypher_queries.get("load_entities_relationships")
                if relationships_query:
                    self.neo4j_client.execute_query(relationships_query, {
                        "sanctionId": entity["sanctionId"],
                        "subsidiaries": entity.get("subsidiaries", []),
                        "relatedEntities": entity.get("relatedEntities", [])
                    })

            return True

        except Exception as e:
            pipeline_logger.error(f"Failed to load entity record {entity.get('sanctionId')}: {e}")
            return False

    def load_all_data(self, individuals_json_path: str = "output/individuals_extracted.json",
                     entities_json_path: str = "output/entities_extracted.json",
                     clear_existing: bool = False) -> Tuple[int, int]:
        """
        Load all sanctions data (individuals and entities) into Neo4j.

        Args:
            individuals_json_path: Path to individuals JSON file
            entities_json_path: Path to entities JSON file
            clear_existing: Whether to clear existing data first

        Returns:
            Tuple of (individuals_loaded, entities_loaded)
        """
        # Step 1: Setup database
        if not self.setup_database():
            raise RuntimeError("Failed to setup Neo4j database")

        # Step 2: Clear existing data if requested
        if clear_existing:
            self.clear_existing_data()

        # Step 3: Load individuals
        individuals_loaded = self.load_individuals(individuals_json_path)

        # Step 4: Load entities
        entities_loaded = self.load_entities(entities_json_path)

        return individuals_loaded, entities_loaded

    def get_database_stats(self) -> Dict[str, Any]:
        """
        Get database statistics after loading.

        Returns:
            Dictionary with database statistics
        """
        return self.neo4j_client.get_database_stats()

    def close(self):
        """Close Neo4j connection."""
        self.neo4j_client.disconnect()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


def process_sanctions_to_neo4j(individuals_json_path: str = "output/individuals_extracted.json",
                              entities_json_path: str = "output/entities_extracted.json",
                              clear_existing: bool = False) -> Tuple[int, int]:
    """
    Main function to load sanctions data into Neo4j.

    This is a simple, clean entry point that demonstrates the complete workflow.

    Args:
        individuals_json_path: Path to individuals JSON file
        entities_json_path: Path to entities JSON file
        clear_existing: Whether to clear existing data first

    Returns:
        Tuple of (individuals_loaded, entities_loaded)
    """
    # Step 1: Initialize the loader
    with Neo4jSanctionsLoader() as loader:
        # Step 2: Load all data with progress tracking
        individuals_loaded, entities_loaded = loader.load_all_data(
            individuals_json_path, entities_json_path, clear_existing
        )

        # Step 3: Get final database statistics
        db_stats = loader.get_database_stats()

        # Step 4: Report final summary
        pipeline_logger.info("")
        pipeline_logger.info("🎯 Final Neo4j Loading Summary:")
        pipeline_logger.info(f"   • Individuals loaded: {individuals_loaded}")
        pipeline_logger.info(f"   • Entities loaded: {entities_loaded}")
        pipeline_logger.info(f"   • Total Person nodes: {db_stats.get('node_counts', {}).get('Person', 0)}")
        pipeline_logger.info(f"   • Total Organisation nodes: {db_stats.get('node_counts', {}).get('Organisation', 0)}")
        pipeline_logger.info(f"   • Total relationships: {db_stats.get('total_relationships', 0)}")

        return individuals_loaded, entities_loaded


if __name__ == "__main__":
    # Run Neo4j loading when module is executed directly
    try:
        individuals_loaded, entities_loaded = process_sanctions_to_neo4j(clear_existing=True)
        if individuals_loaded > 0 or entities_loaded > 0:
            pipeline_logger.info("✅ Neo4j loading completed successfully!")
        else:
            pipeline_logger.warning("⚠️ No data was loaded into Neo4j")
    except Exception as e:
        pipeline_logger.error(f"Neo4j loading failed: {e}")
        exit(1)
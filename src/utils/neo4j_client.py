"""
Neo4j database client for UK sanctions data loading.
Handles connections, transactions, and database operations.
"""

import os
from typing import List, Dict, Any, Optional
from neo4j import GraphDatabase, Session, Transaction
from dotenv import load_dotenv

from src.logger_config import pipeline_logger

# Load environment variables
load_dotenv()


class Neo4jClient:
    """
    Neo4j database client for managing connections and transactions.

    Provides a clean interface for database operations including
    connection management, transaction handling, and query execution.
    """

    def __init__(self, uri: str = None, username: str = None, password: str = None, database: str = None):
        """
        Initialize Neo4j client with connection parameters.

        Args:
            uri: Neo4j connection URI (defaults to environment variable)
            username: Database username (defaults to environment variable)
            password: Database password (defaults to environment variable)
            database: Database name (defaults to environment variable)
        """
        # Use environment variables as defaults
        self.uri = uri or os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.username = username or os.getenv("NEO4J_USERNAME", "neo4j")
        self.password = password or os.getenv("NEO4J_PASSWORD")
        self.database = database or os.getenv("NEO4J_DATABASE", "neo4j")

        if not self.password:
            raise ValueError("Neo4j password must be provided via NEO4J_PASSWORD environment variable or parameter")

        # Initialize driver
        self.driver = None
        self.is_connected = False

    def connect(self) -> bool:
        """
        Establish connection to Neo4j database.

        Returns:
            True if connection successful, False otherwise
        """
        try:
            self.driver = GraphDatabase.driver(
                self.uri,
                auth=(self.username, self.password)
            )

            # Test the connection
            with self.driver.session(database=self.database) as session:
                result = session.run("RETURN 1 as test")
                test_value = result.single()["test"]

            if test_value == 1:
                self.is_connected = True
                pipeline_logger.info(f"✅ Connected to Neo4j database: {self.database}")
                return True
            else:
                pipeline_logger.error("Neo4j connection test failed")
                return False

        except Exception as e:
            pipeline_logger.error(f"Failed to connect to Neo4j: {e}")
            self.is_connected = False
            return False

    def disconnect(self):
        """Close Neo4j driver connection."""
        if self.driver:
            self.driver.close()
            self.is_connected = False
            pipeline_logger.info("📦 Neo4j connection closed")

    def execute_query(self, query: str, parameters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Execute a Cypher query and return results.

        Args:
            query: Cypher query string
            parameters: Query parameters dictionary

        Returns:
            List of result records as dictionaries
        """
        if not self.is_connected:
            raise RuntimeError("Not connected to Neo4j database")

        try:
            with self.driver.session(database=self.database) as session:
                result = session.run(query, parameters or {})
                return [record.data() for record in result]

        except Exception as e:
            pipeline_logger.error(f"Query execution failed: {e}")
            raise

    def execute_write_transaction(self, queries: List[Dict[str, Any]]) -> int:
        """
        Execute multiple queries in a single write transaction.

        Args:
            queries: List of query dictionaries with 'query' and 'parameters' keys

        Returns:
            Number of queries executed successfully
        """
        if not self.is_connected:
            raise RuntimeError("Not connected to Neo4j database")

        def _execute_queries(tx: Transaction) -> int:
            executed_count = 0
            for query_dict in queries:
                query = query_dict.get("query")
                parameters = query_dict.get("parameters", {})

                if query:
                    tx.run(query, parameters)
                    executed_count += 1

            return executed_count

        try:
            with self.driver.session(database=self.database) as session:
                return session.execute_write(_execute_queries)

        except Exception as e:
            pipeline_logger.error(f"Transaction execution failed: {e}")
            raise

    def create_constraints_and_indices(self) -> bool:
        """
        Create necessary constraints and indices for sanctions data.

        Returns:
            True if successful, False otherwise
        """
        constraints_and_indices = [
            # Unique constraints
            "CREATE CONSTRAINT unique_person_sanction_id IF NOT EXISTS FOR (p:Person) REQUIRE p.sanctionId IS UNIQUE",
            "CREATE CONSTRAINT unique_org_sanction_id IF NOT EXISTS FOR (o:Organisation) REQUIRE o.sanctionId IS UNIQUE",
            "CREATE CONSTRAINT unique_country_code IF NOT EXISTS FOR (c:Country) REQUIRE c.code IS UNIQUE",
            "CREATE CONSTRAINT unique_alias_key IF NOT EXISTS FOR (a:Alias) REQUIRE a.aliasId IS UNIQUE",
            "CREATE CONSTRAINT unique_address_id IF NOT EXISTS FOR (addr:Address) REQUIRE addr.addressId IS UNIQUE",

            # Performance indices
            "CREATE INDEX person_fullname IF NOT EXISTS FOR (p:Person) ON (p.fullName)",
            "CREATE INDEX person_lastname IF NOT EXISTS FOR (p:Person) ON (p.lastName)",
            "CREATE INDEX org_name IF NOT EXISTS FOR (o:Organisation) ON (o.organisationName)",
            "CREATE INDEX person_listed_date IF NOT EXISTS FOR (p:Person) ON (p.listedOn)",
            "CREATE INDEX country_name IF NOT EXISTS FOR (c:Country) ON (c.name)",
            "CREATE INDEX alias_key IF NOT EXISTS FOR (a:Alias) ON (a.aliasId)",
            "CREATE INDEX address_id IF NOT EXISTS FOR (addr:Address) ON (addr.addressId)",
            "CREATE INDEX address_postcode IF NOT EXISTS FOR (addr:Address) ON (addr.postCode)",

            # Full-text search indices
            "CREATE FULLTEXT INDEX person_name_search IF NOT EXISTS FOR (p:Person) ON EACH [p.fullName, p.firstName, p.lastName]",
            "CREATE FULLTEXT INDEX alias_search IF NOT EXISTS FOR (a:Alias) ON EACH [a.aliasName, a.aliasId]"
        ]

        try:
            successful = 0
            for constraint_query in constraints_and_indices:
                try:
                    self.execute_query(constraint_query)
                    successful += 1
                except Exception as e:
                    # Log but continue - constraint might already exist
                    pipeline_logger.debug(f"Constraint/index creation note: {e}")

            pipeline_logger.info(f"✅ Database schema setup: {successful}/{len(constraints_and_indices)} constraints/indices processed")
            return True

        except Exception as e:
            pipeline_logger.error(f"Failed to create constraints and indices: {e}")
            return False

    def get_database_stats(self) -> Dict[str, Any]:
        """
        Get database statistics for monitoring.

        Returns:
            Dictionary with database statistics
        """
        try:
            # Count nodes by label
            node_counts = {}

            labels_query = "CALL db.labels()"
            labels_result = self.execute_query(labels_query)

            for label_record in labels_result:
                label = label_record.get("label")
                if label:
                    count_query = f"MATCH (n:{label}) RETURN count(n) as count"
                    count_result = self.execute_query(count_query)
                    node_counts[label] = count_result[0]["count"] if count_result else 0

            # Count relationships
            rel_query = "MATCH ()-[r]->() RETURN count(r) as total_relationships"
            rel_result = self.execute_query(rel_query)
            total_relationships = rel_result[0]["total_relationships"] if rel_result else 0

            return {
                "node_counts": node_counts,
                "total_relationships": total_relationships,
                "database": self.database
            }

        except Exception as e:
            pipeline_logger.error(f"Failed to get database stats: {e}")
            return {"error": str(e)}

    def clear_sanctions_data(self) -> bool:
        """
        Clear all sanctions-related data from the database.

        WARNING: This will delete all Person, Organisation, Address, Alias nodes and their relationships.

        Returns:
            True if successful, False otherwise
        """
        try:
            clear_queries = [
                "MATCH (p:Person) DETACH DELETE p",
                "MATCH (o:Organisation) DETACH DELETE o",
                "MATCH (a:Address) DETACH DELETE a",
                "MATCH (al:Alias) DETACH DELETE al",
                "MATCH (c:Country) WHERE NOT EXISTS { MATCH (c)<-[]-() } DELETE c"  # Only delete orphaned countries
            ]

            for query in clear_queries:
                self.execute_query(query)

            pipeline_logger.info("🗑️ Sanctions data cleared from database")
            return True

        except Exception as e:
            pipeline_logger.error(f"Failed to clear sanctions data: {e}")
            return False

    def __enter__(self):
        """Context manager entry."""
        if not self.connect():
            raise RuntimeError("Failed to connect to Neo4j database")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()
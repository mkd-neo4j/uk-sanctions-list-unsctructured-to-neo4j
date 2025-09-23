"""
Main entry point for UK Sanctions List processing pipeline.
This orchestrates the multi-step process to convert unstructured PDF data
into structured Neo4j graph database format.
"""

import os
from dotenv import load_dotenv

from src.pdf_to_text import process_sanctions_pdf
from src.llm_extractor import process_sanctions_with_llm
from src.neo4j_loader import process_sanctions_to_neo4j
from src.logger_config import pipeline_logger


def main():
    """
    Execute the complete sanctions data processing pipeline.

    Steps:
    1. PDF to Text conversion
    2. LLM parsing with structured output
    3. Neo4j graph database loading
    4. Complete end-to-end data transformation
    """
    try:
        # Load environment variables
        load_dotenv()

        # Initialize pipeline with professional logging
        pipeline_logger.pipeline_start("UK Sanctions List Processing Pipeline")
        pipeline_logger.info("🔄 Initializing AI-powered sanctions data extraction system")
        pipeline_logger.info("🎯 Target: Convert unstructured PDF data to structured Neo4j graph database")

        # Step 1: PDF to Text Conversion
        pipeline_logger.step_start("PDF to Text Conversion", "Extracting raw text from sanctions PDF document")

        text_content = process_sanctions_pdf()

        if not text_content:
            pipeline_logger.step_error("PDF to Text Conversion", "Could not extract text from PDF file")
            return 1

        pipeline_logger.step_complete("PDF to Text Conversion", {
            "Text extracted": f"{len(text_content):,} characters",
            "Output file": "output/Cyber_text.txt",
            "Status": "Ready for LLM processing"
        })

        # Step 2: LLM Parsing and Structured Extraction
        model_name = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        pipeline_logger.step_start("LLM Structured Extraction", f"Processing text with OpenAI {model_name} for structured data extraction")

        try:
            individuals, entities = process_sanctions_with_llm()

            pipeline_logger.step_complete("LLM Structured Extraction", {
                "Individuals extracted": f"{individuals.totalCount}",
                "Entities extracted": f"{entities.totalCount}",
                "Output file": "output/extracted_data.json",
                "Data quality": "Structured and validated"
            })

            # Show sample extracted data for demo
            if individuals.individuals and len(individuals.individuals) > 0:
                sample_individual = individuals.individuals[0]
                pipeline_logger.data_sample("Sample Individual Record", {
                    "Name": f"{sample_individual.firstName} {sample_individual.lastName}",
                    "Sanction ID": sample_individual.sanctionId,
                    "Nationality": sample_individual.nationality,
                    "Date of Birth": sample_individual.dateOfBirth or "Not provided",
                    "Group ID": sample_individual.groupId
                })

            if entities.entities and len(entities.entities) > 0:
                sample_entity = entities.entities[0]
                pipeline_logger.data_sample("Sample Entity Record", {
                    "Organization": sample_entity.organizationName,
                    "Sanction ID": sample_entity.sanctionId,
                    "Entity Type": sample_entity.entityType,
                    "Group ID": sample_entity.groupId,
                    "Aliases": f"{len(sample_entity.aliases)} aliases found" if sample_entity.aliases else "No aliases"
                })

            # Step 3: Neo4j Database Loading
            pipeline_logger.step_start("Neo4j Database Loading", "Loading structured data into Neo4j graph database")

            try:
                individuals_loaded, entities_loaded = process_sanctions_to_neo4j(
                    clear_existing=True  # Clear existing data for fresh load
                )

                pipeline_logger.step_complete("Neo4j Database Loading", {
                    "Individuals loaded": f"{individuals_loaded}",
                    "Entities loaded": f"{entities_loaded}",
                    "Database": "Neo4j graph structure created",
                    "Relationships": "Full graph relationships established"
                })

                # Pipeline completion with context-aware stats
                pipeline_logger.info("")
                pipeline_logger.info("🎯 Pipeline Summary:")

                # Always show what Neo4j loaded (this step always runs in this block)
                pipeline_logger.info(f"   • Individuals loaded to Neo4j: {individuals_loaded}")
                pipeline_logger.info(f"   • Entities loaded to Neo4j: {entities_loaded}")

                # Conditionally show Step 1 stats if available
                if 'text_content' in locals() and text_content:
                    pipeline_logger.info(f"   • Text extracted: {len(text_content):,} characters")
                else:
                    pipeline_logger.info("   • Text extraction: Skipped (using existing data)")

                # Conditionally show Step 2 stats if available
                if 'individuals' in locals() and individuals:
                    pipeline_logger.info(f"   • Individuals processed by LLM: {individuals.totalCount}")
                else:
                    pipeline_logger.info("   • LLM individual processing: Skipped (using existing JSON)")

                if 'entities' in locals() and entities:
                    pipeline_logger.info(f"   • Entities processed by LLM: {entities.totalCount}")
                else:
                    pipeline_logger.info("   • LLM entity processing: Skipped (using existing JSON)")

                # Show appropriate completion message
                if 'text_content' in locals() and 'individuals' in locals():
                    pipeline_logger.info("   • Status: Complete end-to-end pipeline success! 🚀")
                else:
                    pipeline_logger.info("   • Status: Neo4j loading completed successfully! ✅")

                pipeline_logger.pipeline_complete()

            except Exception as e:
                pipeline_logger.step_error("Neo4j Database Loading", str(e))
                pipeline_logger.error("💡 Neo4j Troubleshooting:")
                pipeline_logger.error("   • Verify Neo4j database is running")
                pipeline_logger.error("   • Check NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD in .env file")
                pipeline_logger.error("   • Ensure Neo4j database is accessible")
                pipeline_logger.error("   • Verify network connectivity to Neo4j instance")
                return 1

        except Exception as e:
            pipeline_logger.step_error("LLM Structured Extraction", str(e))
            pipeline_logger.error("💡 Troubleshooting:")
            pipeline_logger.error("   • Verify OPENAI_API_KEY is set in .env file")
            pipeline_logger.error("   • Check internet connectivity")
            pipeline_logger.error("   • Ensure OpenAI API credits are available")
            return 1

    except Exception as e:
        pipeline_logger.error(f"Pipeline initialization failed: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
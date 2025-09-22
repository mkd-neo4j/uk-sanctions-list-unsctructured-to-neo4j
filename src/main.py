"""
Main entry point for UK Sanctions List processing pipeline.
This orchestrates the multi-step process to convert unstructured PDF data
into structured Neo4j graph database format.
"""

from src.pdf_to_text import process_sanctions_pdf
from src.llm_extractor import process_sanctions_with_llm
from src.logger_config import pipeline_logger


def main():
    """
    Execute the sanctions data processing pipeline.

    Steps:
    1. PDF to Text conversion
    2. LLM parsing with structured output
    3. Data modeling with Pydantic (implemented)
    4. Neo4j loading (to be implemented)
    """
    try:
        # Initialize pipeline with professional logging
        pipeline_logger.pipeline_start("UK Sanctions List Processing Pipeline")
        pipeline_logger.info("🔄 Initializing AI-powered sanctions data extraction system")
        pipeline_logger.info("🎯 Target: Convert unstructured PDF data to structured Neo4j format")

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
        pipeline_logger.step_start("LLM Structured Extraction", "Processing text with OpenAI GPT-4o-mini for structured data extraction")

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

            # Pipeline completion
            pipeline_logger.info("")
            pipeline_logger.info("🚀 Next Implementation Steps:")
            pipeline_logger.info("   • Neo4j database schema design")
            pipeline_logger.info("   • Graph relationship modeling")
            pipeline_logger.info("   • Data loading and indexing")

            pipeline_logger.pipeline_complete()

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
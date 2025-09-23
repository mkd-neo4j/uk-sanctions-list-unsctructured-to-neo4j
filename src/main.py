"""
Main entry point for UK Sanctions List processing pipeline.
This orchestrates the multi-step process to convert unstructured PDF data
into structured Neo4j graph database format.
"""

import os
import sys
import argparse
from dotenv import load_dotenv

# Add project root to Python path for imports
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

try:
    # Try imports as if run from project root
    from src.pdf_to_text import process_sanctions_pdf
    from src.llm_extractor import process_sanctions_with_llm
    from src.neo4j_loader import process_sanctions_to_neo4j
    from src.logger_config import pipeline_logger
except ImportError:
    # Try imports as if run from src/ directory
    from pdf_to_text import process_sanctions_pdf
    from llm_extractor import process_sanctions_with_llm
    from neo4j_loader import process_sanctions_to_neo4j
    from logger_config import pipeline_logger


def parse_arguments():
    """Parse command-line arguments for stage selection."""
    parser = argparse.ArgumentParser(
        description="UK Sanctions List processing pipeline - convert unstructured PDF data to structured Neo4j format",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Stage Options:
  pdf     - Extract text from PDF documents
  llm     - AI-powered entity extraction from text
  neo4j   - Load structured data into Neo4j database
  all     - Run all stages (default)

Examples:
  python src/main.py --stages all          # Run complete pipeline
  python src/main.py --stages neo4j        # Load existing JSON data to Neo4j only
  python src/main.py --stages llm,neo4j    # Extract entities and load to Neo4j
  python src/main.py --stages pdf          # Extract text from PDF only
  python src/main.py --stages pdf,llm      # Extract text and entities only
        """
    )

    parser.add_argument(
        "--stages", "-s",
        default="all",
        help="Comma-separated list of stages to run: pdf, llm, neo4j, or 'all' (default: all)"
    )

    return parser.parse_args()


def validate_stages(stages_input):
    """Validate and parse stage selection."""
    valid_stages = {"pdf", "llm", "neo4j", "all"}

    if stages_input == "all":
        return ["pdf", "llm", "neo4j"]

    requested_stages = [stage.strip().lower() for stage in stages_input.split(",")]

    # Validate all requested stages
    invalid_stages = set(requested_stages) - valid_stages
    if invalid_stages:
        raise ValueError(f"Invalid stages: {', '.join(invalid_stages)}. Valid options: {', '.join(sorted(valid_stages))}")

    return requested_stages


def check_stage_dependencies(stages):
    """Check if required files exist for selected stages."""
    issues = []

    if "llm" in stages and not os.path.exists("output/Cyber_text.txt"):
        issues.append("LLM stage requires 'output/Cyber_text.txt' (run 'pdf' stage first)")

    if "neo4j" in stages:
        json_files = ["output/extracted_data.json", "output/individuals_extracted.json", "output/entities_extracted.json"]
        missing_files = [f for f in json_files if not os.path.exists(f)]
        if len(missing_files) == len(json_files):  # All missing
            issues.append("Neo4j stage requires extracted JSON data (run 'llm' stage first)")

    return issues


def run_pdf_extraction():
    """Execute PDF to text conversion stage."""
    pipeline_logger.step_start("PDF to Text Conversion", "Extracting raw text from sanctions PDF document")

    text_content = process_sanctions_pdf()

    if not text_content:
        pipeline_logger.step_error("PDF to Text Conversion", "Could not extract text from PDF file")
        return None

    pipeline_logger.step_complete("PDF to Text Conversion", {
        "Text extracted": f"{len(text_content):,} characters",
        "Output file": "output/Cyber_text.txt",
        "Status": "Ready for LLM processing"
    })

    return text_content


def run_llm_extraction():
    """Execute LLM parsing and structured extraction stage."""
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

        return individuals, entities

    except Exception as e:
        pipeline_logger.step_error("LLM Structured Extraction", str(e))
        pipeline_logger.error("💡 Troubleshooting:")
        pipeline_logger.error("   • Verify OPENAI_API_KEY is set in .env file")
        pipeline_logger.error("   • Check internet connectivity")
        pipeline_logger.error("   • Ensure OpenAI API credits are available")
        raise


def run_neo4j_loading():
    """Execute Neo4j database loading stage."""
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

        return individuals_loaded, entities_loaded

    except Exception as e:
        pipeline_logger.step_error("Neo4j Database Loading", str(e))
        pipeline_logger.error("💡 Neo4j Troubleshooting:")
        pipeline_logger.error("   • Verify Neo4j database is running")
        pipeline_logger.error("   • Check NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD in .env file")
        pipeline_logger.error("   • Ensure Neo4j database is accessible")
        pipeline_logger.error("   • Verify network connectivity to Neo4j instance")
        raise


def main():
    """
    Execute the sanctions data processing pipeline with configurable stages.

    Supports selective execution of:
    - PDF to Text conversion
    - LLM parsing with structured output
    - Neo4j graph database loading
    """
    try:
        # Parse command-line arguments
        args = parse_arguments()

        # Load environment variables
        load_dotenv()

        # Validate and parse stages
        try:
            stages = validate_stages(args.stages)
        except ValueError as e:
            print(f"Error: {e}")
            return 1

        # Check stage dependencies
        dependency_issues = check_stage_dependencies(stages)
        if dependency_issues:
            print("Dependency issues found:")
            for issue in dependency_issues:
                print(f"  • {issue}")
            print("\nPlease resolve these issues or run required stages first.")
            return 1

        # Initialize pipeline with professional logging
        stage_names = ", ".join(stages)
        pipeline_logger.pipeline_start(f"UK Sanctions List Processing Pipeline - Stages: {stage_names}")
        pipeline_logger.info("🔄 Initializing AI-powered sanctions data extraction system")
        pipeline_logger.info(f"🎯 Selected stages: {stage_names}")

        # Track results for summary
        results = {}

        # Execute selected stages
        if "pdf" in stages:
            text_content = run_pdf_extraction()
            if text_content is None:
                return 1
            results["text_content"] = text_content

        if "llm" in stages:
            individuals, entities = run_llm_extraction()
            results["individuals"] = individuals
            results["entities"] = entities

        if "neo4j" in stages:
            individuals_loaded, entities_loaded = run_neo4j_loading()
            results["individuals_loaded"] = individuals_loaded
            results["entities_loaded"] = entities_loaded

        # Generate pipeline summary
        pipeline_logger.info("")
        pipeline_logger.info("🎯 Pipeline Summary:")

        if "neo4j" in stages:
            pipeline_logger.info(f"   • Individuals loaded to Neo4j: {results['individuals_loaded']}")
            pipeline_logger.info(f"   • Entities loaded to Neo4j: {results['entities_loaded']}")

        if "pdf" in stages and "text_content" in results:
            pipeline_logger.info(f"   • Text extracted: {len(results['text_content']):,} characters")
        elif "llm" in stages or "neo4j" in stages:
            pipeline_logger.info("   • Text extraction: Skipped (using existing data)")

        if "llm" in stages and "individuals" in results:
            pipeline_logger.info(f"   • Individuals processed by LLM: {results['individuals'].totalCount}")
        elif "neo4j" in stages and "llm" not in stages:
            pipeline_logger.info("   • LLM individual processing: Skipped (using existing JSON)")

        if "llm" in stages and "entities" in results:
            pipeline_logger.info(f"   • Entities processed by LLM: {results['entities'].totalCount}")
        elif "neo4j" in stages and "llm" not in stages:
            pipeline_logger.info("   • LLM entity processing: Skipped (using existing JSON)")

        # Show appropriate completion message
        if len(stages) == 3:  # All stages
            pipeline_logger.info("   • Status: Complete end-to-end pipeline success! 🚀")
        elif len(stages) == 1:
            stage_name = stages[0].upper()
            pipeline_logger.info(f"   • Status: {stage_name} stage completed successfully! ✅")
        else:
            pipeline_logger.info(f"   • Status: Selected stages completed successfully! ✅")

        pipeline_logger.pipeline_complete()

    except Exception as e:
        pipeline_logger.error(f"Pipeline execution failed: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
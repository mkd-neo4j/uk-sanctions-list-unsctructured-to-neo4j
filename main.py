"""
Main entry point for UK Sanctions List processing pipeline.
This orchestrates the multi-step process to convert unstructured PDF data
into structured Neo4j graph database format.
"""

from pdf_to_text import process_sanctions_pdf
from llm_extractor import process_sanctions_with_llm


def main():
    """
    Execute the sanctions data processing pipeline.

    Steps:
    1. PDF to Text conversion
    2. LLM parsing with structured output
    3. Data modeling with Pydantic (implemented)
    4. Neo4j loading (to be implemented)
    """
    print("=== UK Sanctions List Processing Pipeline ===")
    print("Starting Step 1: PDF to Text Conversion\n")

    text_content = process_sanctions_pdf()

    if text_content:
        print("\n✅ Step 1 completed successfully")
        print("\nStarting Step 2: LLM parsing with structured output\n")

        try:
            individuals, entities = process_sanctions_with_llm()
            print(f"\n✅ Step 2 completed successfully")
            print(f"   - Extracted {individuals.totalCount} sanctioned individuals")
            print(f"   - Extracted {entities.totalCount} sanctioned entities")
            print("   - Results saved to output/extracted_data.json")

            print("\nNext steps to implement:")
            print("- Step 4: Neo4j database loading")

        except Exception as e:
            print(f"\n❌ Step 2 failed: {e}")
            print("Make sure you have set your OPENAI_API_KEY environment variable")
            return 1

    else:
        print("\n❌ Step 1 failed: Could not extract text from PDF")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
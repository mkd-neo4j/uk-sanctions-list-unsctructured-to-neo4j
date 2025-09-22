# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a UK Sanctions List processing pipeline that transforms unstructured PDF documents into structured data using AI extraction and stores the results in JSON format. The project is built with Python and uses OpenAI's GPT-4o-mini for intelligent entity extraction from sanctions documents.

**Core Purpose**: Convert unstructured UK sanctions PDFs → AI-powered entity extraction → JSON output → Future Neo4j knowledge graph

## Common Development Commands

### Setup and Environment
```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment configuration
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY
```

### Running the Pipeline
```bash
# Run the complete processing pipeline
python src/main.py

# Run individual components
python src/pdf_to_text.py          # PDF extraction only
python src/llm_extractor.py        # LLM extraction only
```

### Testing and Validation
```bash
# Check output files
ls -la output/
cat output/individuals_extracted.json | jq '.[0]'    # View first individual
cat output/entities_extracted.json | jq '.[0]'       # View first entity
```

## Architecture Overview

### Processing Pipeline Flow
The application follows a sequential processing pipeline:

1. **PDF Processing** (`pdf_to_text.py`) → Extract text from PDF documents in `pdf/` directory
2. **AI Extraction** (`llm_extractor.py`) → Use OpenAI API to extract structured entities from text
3. **Data Modeling** (`models/`) → Validate extracted data using Pydantic models
4. **Orchestration** (`main.py`) → Coordinate the entire pipeline with logging

### Key Architecture Patterns

**Modular Processing Chain**: Each step is independent and can be run separately for development/debugging.

**Incremental Output**: Individual and entity records are saved to JSON files immediately after extraction to prevent data loss on failures.

**Professional Logging**: Custom logging system (`logger_config.py`) provides structured progress tracking, metrics, and error reporting.

**Structured Data Models**: Pydantic models in `models/` define the schema for individuals, entities, and addresses with Neo4j-compatible field names.

### Data Flow Architecture

```
pdf/Cyber.pdf → [PDF Text Extraction] → output/Cyber_text.txt
              ↓
[LLM Record Splitting] → Individual records + Entity records
              ↓
[OpenAI Structured Output] → Pydantic validation
              ↓
output/individuals_extracted.json + output/entities_extracted.json
```

### File Organization Patterns

- `src/`: All Python modules with clear separation of concerns
- `pdf/`: Input PDF documents (currently contains Cyber.pdf)
- `output/`: Generated files from processing pipeline
- `models/`: Pydantic data models for structured data validation
- Configuration via `.env` file for API keys and model settings

## Key Technical Details

### LLM Processing Strategy
- **Record Splitting**: Text is intelligently split into individual records before LLM processing
- **Structured Output**: Uses OpenAI's structured output feature with Pydantic models for reliable data extraction
- **Incremental Processing**: Processes one record at a time for better accuracy and error recovery
- **Cost Tracking**: Monitors token usage and provides cost estimates

### Data Models (Pydantic)
- `SanctionedIndividual`: Core model for person entities with name parsing, addresses, aliases
- `SanctionedEntity`: Model for organizations/companies with structured metadata
- `Address`: Nested model for location data with both raw and parsed components
- All models use camelCase properties for Neo4j compatibility

### Error Handling & Resilience
- Individual record processing failures don't stop the entire pipeline
- Incremental saving prevents data loss on crashes
- Comprehensive logging for debugging and monitoring
- API usage tracking and cost estimation

### Environment Configuration
Key environment variables in `.env`:
- `OPENAI_API_KEY`: Required for LLM processing
- `OPENAI_MODEL`: Defaults to gpt-4o-mini
- `OPENAI_INPUT_COST_PER_MILLION`/`OPENAI_OUTPUT_COST_PER_MILLION`: For cost estimation

## Development Notes

### Working with the LLM Extractor
- The `LLMExtractor` class handles all OpenAI API interactions
- Records are processed individually for maximum accuracy
- Progress is tracked and displayed during processing
- Results are saved incrementally to prevent data loss

### Output File Structure
- `individuals_extracted.json`: Array of individual person records
- `entities_extracted.json`: Array of organization/entity records
- `extracted_data.json`: Combined summary file for compatibility

### Code Style Conventions
- Pydantic models use camelCase field names (Neo4j compatibility)
- Comprehensive docstrings for all classes and functions
- Type hints throughout the codebase
- Professional logging instead of print statements
# WHY - UK Sanctions List: Unstructured to Neo4j

## The Use Case

Organisations and banks building fraud detection platforms commonly face the challenge of processing unstructured data. This repository demonstrates how to transform unstructured PDF data into a structured graph database format suitable for fraud pattern analysis.

## What We're Building

This demo takes the UK List of Financial Sanctions Targets (Asset Freeze Targets under the Cyber regime) and transforms it from an unstructured PDF format into a structured Neo4j graph database.

### The Data
- **Source**: UK Cyber Sanctions PDF (`cyber.pdf`)
- **Content**:
  - 70 sanctioned individuals
  - 9 sanctioned entities
  - Total: 13 pages of sanctions data

### The Challenge
While PDFs may appear semi-structured visually, they lack true data structure. The sanctions list contains various fields like:
- Group IDs
- Last Updated dates
- Names
- Addresses
- AKAs (Also Known As)
- Other important metadata

## Why This Matters

### Advantages
1. **Automated Processing**: Manual extraction of sanctions data is error-prone and time-consuming
2. **Graph Relationships**: Neo4j reveals hidden connections between sanctioned entities
3. **Scalability**: Process can handle growing sanctions lists automatically
4. **Integration**: Structured data integrates seamlessly with existing fraud detection systems
5. **Compliance**: Ensures up-to-date sanctions screening

## The Technical Approach

### Pipeline Overview
1. **PDF to Text Conversion**: Extract raw text from the sanctions PDF
2. **LLM Parsing**: Use language models to identify and extract individuals and entities
3. **Data Modelling**:
   - Create Pydantic models for individuals
   - Create Pydantic models for entities
4. **Data Extraction**: Parse each record with structured fields:
   - Core identifiers (names, IDs)
   - Metadata (list dates, last updated, group IDs)
   - Additional information stored as strings for unmapped fields
5. **Neo4j Loading**: Insert data following the [Neo4j Transactional Data Model](https://neo4j.com/developer/industry-use-cases/data-models/transactions/transactions-base-model/)
   - Model persons
   - Model passport numbers
   - Model other identifying information
   - Preserve all metadata for compliance

## Expected Outcome

A fully searchable, relationship-aware graph database containing UK sanctions data that can be:
- Queried for compliance checks
- Analysed for relationship patterns
- Integrated with existing fraud detection systems
- Updated as new sanctions are published
"""
UK Sanctions List Processing Pipeline

This package contains modules for processing UK sanctions data from PDF format
into structured data suitable for Neo4j graph database loading.

Main modules:
- pdf_to_text: PDF text extraction
- llm_extractor: AI-powered structured data extraction
- models: Pydantic data models for individuals, entities, and addresses
- logger_config: Pipeline logging configuration
"""
# UK Sanctions List: Unstructured to Neo4j

Transform unstructured UK sanctions PDF data into a structured Neo4j graph database for
fraud detection and compliance.

## 🎯 Overview

This project demonstrates how to process the UK List of Financial Sanctions Targets
(Cyber regime) from an unstructured PDF format into a structured graph database
suitable for:
- Compliance checks
- Relationship analysis
- Fraud pattern detection
- Integration with existing fraud detection systems

## 🚀 Quick Start

### Prerequisites
- Python 3.x
- Virtual environment (recommended)

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd uk-sanctions-list-unsctructured-to-neo4j

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Run the Pipeline

```bash
python main.py
```

## 📁 Project Structure

```
.
├── main.py              # Main entry point - orchestrates the pipeline
├── pdf_to_text.py       # Step 1: PDF to text conversion module
├── requirements.txt     # Python dependencies
├── pdf/
│   └── Cyber.pdf       # UK sanctions list (Cyber regime)
├── output/
│   └── Cyber_text.txt  # Extracted text from PDF
└── WHY.md              # Detailed project rationale
```

## 🔄 Pipeline Steps

### Step 1: PDF to Text Conversion ✅
- **Status**: Implemented
- **Module**: `pdf_to_text.py`
- **Function**: Extracts raw text from the sanctions PDF
- **Output**: `output/Cyber_text.txt`

### Step 2: LLM Parsing 🔄
- **Status**: Coming soon
- **Purpose**: Use language models to identify and extract individuals and entities
- **Expected output**: Structured JSON with parsed entities

### Step 3: Data Modeling 🔄
- **Status**: Coming soon
- **Purpose**: Create Pydantic models for validation
- **Models**:
- Individual sanctions records
- Entity sanctions records

### Step 4: Neo4j Loading 🔄
- **Status**: Coming soon
- **Purpose**: Load structured data into Neo4j
- **Schema**: Based on [Neo4j Transactional Data Model](https://neo4j.com/developer/industry-use-cases/data-models/transactions/transactions-base-model/)

## 📊 Current Implementation

### PDF Processing Results
- **Source**: `pdf/Cyber.pdf`
- **Pages**: 13
- **Content**:
- 70 sanctioned individuals
- 9 sanctioned entities
- **Extracted characters**: 86,443

### Sample Data Structure
The PDF contains structured fields including:
- Names and aliases (AKAs)
- Group IDs
- Last Updated dates
- Passport numbers
- Addresses
- Statement of Reasons
- Other metadata

## 🛠 Technologies

- **PDF Processing**: pdfplumber 0.11.4
- **Future additions**:
- LLM integration (OpenAI/Anthropic)
- Pydantic for data validation
- Neo4j Python driver

## 📋 Requirements

See `requirements.txt` for full list. Core dependencies:
```
pdfplumber==0.11.4
```

## 📈 Next Steps

1. Implement LLM-based entity extraction
2. Design Pydantic models for data validation
3. Create Neo4j schema and loading logic
4. Add error handling and logging
5. Implement incremental updates for new sanctions
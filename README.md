# 🏦 UK Sanctions List: AI-Powered Data Extraction Pipeline

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://www.python.org/)
[![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4o--mini-green)](https://openai.com/)
[![Neo4j](https://img.shields.io/badge/Neo4j-Ready-orange)](https://neo4j.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

## 🎯 Overview

Transform unstructured UK sanctions PDF documents into structured, queryable data using AI. This enterprise-grade pipeline leverages OpenAI's GPT-4o-mini to extract, validate, and structure sanctions data for compliance systems.

**Perfect for banks and financial institutions** requiring automated sanctions screening and compliance monitoring.

## ✨ Key Features

- **🤖 AI-Powered Extraction**: Uses OpenAI GPT-4o-mini for intelligent data parsing
- **📊 Real-Time Processing**: Live progress tracking with professional logging
- **💾 Incremental Saving**: Crash-resilient with automatic save after each record
- **💰 Cost Tracking**: Real-time OpenAI API usage and cost monitoring
- **🔍 Data Validation**: Structured output with Pydantic models
- **📈 Performance Metrics**: Processing times, success rates, and quality metrics
- **🏢 Enterprise Ready**: Professional logging for bank demonstrations

## 📁 Project Structure

```
uk-sanctions-list-neo4j/
│
├── src/                          # Source code
│   ├── main.py                   # Main pipeline orchestrator
│   ├── pdf_to_text.py            # PDF extraction module
│   ├── llm_extractor.py          # AI-powered extraction
│   ├── logger_config.py          # Professional logging
│   └── models/                   # Data models
│       ├── __init__.py
│       ├── address.py            # Address structure
│       ├── individual.py         # Individual sanctions
│       └── entity.py             # Entity sanctions
│
├── pdf/                          # Input PDF files
│   └── Cyber.pdf                 # UK Sanctions List
│
├── output/                       # Extraction results
│   ├── Cyber_text.txt           # Extracted raw text
│   ├── individuals_extracted.json   # Individual records
│   ├── entities_extracted.json      # Entity records
│   └── extracted_data.json         # Combined summary
│
├── .env.example                  # Configuration template
├── requirements.txt              # Python dependencies
├── WHY.md                       # Project motivation
└── README.md                    # This file
```

## 🚀 Quick Start

### 1. Prerequisites

- Python 3.8+
- OpenAI API key ([Get one here](https://platform.openai.com/api-keys))
- 2GB free disk space

### 2. Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/uk-sanctions-list-neo4j.git
cd uk-sanctions-list-neo4j

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit .env and add your OpenAI API key
# OPENAI_API_KEY=sk-proj-...
```

**Configuration Options** (in `.env`):
```env
OPENAI_API_KEY=your_api_key_here
OPENAI_MODEL=gpt-4o-mini              # Model to use
OPENAI_INPUT_COST_PER_MILLION=0.150   # $ per 1M input tokens
OPENAI_OUTPUT_COST_PER_MILLION=0.600  # $ per 1M output tokens
```

### 4. Run the Pipeline

```bash
python src/main.py
```

## 📊 Sample Output

### Real-Time Processing View:
```
[10:15:23] ============================================================
[10:15:23] 🏦 UK Sanctions List Processing Pipeline
[10:15:23] ============================================================
[10:15:23] 🔄 Initializing AI-powered sanctions data extraction system

[10:15:24] 📋 STEP: PDF to Text Conversion
[10:15:25] ⚡ [████████████████████] 100.0% 45/45 pages - Extracting page 45
[10:15:26] ✅ PDF to Text Conversion completed in 2.1s
[10:15:26]    • Text extracted: 125,432 characters
[10:15:26]    • Output file: output/Cyber_text.txt

[10:15:27] 📋 STEP: LLM Structured Extraction
[10:15:27] 🤖 Starting LLM extraction for 70 individuals
[10:15:28] 📁 Initialized output files:
[10:15:28]    • output/individuals_extracted.json
[10:15:28]    • output/entities_extracted.json

[10:15:30] ⚡ [██░░░░░░░░░░░░░░░░░░] 10.0% 7/70 individuals - Processing and saving record 7

[10:15:31] 🔍 EXAMPLE: Raw Input vs Structured Output
[10:15:31] ============================================================
[10:15:31] 📄 RAW INPUT TEXT:
[10:15:31]    1. Name 6: ANANEV 1: VLADIMIR 2: VLADIMIROVICH 3: n/a 4: n/a
[10:15:31]    DOB: 03/07/1987. POB: Kyrgyzstan a.k.a: (1) DARKON...

[10:15:31] 🤖 AI STRUCTURED OUTPUT:
[10:15:31]    • Name: VLADIMIR VLADIMIROVICH ANANEV
[10:15:31]    • Sanction ID: CYB0071-16753
[10:15:31]    • Nationality: Russia
[10:15:31]    • Date of Birth: 03/07/1987
[10:15:31]    • Processing time: 1.2s
[10:15:31] ============================================================
```

### Final Metrics:
```
[10:16:45] 📈 Individual Extraction Metrics:
[10:16:45]    • Records processed: 70
[10:16:45]    • Success rate: 98.6%
[10:16:45]    • Average time per record: 0.85s
[10:16:45]    • Total processing time: 59.5s

[10:16:50] 💰 OpenAI API Usage & Cost Estimate:
[10:16:50]    • Model used: gpt-4o-mini
[10:16:50]    • Total API calls: 79
[10:16:50]    • Input tokens: 145,230
[10:16:50]    • Estimated cost: $0.0312
```

## 📄 Output Files

### 1. `individuals_extracted.json`
Clean array of individual sanctions:
```json
[
  {
    "sanctionId": "CYB0071-16753",
    "firstName": "VLADIMIR",
    "lastName": "ANANEV",
    "nationality": "Russia",
    "dateOfBirth": "03/07/1987",
    "passportNumber": "766211028",
    "aliases": ["DARKON", "THEVLADAN33"],
    ...
  }
]
```

### 2. `entities_extracted.json`
Clean array of entity sanctions:
```json
[
  {
    "sanctionId": "CYB0097-16991",
    "organizationName": "161ST SPECIALIST TRAINING CENTRE",
    "entityType": "MILITARY",
    "aliases": ["GRU Unit 29155"],
    ...
  }
]
```

## 🔬 Technical Details

### Data Extraction Process

1. **PDF Processing**: Extracts text while preserving structure
2. **Text Splitting**: Intelligently splits records using regex patterns
3. **AI Extraction**: Each record processed individually for accuracy
4. **Incremental Saving**: Results saved immediately after each extraction
5. **Validation**: Pydantic models ensure data consistency

### Cost Optimization

- Uses GPT-4o-mini for cost-effective processing
- Typical cost: ~$0.03 for 70 individuals + 9 entities
- Configurable token pricing for accurate cost tracking

### Error Handling

- Crash-resilient with incremental saving
- Partial results preserved on interruption
- Detailed error logging with recovery suggestions

## 🏗️ Pipeline Status

| Step | Status | Description |
|------|--------|-------------|
| 1. PDF to Text | ✅ Complete | Extracts text from sanctions PDF |
| 2. LLM Parsing | ✅ Complete | AI-powered data extraction |
| 3. Data Modeling | ✅ Complete | Structured Pydantic models |
| 4. Neo4j Loading | 🚧 Planned | Graph database integration |

## 🤝 Contributing

Contributions welcome! Please read our [Contributing Guide](CONTRIBUTING.md) for details.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- UK Government for providing sanctions data
- OpenAI for GPT-4o-mini API
- Neo4j community for graph database excellence

## 📞 Support

For issues or questions:
- Create an issue on GitHub
- Email: your.email@example.com

---

**Built with ❤️ for compliance teams worldwide**
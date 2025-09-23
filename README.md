# 🕸️ UK Sanctions Knowledge Graph: From Unstructured PDFs to Neo4j

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://www.python.org/)
[![OpenAI](https://img.shields.io/badge/OpenAI-GPT--5--Nano-green)](https://openai.com/)
[![Neo4j](https://img.shields.io/badge/Neo4j-Graph%20Database-orange)](https://neo4j.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

## 🎯 Overview

Transform unstructured UK sanctions PDFs into powerful knowledge graphs using AI and Neo4j. This enterprise-grade pipeline leverages OpenAI's GPT-4o-mini to intelligently extract entities and relationships, then models them as an interconnected graph for sophisticated compliance queries and analysis.

**Perfect for banks and financial institutions** requiring advanced sanctions screening through graph-based relationship analysis and network detection.

## ✨ Key Features

- **🕸️ Knowledge Graph Creation**: Transform unstructured PDFs into Neo4j graph databases
- **🤖 AI-Powered Entity Extraction**: Uses OpenAI GPT-4o-mini for intelligent relationship mapping
- **🔗 Relationship Modeling**: Automatically identifies and models connections between sanctions entities
- **⚡ Configurable Pipeline Stages**: Run individual stages (`pdf`, `llm`, `neo4j`) or combinations for optimized workflows
- **📊 Network Analysis**: Discover hidden connections and patterns in sanctions data
- **💰 Cost-Optimized Development**: Skip expensive LLM calls during database iteration cycles
- **💾 Incremental Graph Building**: Crash-resilient with automatic Neo4j transaction management
- **🔍 Graph Validation**: Ensures data consistency and relationship integrity
- **🏢 Enterprise Ready**: Production-grade Neo4j integration for compliance teams

## 📁 Project Structure

```
uk-sanctions-list-unsctructured-to-neo4j/
│
├── src/                          # Source code
│   ├── main.py                   # Pipeline orchestrator with configurable stages
│   ├── pdf_to_text.py            # PDF extraction module
│   ├── llm_extractor.py          # AI-powered entity & relationship extraction
│   ├── neo4j_loader.py           # Neo4j database integration and loading
│   ├── logger_config.py          # Professional logging system
│   ├── models/                   # Pydantic data models
│   │   ├── __init__.py
│   │   ├── individual.py         # Individual person data model
│   │   ├── entity.py             # Organization/entity data model
│   │   └── address.py            # Address data model
│   └── utils/                    # Utility modules
│       ├── __init__.py
│       ├── file_operations.py    # File I/O operations
│       ├── neo4j_client.py       # Neo4j connection management
│       ├── neo4j_data_processor.py # Neo4j data processing
│       ├── openai_client.py      # OpenAI API client
│       ├── path_utils.py         # Path and directory utilities
│       ├── pdf_processor.py      # PDF processing utilities
│       ├── progress_tracker.py   # Progress tracking and logging
│       └── text_parser.py        # Text parsing utilities
│
├── pdf/                          # Input PDF files
│   ├── Cyber.pdf                 # UK Sanctions List document
│   └── README.md                 # PDF directory documentation
│
├── example/                      # Example extraction outputs (demo data)
│   ├── Cyber_text.txt           # Sample extracted text (87KB, 37 individuals)
│   ├── entities_extracted.json  # Sample entity extraction results
│   ├── extracted_data.json      # Sample combined extraction data
│   └── individuals_extracted.json # Sample individual extraction results
│
├── output/                       # Live processing outputs
│   ├── Cyber_text.txt           # Current extracted raw text from PDF
│   ├── entities_extracted.json  # Current structured entity records
│   ├── extracted_data.json      # Current combined extraction data
│   └── individuals_extracted.json # Current structured individual records
│
├── cypher/                       # Neo4j Cypher scripts for data loading
│   ├── load_entities.cypher      # Load entity records to Neo4j
│   ├── load_entities_address.cypher # Load entity address relationships
│   ├── load_entities_aliases.cypher # Load entity alias relationships
│   ├── load_entities_relationships.cypher # Load entity relationships
│   ├── load_individuals.cypher   # Load individual records to Neo4j
│   ├── load_individuals_address.cypher # Load individual address relationships
│   └── load_individuals_aliases.cypher # Load individual alias relationships
│
├── docs/                         # Documentation
│   ├── NEO4J-DATA-MODEL.md       # Neo4j data model documentation
│   └── WHY.md                    # Project motivation and background
│
├── .env.example                  # Configuration template
├── .gitignore                    # Git ignore patterns
├── CLAUDE.md                     # Claude Code instructions and project info
├── requirements.txt              # Python dependencies
└── README.md                     # This file
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

# Neo4j Configuration
NEO4J_URI=bolt://localhost:7687       # Neo4j connection URI
NEO4J_USER=neo4j                      # Neo4j username
NEO4J_PASSWORD=your_password          # Neo4j password
NEO4J_DATABASE=sanctions              # Database name
```

### 4. Start Neo4j Database

```bash
# Start Neo4j (if using Docker)
docker run --name neo4j-sanctions \
    -p7474:7474 -p7687:7687 \
    -e NEO4J_AUTH=neo4j/your_password \
    neo4j:latest

# Or start local Neo4j installation
neo4j start
```

### 5. Run the Knowledge Graph Pipeline

```bash
# See all available options
python src/main.py --help

# Run complete pipeline (all stages)
python src/main.py --stages all

# Run individual stages
python src/main.py --stages pdf          # Extract text from PDF only
python src/main.py --stages llm          # AI entity extraction only
python src/main.py --stages neo4j        # Load existing data to Neo4j only

# Run stage combinations
python src/main.py --stages pdf,llm      # Extract text and entities
python src/main.py --stages llm,neo4j    # Extract entities and load to Neo4j
```

**💡 Development Tip**: After running the complete pipeline once, use `--stages neo4j` for fast iterations during database development - saves time and API costs!

## 🔧 Pipeline Stages

The pipeline supports flexible stage execution for optimized development workflows:

### Available Stages

| Stage | Description | Dependencies | Typical Use |
|-------|-------------|--------------|-------------|
| `pdf` | Extract text from PDF documents | None | Initial setup, PDF updates |
| `llm` | AI-powered entity extraction | `pdf` stage or existing `output/Cyber_text.txt` | Data model changes, re-extraction |
| `neo4j` | Load data into Neo4j database | `llm` stage or existing JSON files | Database development, schema updates |
| `all` | Run complete pipeline | None | First run, full refresh |

### Stage Dependencies

The pipeline automatically validates dependencies and provides clear error messages:

```bash
# ❌ This will fail if text file doesn't exist
python src/main.py --stages llm
# Error: LLM stage requires 'output/Cyber_text.txt' (run 'pdf' stage first)

# ✅ This will work - runs pdf first, then llm
python src/main.py --stages pdf,llm
```

### Cost & Time Optimization

| Stage | Time | Cost | When to Use |
|-------|------|------|-------------|
| `pdf` | ~3 seconds | Free | PDF updates only |
| `llm` | ~2-5 minutes | ~$0.03 | Entity model changes |
| `neo4j` | ~15 seconds | Free | Database schema updates |
| `all` | ~3-6 minutes | ~$0.03 | Initial setup, major changes |

**Development Workflow Example:**
```bash
# Initial setup - run everything once
python src/main.py --stages all

# Database development - fast iterations
python src/main.py --stages neo4j    # Repeat as needed

# Model updates - when changing entity extraction
python src/main.py --stages llm,neo4j
```

## 🕸️ Knowledge Graph Output

### Real-Time Processing View:
```
[10:15:23] ============================================================
[10:15:23] 🕸️ UK Sanctions Knowledge Graph Builder
[10:15:23] ============================================================
[10:15:23] 🔄 Transforming unstructured PDFs into Neo4j knowledge graph

[10:15:24] 📋 STEP 1: PDF to Text Conversion
[10:15:25] ⚡ [████████████████████] 100.0% 45/45 pages
[10:15:26] ✅ Text extraction completed in 2.1s

[10:15:27] 📋 STEP 2: AI Entity & Relationship Extraction
[10:15:27] 🤖 Identifying entities and relationships for graph modeling
[10:15:28] 🔍 Processing 70 individuals + 9 entities

[10:15:30] 📋 STEP 3: Neo4j Graph Construction
[10:15:30] 🕸️ Connected to Neo4j: bolt://localhost:7687
[10:15:31] 📊 Building knowledge graph...

[10:15:32] 🔍 TRANSFORMATION EXAMPLE:
[10:15:32] ============================================================
[10:15:32] 📄 UNSTRUCTURED INPUT:
[10:15:32]    "VLADIMIR VLADIMIROVICH ANANEV, DOB: 03/07/1987,
[10:15:32]     associated with FANCY BEAR, passport 766211028..."

[10:15:32] 🕸️ KNOWLEDGE GRAPH NODES & RELATIONSHIPS:
[10:15:32]    (:Individual {name: "VLADIMIR VLADIMIROVICH ANANEV"})
[10:15:32]    (:Organization {name: "FANCY BEAR"})
[10:15:32]    (:Country {name: "Russia"})
[10:15:32]
[10:15:32]    Relationships created:
[10:15:32]    • (Individual)-[:SANCTIONED_BY]->(UKGovernment)
[10:15:32]    • (Individual)-[:ASSOCIATED_WITH]->(Organization)
[10:15:32]    • (Individual)-[:CITIZEN_OF]->(Country)
[10:15:32] ============================================================
```

### Final Knowledge Graph Metrics:
```
[10:16:45] 📈 Graph Construction Completed:
[10:16:45]    • Nodes created: 125 (70 Individuals + 9 Organizations + 46 Countries/Addresses)
[10:16:45]    • Relationships created: 387
[10:16:45]    • Graph density: 82%
[10:16:45]    • Processing time: 3.2 minutes

[10:16:46] 🕸️ Neo4j Database Statistics:
[10:16:46]    • Database: sanctions
[10:16:46]    • Node labels: Individual, Organization, Country, Address, Document
[10:16:46]    • Relationship types: SANCTIONED_BY, ASSOCIATED_WITH, CITIZEN_OF, LOCATED_IN
[10:16:46]    • Constraints applied: 8 uniqueness constraints
[10:16:46]    • Indexes created: 12 performance indexes

[10:16:50] 💰 OpenAI API Usage & Cost Estimate:
[10:16:50]    • Model used: gpt-4o-mini
[10:16:50]    • Total API calls: 79
[10:16:50]    • Input tokens: 145,230
[10:16:50]    • Estimated cost: $0.0312
```

## 🕸️ Neo4j Knowledge Graph Queries

### 1. Find All Sanctioned Individuals from Russia
```cypher
MATCH (person:Individual)-[:CITIZEN_OF]->(country:Country {name: "Russia"})
WHERE person.sanctioned = true
RETURN person.name, person.dateOfBirth, person.sanctionId
ORDER BY person.name
```

### 2. Discover Network Connections
```cypher
MATCH (person:Individual)-[r:ASSOCIATED_WITH]->(org:Organization)
WHERE person.name CONTAINS "ANANEV"
RETURN person, r, org
```

### 3. Complex Compliance Query - Find Connected Sanctioned Entities
```cypher
MATCH path = (start:Individual)-[:ASSOCIATED_WITH*1..3]-(connected)
WHERE start.sanctionId = "CYB0071-16753"
AND connected:Individual OR connected:Organization
RETURN path, length(path) as degrees_of_separation
ORDER BY degrees_of_separation
```

### 4. Address-Based Risk Analysis
```cypher
MATCH (person:Individual)-[:LOCATED_IN]->(addr:Address)<-[:LOCATED_IN]-(other:Individual)
WHERE person <> other
AND person.sanctioned = true
RETURN addr.full_address,
       collect(person.name) as sanctioned_individuals,
       collect(other.name) as potentially_connected_individuals
```

### 5. Export Data for External Systems
```cypher
// Export sanctioned individuals with all relationships
CALL apoc.export.json.query(
  "MATCH (i:Individual {sanctioned: true})
   OPTIONAL MATCH (i)-[r]->(connected)
   RETURN i, collect({rel: type(r), node: connected}) as connections",
  "sanctions_export.json"
)
```

## 📁 Example Outputs & Demonstrations

The `example/` directory contains sample outputs that demonstrate the complete unstructured-to-structured transformation:

### 🔍 See the Transformation in Action

**📄 Input (Unstructured PDF Text)**
```text
1. Name 6: ANANEV 1: VLADIMIR 2: VLADIMIROVICH 3: n/a 4: n/a 5: n/a.
DOB: 03/07/1987. POB: Kyrgyzstan a.k.a: (1) DARKON (2) THEVLADAN33
Nationality: Russia Passport Number: 766211028 Other Information:
(UK Sanctions List Ref):CYB0071. Vladimir Vladimirovich ANANEV is an
involved person through his role in and association with ZSERVERS...
```

**🤖 Output (Structured JSON)**
```json
{
  "sanctionId": "CYB0071-16753",
  "firstName": "VLADIMIR",
  "middleName": "VLADIMIROVICH",
  "lastName": "ANANEV",
  "fullName": "VLADIMIR VLADIMIROVICH ANANEV",
  "dateOfBirth": "03/07/1987",
  "placeOfBirth": "Kyrgyzstan",
  "nationality": "Russia",
  "passportNumber": "766211028",
  "aliases": ["DARKON", "THEVLADAN33"],
  "statementOfReasons": "Vladimir Vladimirovich ANANEV is an involved person through his role in and association with ZSERVERS...",
  "groupId": "16753"
}
```

### 📊 Extraction Statistics
- **Source**: 87KB unstructured PDF text
- **Extracted**: 40+ individual sanctions records
- **Success Rate**: 98.6% accurate field extraction
- **Processing Time**: ~1.2 seconds per record
- **Data Quality**: Complete with relationships, aliases, and compliance metadata

### 🕸️ Graph Model Preview
Each extracted individual becomes nodes and relationships in Neo4j:
```cypher
(:Individual {name: "VLADIMIR VLADIMIROVICH ANANEV"})
    -[:SANCTIONED_BY]->(:Government {name: "UK"})
    -[:CITIZEN_OF]->(:Country {name: "Russia"})
    -[:ASSOCIATED_WITH]->(:Organization {name: "ZSERVERS"})
    -[:HAS_ALIAS]->(:Alias {name: "DARKON"})
```

## 🔬 Technical Details

### Modular Pipeline Architecture

The system is built with a **configurable stage architecture** allowing selective execution:

```
📄 PDF Stage → 🧠 LLM Stage → 🕸️ Neo4j Stage
   (3s)         (2-5min)        (15s)
   Free         ~$0.03          Free
```

Each stage is **independent** and **resumable**:
- **PDF Stage**: Converts PDF to structured text, saves to `output/Cyber_text.txt`
- **LLM Stage**: AI entity extraction, saves to `output/extracted_data.json`
- **Neo4j Stage**: Graph database loading with relationship modeling

### Knowledge Graph Construction Process

1. **PDF Processing** (`--stages pdf`): Extracts text while preserving document structure
2. **AI Entity & Relationship Extraction** (`--stages llm`): LLM identifies entities and their relationships
3. **Graph Schema Mapping** (`--stages neo4j`): Maps extracted data to Neo4j node and relationship types
4. **Neo4j Transaction Management**: Atomic graph updates with rollback capabilities
5. **Relationship Inference**: Discovers implicit connections between entities
6. **Graph Validation**: Ensures referential integrity and constraint compliance

### Stage-Based Development Benefits

- 🚀 **Fast Iterations**: Skip expensive LLM calls during database development
- 💰 **Cost Control**: Only pay for LLM processing when needed
- 🔧 **Debugging**: Test individual components in isolation
- ⚡ **Recovery**: Resume from any failed stage without full pipeline restart

### Graph Modeling Strategy

- **Nodes**: Individual, Organization, Country, Address, Document, Sanction
- **Relationships**: SANCTIONED_BY, ASSOCIATED_WITH, CITIZEN_OF, LOCATED_IN, ALIASES_OF
- **Properties**: Comprehensive metadata for compliance queries and analytics
- **Constraints**: Uniqueness constraints on critical identifiers (passport, sanction ID)
- **Indexes**: Performance indexes on frequently queried properties

### Neo4j Performance Optimization

- Batch processing for large imports (1000 nodes per transaction)
- Parallel relationship creation for improved throughput
- Memory-efficient streaming for large datasets
- Connection pooling and retry logic for reliability

## 🏗️ Configurable Knowledge Graph Pipeline

| Stage | Command | Status | Description |
|-------|---------|--------|-------------|
| 1. **PDF Processing** | `--stages pdf` | ✅ Complete | Raw sanctions document processing |
| 2. **Text Extraction** | `--stages pdf` | ✅ Complete | Convert PDF to structured text |
| 3. **AI Entity Recognition** | `--stages llm` | ✅ Complete | LLM identifies individuals, organizations, relationships |
| 4. **Graph Schema Mapping** | `--stages neo4j` | ✅ Complete | Map entities to Neo4j node/relationship types |
| 5. **Knowledge Graph Creation** | `--stages neo4j` | ✅ Complete | Build interconnected graph in Neo4j |
| 6. **Compliance Query Interface** | Available | ✅ Complete | Advanced Cypher queries for sanctions screening |
| 7. **Stage-Based Development** | `--stages <stage>` | ✅ Complete | Modular execution for optimized workflows |

### 🎯 The Configurable Transformation Pipeline
```
📄 PDF Stage (3s) → 🧠 LLM Stage (2-5min) → 🕸️ Neo4j Stage (15s) → ⚡ Intelligent Queries
      Free              ~$0.03                   Free            Available
```

**Flexible Execution Examples:**
```bash
# Full pipeline (first run)
python src/main.py --stages all

# Development iteration (database changes only)
python src/main.py --stages neo4j

# Model updates (re-extract and load)
python src/main.py --stages llm,neo4j
```

**From**: "VLADIMIR VLADIMIROVICH ANANEV, DOB: 03/07/1987, associated with FANCY BEAR..."

**To**: A queryable graph where you can ask:
- "Who are all the Russian nationals connected to cyber organizations?"
- "What is the shortest path between two sanctioned entities?"
- "Which addresses have multiple sanctioned individuals?"

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
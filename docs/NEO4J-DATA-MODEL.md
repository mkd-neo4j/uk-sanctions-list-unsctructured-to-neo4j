# Neo4j Data Model for UK Sanctions List

## Overview

This document outlines the data model for storing UK sanctions data in Neo4j, aligned with the [Neo4j Transactional Data Model](https://neo4j.com/developer/industry-use-cases/data-models/transactions/transactions-base-model/) patterns. The model transforms unstructured PDF sanctions data into a graph structure optimised for compliance screening, relationship analysis, and fraud detection.

## Table of Contents

1. [Current State Analysis](#current-state-analysis)
2. [Neo4j Base Model Alignment](#neo4j-base-model-alignment)
3. [Proposed Node Structure](#proposed-node-structure)
4. [Relationship Patterns](#relationship-patterns)
5. [Property Conventions](#property-conventions)
6. [Migration Strategy](#migration-strategy)
7. [Cypher Examples](#cypher-examples)
8. [Constraints and Indices](#constraints-and-indices)

## Current State Analysis

The existing pipeline extracts sanctions data into three primary Pydantic models:

### Existing Models
- **SanctionedIndividual**: Contains personal information, identifiers, addresses, and sanctions metadata
- **SanctionedEntity**: Represents organisations with registration details and corporate relationships
- **Address**: Structured location data with raw preservation

### Current Data Structure
```json
{
  "individuals": [
    {
      "sanctionId": "CYB0043-16345",
      "ukSanctionsRef": "CYB0043",
      "fullName": "ERMAKOV ALEKSANDR GENNADIEVICH",
      "aliases": ["BLADE_RUNNER", "GISTAVEDORE"],
      "dateOfBirth": "16/05/1990",
      "nationality": "Russia"
    }
  ],
  "entities": [
    {
      "sanctionId": "CYB0044-16460",
      "organizationName": "WUHAN XIAORUIZHI SCIENCE AND TECHNOLOGY COMPANY LIMITED",
      "entityType": "BUSINESS"
    }
  ]
}
```

## Neo4j Base Model Alignment

Following Neo4j's transactional model conventions, we map sanctions data to established patterns:

### Core Principles
1. **Multi-label nodes** for flexible categorisation
2. **Semantic relationships** with directional meaning
3. **Comprehensive metadata** on both nodes and relationships
4. **Property naming** using camelCase convention
5. **Temporal tracking** for compliance audit trails

### Alignment with Base Model
| Base Model Pattern | Sanctions Implementation |
|-------------------|-------------------------|
| Identity Nodes | Person, Organisation |
| Identity Documents | Passport, NationalId |
| Location Nodes | Address, Country |
| Classification | SanctionsRegime, GroupId |
| Temporal | ListedDate, LastUpdated |

## Proposed Node Structure

### 1. Person Nodes
```
(:Person:SanctionedIndividual)
```
**Properties:**
- `sanctionId`: Unique identifier
- `ukSanctionsRef`: UK reference (e.g., CYB0043)
- `firstName`: Given name
- `middleName`: Middle name(s)
- `lastName`: Surname
- `fullName`: Complete name as listed
- `nameNonLatinScript`: Native script name
- `dateOfBirth`: DOB in ISO format
- `placeOfBirth`: Birth location
- `gender`: Gender if specified
- `position`: Role or title
- `listedOn`: Sanctions listing date
- `lastUpdated`: Last modification date

### 2. Organisation Nodes
```
(:Organisation:SanctionedEntity)
```
**Properties:**
- `sanctionId`: Unique identifier
- `ukSanctionsRef`: UK reference
- `organisationName`: Primary name
- `nameNonLatinScript`: Native script name
- `entityType`: Classification (BUSINESS, GOVERNMENT, etc.)
- `registrationNumber`: Company registration
- `listedOn`: Sanctions listing date
- `lastUpdated`: Last modification date

### 3. Address Nodes
```
(:Address)
```
**Properties:**
- `addressId`: Generated unique ID
- `rawAddress`: Original text
- `addressLine1`: Primary line
- `addressLine2`: Secondary line
- `postTown`: City/town
- `postCode`: Postal code
- `region`: State/province

### 4. Document Nodes
```
(:Passport)
```
**Properties:**
- `documentId`: Passport number
- `documentType`: "PASSPORT"
- `issuingCountry`: Country of issue
- `verificationStatus`: Validation state

```
(:NationalId)
```
**Properties:**
- `documentId`: ID number
- `documentType`: "NATIONAL_ID"
- `issuingCountry`: Country of issue

### 5. Alias Nodes
```
(:Alias)
```
**Properties:**
- `aliasName`: Alternative name (original form for display)
- `aliasId`: Normalized name for matching (lowercase, trimmed, no special chars)
- `aliasType`: Classification (NICKNAME, TRADENAME, etc.)

**Normalization Rules for `aliasId`:**
1. Convert to lowercase
2. Trim leading and trailing whitespace
3. Collapse multiple spaces to single space
4. Remove special characters (keep only alphanumeric and spaces)
5. Normalize Unicode characters (é → e, ñ → n)

**Examples:**
- "Boss" → `aliasId: "boss"`
- "BOSS" → `aliasId: "boss"`
- " The Boss " → `aliasId: "the boss"`
- "The-Boss!" → `aliasId: "the boss"`
- "José" → `aliasId: "jose"`

### 6. Sanctions List Nodes
```
(:SanctionsList)
```
**Properties:**
- `listId`: Unique identifier (e.g., "UK_CYBER_2024_01")
- `listName`: Full name of the list (e.g., "UK Cyber Sanctions List")
- `fileName`: Source file name (e.g., "cyber.pdf")
- `publicationDate`: Date the list was published by the authority
- `extractionDate`: Date when data was extracted from the document
- `sourceUrl`: Official government URL where the list was obtained
- `totalIndividuals`: Count of individuals on this list
- `totalEntities`: Count of entities on this list
- `authority`: Publishing authority (e.g., "HM Treasury")
- `version`: Version number or date identifier
- `hash`: Document hash for integrity verification

### 7. Sanctions Regime Nodes
```
(:SanctionsRegime:CyberSanctions)
```
**Properties:**
- `regimeId`: "UK_CYBER_SANCTIONS"
- `regimeName`: "UK Cyber Sanctions"
- `authority`: "HM Treasury"
- `legalBasis`: Legal framework for sanctions
- `lastUpdated`: Latest update date

### 8. Group Nodes
```
(:SanctionGroup)
```
**Properties:**
- `groupId`: Group identifier from source
- `groupType`: Classification if available

### 9. Country Nodes
```
(:Country)
```
**Properties:**
- `code`: Two-letter ISO 3166-1 alpha-2 country code (e.g., "GB", "RU", "CN")
- `name`: Official country name in English (e.g., "United Kingdom", "Russia", "China")

## Relationship Patterns

### Core Relationships

#### 1. Identity Relationships
```cypher
(person:Person)-[:HAS_ADDRESS]->(address:Address)
(organisation:Organisation)-[:HAS_ADDRESS]->(address:Address)
(person:Person)-[:HAS_PASSPORT]->(passport:Passport)
(person:Person)-[:HAS_NATIONAL_ID]->(nationalId:NationalId)
(person:Person)-[:ALSO_KNOWN_AS]->(alias:Alias)
(organisation:Organisation)-[:ALSO_KNOWN_AS]->(alias:Alias)
```

#### 2. Sanctions List Relationships
```cypher
// Connect individuals and organisations to the sanctions list document they appear on
(person:Person)-[:LISTED_ON {
  pageNumber: integer,
  entryNumber: integer,
  addedDate: date
}]->(list:SanctionsList)

(organisation:Organisation)-[:LISTED_ON {
  pageNumber: integer,
  entryNumber: integer,
  addedDate: date
}]->(list:SanctionsList)

// Connect the list to the sanctions regime it implements
(list:SanctionsList)-[:IMPLEMENTS]->(regime:SanctionsRegime)
```

#### 3. Sanctions Regime Relationships
```cypher
// Connect persons/orgs to the type of sanctions they're under
(person:Person)-[:SANCTIONED_UNDER {
  listedOn: date,
  statementOfReasons: string,
  lastUpdated: date
}]->(regime:SanctionsRegime)

(organisation:Organisation)-[:SANCTIONED_UNDER {
  listedOn: date,
  statementOfReasons: string,
  lastUpdated: date
}]->(regime:SanctionsRegime)
```

#### 4. Group Relationships
```cypher
(person:Person)-[:MEMBER_OF]->(group:SanctionGroup)
(organisation:Organisation)-[:MEMBER_OF]->(group:SanctionGroup)
```

#### 4. Corporate Relationships
```cypher
(organisation:Organisation)-[:PARENT_OF]->(subsidiary:Organisation)
(organisation:Organisation)-[:RELATED_TO {
  relationshipType: string
}]->(relatedOrg:Organisation)
```

#### 5. Location and Nationality Relationships
```cypher
// Connect addresses to their countries
(address:Address)-[:LOCATED_IN]->(country:Country)

// Connect persons to their nationality countries
(person:Person)-[:HAS_NATIONALITY]->(country:Country)

// Connect place of birth to countries (if structured)
(person:Person)-[:BORN_IN]->(country:Country)
```

## Property Conventions

### Naming Standards
- **Properties**: camelCase (e.g., `firstName`, `dateOfBirth`)
- **Node Labels**: PascalCase (e.g., `Person`, `SanctionedIndividual`)
- **Relationships**: UPPER_SNAKE_CASE (e.g., `HAS_ADDRESS`, `SANCTIONED_UNDER`)

### Data Types
- **Dates**: ISO 8601 format strings or Neo4j date types
- **IDs**: String format with source prefix
- **Names**: Preserve original capitalisation
- **Metadata**: Store as relationship properties where appropriate

### Required vs Optional
- **Required**: sanctionId, ukSanctionsRef, primary name fields
- **Optional**: All biographical details, addresses, documents
- **Preserved**: Raw data fields for compliance audit

## Migration Strategy

### Phase 1: Data Transformation
1. Parse existing JSON output files
2. Generate unique IDs for addresses and aliases
3. Normalise date formats to ISO 8601
4. Extract document numbers from text fields

### Phase 2: Node Creation
```python
# Example transformation pipeline
def transform_individual_to_nodes(individual):
    nodes = {
        'person': create_person_node(individual),
        'addresses': extract_address_nodes(individual.address),
        'aliases': extract_alias_nodes(individual.aliases),
        'documents': extract_document_nodes(individual)
    }
    return nodes
```

### Phase 3: Relationship Building
1. Connect persons to addresses
2. Link documents to persons
3. Establish sanctions regime relationships
4. Create group associations

### Phase 4: Data Quality
1. Validate required fields
2. Check relationship consistency
3. Verify unique constraints
4. Audit data completeness

## Cypher Examples

### Creating Person with Full Structure
```cypher
// Create person node
CREATE (p:Person:SanctionedIndividual {
  sanctionId: 'CYB0043-16345',
  ukSanctionsRef: 'CYB0043',
  firstName: 'Aleksandr',
  middleName: 'Gennadievich',
  lastName: 'Ermakov',
  fullName: 'ERMAKOV ALEKSANDR GENNADIEVICH',
  nameNonLatinScript: 'Александр Геннадьевич Ермаков',
  dateOfBirth: date('1990-05-16'),
  gender: 'Male',
  listedOn: date('2024-01-23'),
  lastUpdated: date('2024-01-23')
})

// Create or merge country for nationality
MERGE (russia:Country {code: 'RU'})
ON CREATE SET russia.name = 'Russia'
CREATE (p)-[:HAS_NATIONALITY]->(russia)

// Create and connect address
CREATE (a:Address {
  addressId: 'addr_' + randomUUID(),
  rawAddress: 'Moscow, Russia',
  postTown: 'Moscow'
})
CREATE (p)-[:HAS_ADDRESS]->(a)
CREATE (a)-[:LOCATED_IN]->(russia)

// Create and connect aliases
WITH p
UNWIND ['BLADE_RUNNER', 'GISTAVEDORE'] AS aliasName
MERGE (alias:Alias {
  aliasId: toLower(trim(aliasName))
})
ON CREATE SET
  alias.aliasName = aliasName,
  alias.aliasType = 'NICKNAME'
CREATE (p)-[:ALSO_KNOWN_AS]->(alias)

// Connect to sanctions list document
MERGE (list:SanctionsList {
  listId: 'UK_CYBER_2024_01'
})
ON CREATE SET
  list.listName = 'UK Cyber Sanctions List',
  list.fileName = 'cyber.pdf',
  list.publicationDate = date('2024-01-23'),
  list.extractionDate = date('2024-01-25'),
  list.sourceUrl = 'https://www.gov.uk/government/publications/uk-sanctions-list',
  list.totalIndividuals = 70,
  list.totalEntities = 9,
  list.authority = 'HM Treasury'
CREATE (p)-[:LISTED_ON {
  pageNumber: 3,
  entryNumber: 43,
  addedDate: date('2024-01-23')
}]->(list)

// Connect to sanctions regime
MERGE (regime:SanctionsRegime:CyberSanctions {
  regimeId: 'UK_CYBER_SANCTIONS'
})
ON CREATE SET
  regime.regimeName = 'UK Cyber Sanctions',
  regime.authority = 'HM Treasury',
  regime.legalBasis = 'The Cyber (Sanctions) (EU Exit) Regulations 2020'
CREATE (p)-[:SANCTIONED_UNDER {
  listedOn: date('2024-01-23'),
  statementOfReasons: 'Involved in relevant cyber activity...',
  lastUpdated: date('2024-01-23')
}]->(regime)

// Connect list to regime
MERGE (list)-[:IMPLEMENTS]->(regime)
```

### Creating Organisation with Relationships
```cypher
// Create organisation
CREATE (o:Organisation:SanctionedEntity {
  sanctionId: 'CYB0044-16460',
  ukSanctionsRef: 'CYB0044',
  organisationName: 'WUHAN XIAORUIZHI SCIENCE AND TECHNOLOGY COMPANY LIMITED',
  nameNonLatinScript: '武汉晓睿智科技有限责任公司',
  entityType: 'BUSINESS',
  listedOn: date('2024-03-25')
})

// Connect to sanctions list
MERGE (list:SanctionsList {
  listId: 'UK_CYBER_2024_01'
})
CREATE (o)-[:LISTED_ON {
  pageNumber: 5,
  entryNumber: 44,
  addedDate: date('2024-03-25')
}]->(list)

// Connect to sanctions regime
MERGE (regime:SanctionsRegime:CyberSanctions {
  regimeId: 'UK_CYBER_SANCTIONS'
})
CREATE (o)-[:SANCTIONED_UNDER {
  listedOn: date('2024-03-25'),
  statementOfReasons: 'Associated with Advanced Persistent Threat Group 31...',
  lastUpdated: date('2024-03-25')
}]->(regime)

// Create address with full structure
CREATE (a:Address {
  addressId: 'addr_' + randomUUID(),
  rawAddress: '2nd Floor, No. 16, Huashiyuan North Road, East Lake New Technology Development Zone, Hubei Province, Wuhan, China',
  addressLine1: 'No. 16, Huashiyuan North Road',
  addressLine2: '2nd Floor',
  postTown: 'Wuhan',
  region: 'Hubei Province'
})
CREATE (o)-[:HAS_ADDRESS]->(a)

// Connect address to country
MERGE (china:Country {code: 'CN'})
ON CREATE SET china.name = 'China'
CREATE (a)-[:LOCATED_IN]->(china)

// Link to related entities
MERGE (apt:Organisation {organisationName: 'Advanced Persistent Threat Group 31 (APT31)'})
CREATE (o)-[:RELATED_TO {relationshipType: 'ASSOCIATED'}]->(apt)
```

### Query Examples

#### Find all people on a specific sanctions list
```cypher
MATCH (p:Person)-[:LISTED_ON]->(list:SanctionsList {listId: 'UK_CYBER_2024_01'})
OPTIONAL MATCH (p)-[:HAS_NATIONALITY]->(country:Country)
RETURN p.fullName, p.ukSanctionsRef, country.name as nationality
ORDER BY p.lastName
```

#### Find people appearing on multiple sanctions lists
```cypher
MATCH (p:Person)-[:LISTED_ON]->(list:SanctionsList)
WITH p, count(DISTINCT list) as listCount, collect(list.listName) as lists
WHERE listCount > 1
RETURN p.fullName, p.ukSanctionsRef, listCount, lists
ORDER BY listCount DESC
```

#### Track when someone was added to different lists
```cypher
MATCH (p:Person {fullName: 'ERMAKOV ALEKSANDR GENNADIEVICH'})-[r:LISTED_ON]->(list:SanctionsList)
RETURN list.listName, list.publicationDate, r.addedDate, list.fileName
ORDER BY r.addedDate
```

#### Compare sanctions lists over time
```cypher
// Find people added in the latest list but not in previous versions
MATCH (newList:SanctionsList {listId: 'UK_CYBER_2024_02'})
MATCH (oldList:SanctionsList {listId: 'UK_CYBER_2024_01'})
MATCH (p:Person)-[:LISTED_ON]->(newList)
WHERE NOT EXISTS {
  MATCH (p)-[:LISTED_ON]->(oldList)
}
RETURN p.fullName, p.ukSanctionsRef as 'Newly Added Individuals'
```

#### Find all lists implementing a specific sanctions regime
```cypher
MATCH (list:SanctionsList)-[:IMPLEMENTS]->(regime:SanctionsRegime {regimeId: 'UK_CYBER_SANCTIONS'})
RETURN list.listName, list.publicationDate, list.totalIndividuals, list.totalEntities
ORDER BY list.publicationDate DESC
```

#### Find all sanctioned individuals from Russia
```cypher
MATCH (p:Person:SanctionedIndividual)-[:HAS_NATIONALITY]->(country:Country {name: 'Russia'})
RETURN p.fullName, p.dateOfBirth, p.ukSanctionsRef
ORDER BY p.lastName
```

#### Find connections between entities
```cypher
MATCH path = (e1:Organisation)-[*1..3]-(e2:Organisation)
WHERE e1.sanctionId STARTS WITH 'CYB'
  AND e2.sanctionId STARTS WITH 'CYB'
  AND e1 <> e2
RETURN path
```

#### Find individuals with multiple aliases
```cypher
MATCH (p:Person)-[:ALSO_KNOWN_AS]->(a:Alias)
WITH p, count(a) as aliasCount
WHERE aliasCount > 2
MATCH (p)-[:ALSO_KNOWN_AS]->(alias:Alias)
RETURN p.fullName, collect(alias.aliasName) as aliases, aliasCount
ORDER BY aliasCount DESC
```

#### Find all people sharing the same normalized alias
```cypher
// Find all sanctioned individuals who use variations of "Boss" as an alias
MATCH (a:Alias)-[:ALSO_KNOWN_AS]-(p:Person)
WHERE a.aliasId = "boss"  // Matches "Boss", "BOSS", " boss ", "THE BOSS", etc.
RETURN a.aliasName as originalAlias, p.fullName, p.ukSanctionsRef
ORDER BY p.fullName
```

#### Compliance check for a specific name
```cypher
WITH 'ERMAKOV' as searchName, toLower(trim('ERMAKOV')) as normalizedSearch
MATCH (p:Person:SanctionedIndividual)-[:LISTED_ON]->(list:SanctionsList)
WHERE p.fullName CONTAINS searchName
   OR p.lastName = searchName
OPTIONAL MATCH (p)-[:ALSO_KNOWN_AS]->(a:Alias)
WHERE a.aliasName CONTAINS searchName
   OR a.aliasId CONTAINS normalizedSearch
RETURN DISTINCT p.sanctionId, p.fullName, p.ukSanctionsRef, collect(DISTINCT list.listName) as appearingOnLists
```

#### Audit trail: Track all updates to a sanctions list
```cypher
MATCH (list:SanctionsList)
WHERE list.listName CONTAINS 'Cyber'
RETURN list.listId, list.publicationDate, list.extractionDate, list.totalIndividuals, list.totalEntities
ORDER BY list.publicationDate DESC
```

#### Find people by multiple nationalities
```cypher
MATCH (p:Person)-[:HAS_NATIONALITY]->(c:Country)
WHERE c.code IN ['RU', 'CN', 'IR']
RETURN c.name as country, count(p) as sanctionedIndividuals
ORDER BY sanctionedIndividuals DESC
```

#### Find addresses in high-risk countries
```cypher
MATCH (a:Address)-[:LOCATED_IN]->(c:Country)
WHERE c.code IN ['RU', 'CN', 'KP', 'IR']
MATCH (p:Person)-[:HAS_ADDRESS]->(a)
RETURN c.name as country, p.fullName, a.rawAddress
ORDER BY c.name, p.fullName
```

## Constraints and Indices

### Unique Constraints
```cypher
// Ensure unique sanctions IDs
CREATE CONSTRAINT unique_person_sanction_id IF NOT EXISTS
FOR (p:Person) REQUIRE p.sanctionId IS UNIQUE;

CREATE CONSTRAINT unique_org_sanction_id IF NOT EXISTS
FOR (o:Organisation) REQUIRE o.sanctionId IS UNIQUE;

// Ensure unique sanctions list IDs
CREATE CONSTRAINT unique_list_id IF NOT EXISTS
FOR (l:SanctionsList) REQUIRE l.listId IS UNIQUE;

// Ensure unique country codes
CREATE CONSTRAINT unique_country_code IF NOT EXISTS
FOR (c:Country) REQUIRE c.code IS UNIQUE;

// Ensure unique document IDs
CREATE CONSTRAINT unique_passport_id IF NOT EXISTS
FOR (d:Passport) REQUIRE d.documentId IS UNIQUE;

// Ensure unique alias keys (normalized names)
CREATE CONSTRAINT unique_alias_key IF NOT EXISTS
FOR (a:Alias) REQUIRE a.aliasId IS UNIQUE;
```

### Indices for Performance
```cypher
// Name searches
CREATE INDEX person_fullname IF NOT EXISTS
FOR (p:Person) ON (p.fullName);

CREATE INDEX person_lastname IF NOT EXISTS
FOR (p:Person) ON (p.lastName);

CREATE INDEX org_name IF NOT EXISTS
FOR (o:Organisation) ON (organisationName);

// Date-based queries
CREATE INDEX person_listed_date IF NOT EXISTS
FOR (p:Person) ON (p.listedOn);

// Sanctions list queries
CREATE INDEX list_publication_date IF NOT EXISTS
FOR (l:SanctionsList) ON (l.publicationDate);

CREATE INDEX list_name IF NOT EXISTS
FOR (l:SanctionsList) ON (l.listName);

// Country queries
CREATE INDEX country_name IF NOT EXISTS
FOR (c:Country) ON (c.name);

CREATE INDEX country_code IF NOT EXISTS
FOR (c:Country) ON (c.code);

// Alias searches (both normalized and original)
CREATE INDEX alias_key IF NOT EXISTS
FOR (a:Alias) ON (a.aliasId);

CREATE INDEX alias_name IF NOT EXISTS
FOR (a:Alias) ON (a.aliasName);

// Full-text search
CREATE FULLTEXT INDEX person_name_search IF NOT EXISTS
FOR (p:Person) ON EACH [p.fullName, p.firstName, p.lastName];

CREATE FULLTEXT INDEX alias_search IF NOT EXISTS
FOR (a:Alias) ON EACH [a.aliasName, a.aliasId];
```

## Implementation Notes

### Data Quality Considerations
1. **Deduplication**: Implement matching algorithms for potential duplicate persons/organisations
2. **Data Validation**: Ensure date formats, country codes follow standards
3. **Missing Data**: Use NULL for absent fields rather than empty strings
4. **Versioning**: Consider temporal versioning for sanctions updates

### Performance Optimisation
1. **Batch Processing**: Use `UNWIND` for bulk imports
2. **Transaction Size**: Limit to 10,000 operations per transaction
3. **Index Usage**: Ensure queries utilise defined indices
4. **Relationship Properties**: Minimise properties on relationships for performance

### Compliance Requirements
1. **Audit Trail**: Maintain complete history of data changes
2. **Data Retention**: Follow regulatory requirements for data preservation
3. **Access Control**: Implement role-based access for sensitive data
4. **Data Sources**: Track provenance of all sanctions data

## Next Steps

1. **Implementation**: Develop Python Neo4j driver integration
2. **Testing**: Create comprehensive test suite for data integrity
3. **Monitoring**: Implement data quality dashboards
4. **Updates**: Automate periodic sanctions list updates
5. **Integration**: Connect with existing compliance systems

## References

- [Neo4j Transactional Data Model](https://neo4j.com/developer/industry-use-cases/data-models/transactions/transactions-base-model/)
- [UK Sanctions List](https://www.gov.uk/government/publications/the-uk-sanctions-list)
- [Neo4j Best Practices](https://neo4j.com/docs/cypher-manual/current/indexes-for-search-performance/)
- [Graph Data Modelling](https://neo4j.com/developer/data-modeling/)
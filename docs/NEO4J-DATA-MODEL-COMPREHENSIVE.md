# UK Sanctions List Neo4j Data Model - Comprehensive Reference

## Graph Overview

This data model represents sanctioned individuals and entities from UK sanctions lists as a knowledge graph, capturing complex relationships between people, organizations, locations, and sanctions regimes. The model follows Neo4j best practices using multi-labeled nodes, semantic relationships, and comprehensive metadata.

## Node Types and Properties

### Person
**Labels:** `Person`, `SanctionedIndividual`

Represents an individual person subject to UK sanctions. This is the core entity for sanctioned natural persons.

**Key Properties:**
- `sanctionId` (String, UNIQUE): Unique identifier for the sanctioned individual, typically in format "CYB####-#####"
- `ukSanctionsRef` (String): UK government reference number (e.g., "CYB0043")
- `fullName` (String): Complete name as listed in official sanctions documents, usually in uppercase
- `firstName` (String, optional): Given name parsed from the full name
- `middleName` (String, optional): Middle name(s) or patronymic
- `lastName` (String, optional): Surname/family name parsed from the full name
- `nameNonLatinScript` (String, optional): Name in native script (e.g., Cyrillic, Chinese characters)
- `dateOfBirth` (Date, optional): Birth date in Neo4j date format, converted from various input formats
- `placeOfBirth` (String, optional): Location of birth, may include city and country
- `gender` (String, optional): Gender if specified (typically "Male" or "Female")
- `position` (String, optional): Professional role, title, or position (e.g., "Programmer", "Director")
- `passportNumber` (String, optional): Passport identification number(s), may contain multiple
- `nationalIdentificationNumber` (String, optional): National ID number(s) from country of citizenship
- `listedOn` (Date, optional): Date when first added to sanctions list
- `dateDesignated` (Date, optional): Official designation date by sanctioning authority
- `lastUpdated` (Date, optional): Most recent modification date of the sanctions record
- `dateTrustServicesSanctionsImposed` (Date, optional): Specific date when trust services sanctions were applied
- `statementOfReasons` (String): Official justification for sanctions, describes the sanctionable activities
- `otherInformation` (String, optional): Additional details not captured in structured fields
- `groupId` (String, optional): Identifier linking related sanctioned parties

### Organisation
**Labels:** `Organisation`, `SanctionedEntity`

Represents a company, government entity, or other organization subject to sanctions.

**Key Properties:**
- `sanctionId` (String, UNIQUE): Unique identifier for the sanctioned entity, format "CYB####-#####"
- `ukSanctionsRef` (String): UK government reference number
- `organisationName` (String): Official name of the organization
- `nameNonLatinScript` (String, optional): Organization name in native script
- `entityType` (String, optional): Classification of entity (e.g., "BUSINESS", "GOVERNMENT", "STATE-OWNED")
- `typeOfEntity` (String, optional): Additional entity categorization
- `registrationNumber` (String, optional): Company registration or incorporation number
- `parentCompany` (String, optional): Name of parent organization if subsidiary
- `listedOn` (Date, optional): Date when first added to sanctions list
- `dateDesignated` (Date, optional): Official designation date
- `lastUpdated` (Date, optional): Most recent modification date
- `statementOfReasons` (String): Official justification for sanctions
- `otherInformation` (String, optional): Additional unstructured information
- `groupId` (String, optional): Links related entities in sanctions groups

### Address
**Labels:** `Address`

Represents a physical or postal address associated with sanctioned individuals or entities.

**Key Properties:**
- `addressId` (String, UNIQUE): Generated unique identifier for the address (format: "addr_" + UUID)
- `rawAddress` (String): Original address text as extracted from source document
- `addressLine1` (String, optional): Primary street address or building
- `addressLine2` (String, optional): Secondary address information (apartment, suite, floor)
- `postTown` (String, optional): City or town name
- `postCode` (String, optional): Postal/ZIP code
- `region` (String, optional): State, province, or administrative region
- `country` (String, optional): Country name (used for matching to Country nodes)

### Alias
**Labels:** `Alias`

Represents alternative names, nicknames, or trade names for sanctioned parties.

**Key Properties:**
- `aliasId` (String, UNIQUE): Normalized identifier for deduplication (lowercase, trimmed, alphanumeric only)
- `aliasName` (String): Original alias as it appears in sanctions documentation
- `aliasType` (String, optional): Classification of alias (e.g., "NICKNAME", "TRADENAME", "MAIDEN_NAME", "PREVIOUS_NAME")

**Normalization Rules for aliasId:**
1. Convert to lowercase
2. Trim whitespace
3. Collapse multiple spaces to single space
4. Remove special characters
5. Normalize Unicode (é→e, ñ→n)

### Country
**Labels:** `Country`

Represents sovereign nations referenced in sanctions data.

**Key Properties:**
- `name` (String, UNIQUE): Official country name in English (e.g., "Russia", "China", "United Kingdom")
- `code` (String, UNIQUE): ISO 3166-1 alpha-2 country code (e.g., "RU", "CN", "GB")

**Supported Countries (from Cypher queries):**
- Russia (RU), China (CN), Iran (IR), North Korea (KP)
- United Kingdom (GB), United States (US), Ukraine (UA)
- Belarus (BY), Kazakhstan (KZ), Kyrgyzstan (KG)
- Syria (SY), Myanmar (MM), Venezuela (VE), Bolivia (BO)
- Nicaragua (NI), Libya (LY), Mali (ML), Zimbabwe (ZW)
- Serbia (RS), Turkey (TR), Afghanistan (AF), Lebanon (LB)
- Iraq (IQ), Somalia (SO), Sudan (SD), Yemen (YE)
- Cuba (CU), Moldova (MD), Georgia (GE), Armenia (AM)
- Azerbaijan (AZ), Uzbekistan (UZ), Tajikistan (TJ), Turkmenistan (TM)

### SanctionsRegime
**Labels:** `SanctionsRegime`, `CyberSanctions` (or other specific regime type)

Represents the legal framework under which sanctions are imposed.

**Key Properties:**
- `regimeId` (String, UNIQUE): Unique identifier for the sanctions regime (e.g., "UK_CYBER_SANCTIONS")
- `regimeName` (String): Human-readable name (e.g., "UK Cyber Sanctions")
- `authority` (String): Issuing authority (e.g., "HM Treasury")
- `legalBasis` (String): Legal statute or regulation (e.g., "The Cyber (Sanctions) (EU Exit) Regulations 2020")
- `lastUpdated` (Date, optional): Most recent update to the regime

### SanctionsList
**Labels:** `SanctionsList`

Represents a specific published sanctions list document.

**Key Properties:**
- `listId` (String, UNIQUE): Unique identifier (e.g., "UK_CYBER_2024_01")
- `listName` (String): Full name of the list (e.g., "UK Cyber Sanctions List")
- `fileName` (String): Source file name (e.g., "cyber.pdf")
- `publicationDate` (Date, optional): Official publication date
- `extractionDate` (Date): Date when data was extracted from document
- `sourceUrl` (String, optional): Official URL where list was obtained
- `totalIndividuals` (Integer, optional): Count of individuals on this list
- `totalEntities` (Integer, optional): Count of entities on this list
- `authority` (String): Publishing authority (e.g., "HM Treasury")
- `version` (String, optional): Version number or identifier
- `hash` (String, optional): Document hash for integrity verification

## Relationship Types

### Identity and Biographical Relationships

#### HAS_ADDRESS
**Direction:** `(Person)-[:HAS_ADDRESS]->(Address)` or `(Organisation)-[:HAS_ADDRESS]->(Address)`

Links sanctioned parties to their known addresses.

**Properties:** None

#### HAS_NATIONALITY
**Direction:** `(Person)-[:HAS_NATIONALITY]->(Country)`

Indicates the nationality/citizenship of a sanctioned individual.

**Properties:** None

#### BORN_IN
**Direction:** `(Person)-[:BORN_IN]->(Country)`

Links a person to their country of birth (extracted from place of birth).

**Properties:** None

#### ALSO_KNOWN_AS
**Direction:** `(Person)-[:ALSO_KNOWN_AS]->(Alias)` or `(Organisation)-[:ALSO_KNOWN_AS]->(Alias)`

Connects sanctioned parties to their alternative names or aliases.

**Properties:** None

### Sanctions Administrative Relationships

#### SANCTIONED_UNDER
**Direction:** `(Person)-[:SANCTIONED_UNDER]->(SanctionsRegime)` or `(Organisation)-[:SANCTIONED_UNDER]->(SanctionsRegime)`

Links sanctioned parties to the legal framework under which they are sanctioned.

**Properties:**
- `listedOn` (Date, optional): Date when sanctions were first applied
- `statementOfReasons` (String): Specific justification for this party's sanctions
- `lastUpdated` (Date, optional): Most recent update to this sanctions relationship

#### LISTED_ON
**Direction:** `(Person)-[:LISTED_ON]->(SanctionsList)` or `(Organisation)-[:LISTED_ON]->(SanctionsList)`

Connects sanctioned parties to the specific list documents they appear on.

**Properties:**
- `addedDate` (Date, optional): Date when added to this specific list
- `pageNumber` (Integer, optional): Page number in source document
- `entryNumber` (Integer, optional): Entry sequence number on list
- `groupId` (String, optional): Links related entries on the same list

#### IMPLEMENTS
**Direction:** `(SanctionsList)-[:IMPLEMENTS]->(SanctionsRegime)`

Links a published list to the sanctions regime it implements.

**Properties:** None

### Corporate and Organizational Relationships

#### PARENT_OF
**Direction:** `(Organisation)-[:PARENT_OF]->(Organisation)`

Indicates parent-subsidiary relationships between organizations.

**Properties:** None

#### RELATED_TO
**Direction:** `(Organisation)-[:RELATED_TO]->(Organisation)`

Generic relationship between associated organizations.

**Properties:**
- `relationshipType` (String): Nature of relationship (e.g., "ASSOCIATED", "AFFILIATED", "CONTROLLED_BY")

### Geographic Relationships

#### LOCATED_IN
**Direction:** `(Address)-[:LOCATED_IN]->(Country)`

Links an address to its country location.

**Properties:** None

## Data Loading Patterns

### Loading Sequence

The Cypher queries follow a specific loading pattern:

1. **Primary Node Creation**: Create Person/Organisation nodes with core properties
2. **Regime Connection**: Immediately link to SanctionsRegime to ensure all parties are connected
3. **List Connection**: Link to SanctionsList and connect list to regime
4. **Country Relationships**: Create nationality and birth country relationships (non-blocking)
5. **Address Creation**: Separate queries create Address nodes and relationships
6. **Alias Creation**: Separate queries handle dynamic alias arrays

### Error Handling Patterns

- **Optional Properties**: Uses CASE statements to handle null values gracefully
- **Non-blocking Relationships**: Country relationships use FOREACH with conditional arrays to prevent failures
- **Country Validation**: Extensive CASE statements validate and normalize country names
- **Date Conversion**: Converts string dates to Neo4j date format with null handling

### Performance Considerations

- **MERGE Operations**: Prevent duplicate nodes while allowing updates
- **Indexed Properties**: sanctionId, ukSanctionsRef, aliasId should be indexed
- **Relationship Properties**: Minimized for performance, metadata stored on relationships only when necessary
- **Batch Processing**: UNWIND used for processing arrays of aliases and relationships

## Query Patterns

### Compliance Screening
```cypher
// Screen a name against all sanctioned individuals
MATCH (p:Person:SanctionedIndividual)
WHERE p.fullName CONTAINS $searchName
   OR p.lastName = $searchName
OPTIONAL MATCH (p)-[:ALSO_KNOWN_AS]->(a:Alias)
WHERE a.aliasName CONTAINS $searchName
RETURN DISTINCT p
```

### Geographic Risk Assessment
```cypher
// Find all sanctioned parties from high-risk countries
MATCH (p:Person)-[:HAS_NATIONALITY]->(c:Country)
WHERE c.code IN ['RU', 'CN', 'IR', 'KP']
RETURN c.name, count(p) as sanctionedIndividuals
```

### Corporate Network Analysis
```cypher
// Trace corporate relationships
MATCH path = (o1:Organisation)-[:PARENT_OF|RELATED_TO*1..3]-(o2:Organisation)
WHERE o1.sanctionId STARTS WITH 'CYB'
RETURN path
```

### Temporal Analysis
```cypher
// Track sanctions additions over time
MATCH (p:Person)-[r:LISTED_ON]->(list:SanctionsList)
WHERE r.addedDate >= date('2024-01-01')
RETURN date.truncate('month', r.addedDate) as month,
       count(p) as newSanctions
ORDER BY month
```

## Data Quality Constraints

### Unique Constraints
- Person.sanctionId
- Organisation.sanctionId
- Address.addressId
- Alias.aliasId
- Country.code
- Country.name
- SanctionsRegime.regimeId
- SanctionsList.listId

### Required Properties
- All nodes must have their primary identifier
- Person/Organisation must have sanctionId and ukSanctionsRef
- Address must have addressId and rawAddress
- Alias must have aliasId and aliasName
- Country must have both name and code
- SanctionsRegime must have regimeId
- SanctionsList must have listId

### Data Validation Rules
- Dates must be valid Neo4j date objects
- Country codes must be valid ISO 3166-1 alpha-2
- aliasId must be normalized according to rules
- Relationship directions must follow specified patterns
- groupId should link only related entries from same source

## Extension Points

The model is designed for extension:

1. **Additional Sanctions Regimes**: Add new regime-specific labels (e.g., `:TerrorismSanctions`, `:HumanRightsSanctions`)
2. **Document Types**: Extend beyond Passport/NationalId to other identity documents
3. **Enhanced Geographic Data**: Add City, Region nodes for more granular location tracking
4. **Temporal Versioning**: Add ValidFrom/ValidTo properties for historical tracking
5. **Risk Scoring**: Add computed risk properties based on relationship patterns
6. **Cross-List Matching**: Add relationships between same entities on different lists
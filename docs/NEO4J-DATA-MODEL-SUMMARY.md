# UK Sanctions Neo4j Data Model Summary

## Nodes

### Person (:Person:SanctionedIndividual)
- `sanctionId` (String, UNIQUE): Format "CYB####-#####"
- `ukSanctionsRef` (String): UK reference e.g., "CYB0043"
- `fullName`, `firstName`, `lastName`, `nameNonLatinScript`
- `dateOfBirth`, `placeOfBirth`, `gender`, `position`
- `passportNumber`, `nationalIdentificationNumber`
- `listedOn`, `dateDesignated`, `lastUpdated`
- `statementOfReasons`, `otherInformation`, `groupId`

### Organisation (:Organisation:SanctionedEntity)
- `sanctionId`, `ukSanctionsRef`, `organisationName`
- `nameNonLatinScript`, `entityType`, `typeOfEntity`
- `registrationNumber`, `parentCompany`
- `listedOn`, `dateDesignated`, `lastUpdated`
- `statementOfReasons`, `otherInformation`, `groupId`

### Address (:Address)
- `addressId` (String, UNIQUE): "addr_" + UUID
- `rawAddress`, `addressLine1`, `addressLine2`
- `postTown`, `postCode`, `region`, `country`

### Alias (:Alias)
- `aliasId` (String, UNIQUE): Normalized lowercase
- `aliasName`: Original form
- `aliasType`: NICKNAME, TRADENAME, etc.

### Country (:Country)
- `name` (String): "Russia", "China", etc.
- `code` (String): ISO alpha-2 "RU", "CN", etc.

### SanctionsRegime (:SanctionsRegime:CyberSanctions)
- `regimeId`: "UK_CYBER_SANCTIONS"
- `regimeName`, `authority`, `legalBasis`

### SanctionsList (:SanctionsList)
- `listId`: "UK_CYBER_2024_01"
- `listName`, `fileName`, `extractionDate`
- `authority`, `totalIndividuals`, `totalEntities`

## Relationships

- `(Person)-[:HAS_ADDRESS]->(Address)`
- `(Person)-[:HAS_NATIONALITY]->(Country)`
- `(Person)-[:BORN_IN]->(Country)`
- `(Person)-[:ALSO_KNOWN_AS]->(Alias)`
- `(Person)-[:SANCTIONED_UNDER {listedOn, statementOfReasons}]->(SanctionsRegime)`
- `(Person)-[:LISTED_ON {addedDate, groupId}]->(SanctionsList)`
- `(Organisation)-[:PARENT_OF]->(Organisation)`
- `(Organisation)-[:RELATED_TO {relationshipType}]->(Organisation)`
- `(Address)-[:LOCATED_IN]->(Country)`
- `(SanctionsList)-[:IMPLEMENTS]->(SanctionsRegime)`
// Cypher queries for loading sanctioned entities into Neo4j
// Based on the Neo4j data model for UK sanctions list

// Create Organisation node with SanctionedEntity label
MERGE (o:Organisation:SanctionedEntity {sanctionId: $sanctionId})
SET
    o.ukSanctionsRef = $ukSanctionsRef,
    o.organisationName = $organisationName,
    o.nameNonLatinScript = CASE WHEN $nameNonLatinScript IS NOT NULL THEN $nameNonLatinScript ELSE null END,
    o.entityType = CASE WHEN $entityType IS NOT NULL THEN $entityType ELSE null END,
    o.typeOfEntity = CASE WHEN $typeOfEntity IS NOT NULL THEN $typeOfEntity ELSE null END,
    o.registrationNumber = CASE WHEN $registrationNumber IS NOT NULL THEN $registrationNumber ELSE null END,
    o.parentCompany = CASE WHEN $parentCompany IS NOT NULL THEN $parentCompany ELSE null END,
    o.listedOn = CASE WHEN $listedOn IS NOT NULL THEN date($listedOn) ELSE null END,
    o.dateDesignated = CASE WHEN $dateDesignated IS NOT NULL THEN date($dateDesignated) ELSE null END,
    o.lastUpdated = CASE WHEN $lastUpdated IS NOT NULL THEN date($lastUpdated) ELSE null END,
    o.statementOfReasons = $statementOfReasons,
    o.otherInformation = CASE WHEN $otherInformation IS NOT NULL THEN $otherInformation ELSE null END,
    o.groupId = $groupId

// Create sanctions regime relationship
WITH o
MERGE (regime:SanctionsRegime:CyberSanctions {regimeId: 'UK_CYBER_SANCTIONS'})
ON CREATE SET
    regime.regimeName = 'UK Cyber Sanctions',
    regime.authority = 'HM Treasury',
    regime.legalBasis = 'The Cyber (Sanctions) (EU Exit) Regulations 2020'
MERGE (o)-[sanctioned:SANCTIONED_UNDER]->(regime)
SET
    sanctioned.listedOn = CASE WHEN $listedOn IS NOT NULL THEN date($listedOn) ELSE null END,
    sanctioned.statementOfReasons = $statementOfReasons,
    sanctioned.lastUpdated = CASE WHEN $lastUpdated IS NOT NULL THEN date($lastUpdated) ELSE null END

// Create sanctions list relationship
WITH o
MERGE (list:SanctionsList {listId: 'UK_CYBER_2024_01'})
ON CREATE SET
    list.listName = 'UK Cyber Sanctions List',
    list.fileName = 'cyber.pdf',
    list.extractionDate = date(),
    list.authority = 'HM Treasury'
MERGE (o)-[listed:LISTED_ON]->(list)
SET
    listed.addedDate = CASE WHEN $listedOn IS NOT NULL THEN date($listedOn) ELSE null END,
    listed.groupId = $groupId

// Connect list to regime
WITH o, list
MATCH (regime:SanctionsRegime {regimeId: 'UK_CYBER_SANCTIONS'})
MERGE (list)-[:IMPLEMENTS]->(regime)

// Create parent company relationship if specified
WITH o
WHERE $parentCompany IS NOT NULL
MERGE (parent:Organisation {organisationName: $parentCompany})
MERGE (parent)-[:PARENT_OF]->(o)

RETURN o.sanctionId as loaded_entity;
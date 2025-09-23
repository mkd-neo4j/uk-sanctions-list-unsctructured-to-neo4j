// Cypher queries for loading sanctioned individuals into Neo4j
// Based on the Neo4j data model for UK sanctions list

// Create Person node with SanctionedIndividual label
MERGE (p:Person:SanctionedIndividual {sanctionId: $sanctionId})
SET
    p.ukSanctionsRef = $ukSanctionsRef,
    p.fullName = $fullName,
    p.firstName = CASE WHEN $firstName IS NOT NULL THEN $firstName ELSE null END,
    p.middleName = CASE WHEN $middleName IS NOT NULL THEN $middleName ELSE null END,
    p.lastName = CASE WHEN $lastName IS NOT NULL THEN $lastName ELSE null END,
    p.nameNonLatinScript = CASE WHEN $nameNonLatinScript IS NOT NULL THEN $nameNonLatinScript ELSE null END,
    p.dateOfBirth = CASE WHEN $dateOfBirth IS NOT NULL THEN date($dateOfBirth) ELSE null END,
    p.placeOfBirth = CASE WHEN $placeOfBirth IS NOT NULL THEN $placeOfBirth ELSE null END,
    p.gender = CASE WHEN $gender IS NOT NULL THEN $gender ELSE null END,
    p.position = CASE WHEN $position IS NOT NULL THEN $position ELSE null END,
    p.passportNumber = CASE WHEN $passportNumber IS NOT NULL THEN $passportNumber ELSE null END,
    p.nationalIdentificationNumber = CASE WHEN $nationalIdentificationNumber IS NOT NULL THEN $nationalIdentificationNumber ELSE null END,
    p.listedOn = CASE WHEN $listedOn IS NOT NULL THEN date($listedOn) ELSE null END,
    p.dateDesignated = CASE WHEN $dateDesignated IS NOT NULL THEN date($dateDesignated) ELSE null END,
    p.lastUpdated = CASE WHEN $lastUpdated IS NOT NULL THEN date($lastUpdated) ELSE null END,
    p.dateTrustServicesSanctionsImposed = CASE WHEN $dateTrustServicesSanctionsImposed IS NOT NULL THEN date($dateTrustServicesSanctionsImposed) ELSE null END,
    p.statementOfReasons = $statementOfReasons,
    p.otherInformation = CASE WHEN $otherInformation IS NOT NULL THEN $otherInformation ELSE null END,
    p.groupId = $groupId

// Create nationality relationship if nationality exists
WITH p
WHERE $nationality IS NOT NULL
MERGE (country:Country {name: $nationality})
ON CREATE SET country.code = CASE
    WHEN toLower($nationality) = 'russia' THEN 'RU'
    WHEN toLower($nationality) = 'china' THEN 'CN'
    WHEN toLower($nationality) = 'iran' THEN 'IR'
    WHEN toLower($nationality) = 'north korea' THEN 'KP'
    WHEN toLower($nationality) IN ['united kingdom', 'uk'] THEN 'GB'
    WHEN toLower($nationality) IN ['united states', 'usa'] THEN 'US'
    WHEN toLower($nationality) = 'ukraine' THEN 'UA'
    WHEN toLower($nationality) = 'kyrgyzstan' THEN 'KG'
    WHEN toLower($nationality) = 'kazakhstan' THEN 'KZ'
    ELSE toLower($nationality)
END
MERGE (p)-[:HAS_NATIONALITY]->(country)

// Create place of birth relationship if available and different from nationality
WITH p
WHERE $placeOfBirth IS NOT NULL AND $placeOfBirth <> $nationality
MERGE (birthCountry:Country {name: $placeOfBirth})
ON CREATE SET birthCountry.code = CASE
    WHEN toLower($placeOfBirth) = 'russia' THEN 'RU'
    WHEN toLower($placeOfBirth) = 'china' THEN 'CN'
    WHEN toLower($placeOfBirth) = 'iran' THEN 'IR'
    WHEN toLower($placeOfBirth) = 'north korea' THEN 'KP'
    WHEN toLower($placeOfBirth) IN ['united kingdom', 'uk'] THEN 'GB'
    WHEN toLower($placeOfBirth) IN ['united states', 'usa'] THEN 'US'
    WHEN toLower($placeOfBirth) = 'ukraine' THEN 'UA'
    WHEN toLower($placeOfBirth) = 'kyrgyzstan' THEN 'KG'
    WHEN toLower($placeOfBirth) = 'kazakhstan' THEN 'KZ'
    ELSE toLower($placeOfBirth)
END
MERGE (p)-[:BORN_IN]->(birthCountry)

// Create sanctions regime relationship
WITH p
MERGE (regime:SanctionsRegime:CyberSanctions {regimeId: 'UK_CYBER_SANCTIONS'})
ON CREATE SET
    regime.regimeName = 'UK Cyber Sanctions',
    regime.authority = 'HM Treasury',
    regime.legalBasis = 'The Cyber (Sanctions) (EU Exit) Regulations 2020'
MERGE (p)-[sanctioned:SANCTIONED_UNDER]->(regime)
SET
    sanctioned.listedOn = CASE WHEN $listedOn IS NOT NULL THEN date($listedOn) ELSE null END,
    sanctioned.statementOfReasons = $statementOfReasons,
    sanctioned.lastUpdated = CASE WHEN $lastUpdated IS NOT NULL THEN date($lastUpdated) ELSE null END

// Create sanctions list relationship
WITH p
MERGE (list:SanctionsList {listId: 'UK_CYBER_2024_01'})
ON CREATE SET
    list.listName = 'UK Cyber Sanctions List',
    list.fileName = 'cyber.pdf',
    list.extractionDate = date(),
    list.authority = 'HM Treasury'
MERGE (p)-[listed:LISTED_ON]->(list)
SET
    listed.addedDate = CASE WHEN $listedOn IS NOT NULL THEN date($listedOn) ELSE null END,
    listed.groupId = $groupId

// Connect list to regime
WITH p, list
MATCH (regime:SanctionsRegime {regimeId: 'UK_CYBER_SANCTIONS'})
MERGE (list)-[:IMPLEMENTS]->(regime)

RETURN p.sanctionId as loaded_individual;
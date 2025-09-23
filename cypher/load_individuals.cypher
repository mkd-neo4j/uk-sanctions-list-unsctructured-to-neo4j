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

// CRITICAL: Create sanctions regime relationship IMMEDIATELY after person creation
// This ensures every Person gets connected to sanctions list regardless of nationality/birth place data
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

// Create nationality relationship if nationality exists and is a valid country
// Made non-blocking - execution continues even if nationality is invalid/missing
WITH p,
CASE WHEN $nationality IS NOT NULL THEN
    CASE toLower($nationality)
        WHEN 'russia' THEN {name: 'Russia', code: 'RU'}
        WHEN 'russian federation' THEN {name: 'Russia', code: 'RU'}
        WHEN 'china' THEN {name: 'China', code: 'CN'}
        WHEN "people's republic of china" THEN {name: 'China', code: 'CN'}
        WHEN 'iran' THEN {name: 'Iran', code: 'IR'}
        WHEN 'islamic republic of iran' THEN {name: 'Iran', code: 'IR'}
        WHEN 'north korea' THEN {name: 'North Korea', code: 'KP'}
        WHEN 'democratic people\'s republic of korea' THEN {name: 'North Korea', code: 'KP'}
        WHEN 'dprk' THEN {name: 'North Korea', code: 'KP'}
        WHEN 'united kingdom' THEN {name: 'United Kingdom', code: 'GB'}
        WHEN 'uk' THEN {name: 'United Kingdom', code: 'GB'}
        WHEN 'great britain' THEN {name: 'United Kingdom', code: 'GB'}
        WHEN 'britain' THEN {name: 'United Kingdom', code: 'GB'}
        WHEN 'united states' THEN {name: 'United States', code: 'US'}
        WHEN 'united states of america' THEN {name: 'United States', code: 'US'}
        WHEN 'usa' THEN {name: 'United States', code: 'US'}
        WHEN 'america' THEN {name: 'United States', code: 'US'}
        WHEN 'ukraine' THEN {name: 'Ukraine', code: 'UA'}
        WHEN 'kyrgyzstan' THEN {name: 'Kyrgyzstan', code: 'KG'}
        WHEN 'kyrgyz republic' THEN {name: 'Kyrgyzstan', code: 'KG'}
        WHEN 'kazakhstan' THEN {name: 'Kazakhstan', code: 'KZ'}
        WHEN 'republic of kazakhstan' THEN {name: 'Kazakhstan', code: 'KZ'}
        WHEN 'belarus' THEN {name: 'Belarus', code: 'BY'}
        WHEN 'republic of belarus' THEN {name: 'Belarus', code: 'BY'}
        WHEN 'syria' THEN {name: 'Syria', code: 'SY'}
        WHEN 'syrian arab republic' THEN {name: 'Syria', code: 'SY'}
        WHEN 'myanmar' THEN {name: 'Myanmar', code: 'MM'}
        WHEN 'burma' THEN {name: 'Myanmar', code: 'MM'}
        WHEN 'venezuela' THEN {name: 'Venezuela', code: 'VE'}
        WHEN 'bolivia' THEN {name: 'Bolivia', code: 'BO'}
        WHEN 'nicaragua' THEN {name: 'Nicaragua', code: 'NI'}
        WHEN 'libya' THEN {name: 'Libya', code: 'LY'}
        WHEN 'mali' THEN {name: 'Mali', code: 'ML'}
        WHEN 'zimbabwe' THEN {name: 'Zimbabwe', code: 'ZW'}
        WHEN 'serbia' THEN {name: 'Serbia', code: 'RS'}
        WHEN 'turkey' THEN {name: 'Turkey', code: 'TR'}
        WHEN 'turkiye' THEN {name: 'Turkey', code: 'TR'}
        WHEN 'afghanistan' THEN {name: 'Afghanistan', code: 'AF'}
        WHEN 'lebanon' THEN {name: 'Lebanon', code: 'LB'}
        WHEN 'iraq' THEN {name: 'Iraq', code: 'IQ'}
        WHEN 'somalia' THEN {name: 'Somalia', code: 'SO'}
        WHEN 'sudan' THEN {name: 'Sudan', code: 'SD'}
        WHEN 'yemen' THEN {name: 'Yemen', code: 'YE'}
        WHEN 'cuba' THEN {name: 'Cuba', code: 'CU'}
        WHEN 'moldova' THEN {name: 'Moldova', code: 'MD'}
        WHEN 'georgia' THEN {name: 'Georgia', code: 'GE'}
        WHEN 'armenia' THEN {name: 'Armenia', code: 'AM'}
        WHEN 'azerbaijan' THEN {name: 'Azerbaijan', code: 'AZ'}
        WHEN 'uzbekistan' THEN {name: 'Uzbekistan', code: 'UZ'}
        WHEN 'tajikistan' THEN {name: 'Tajikistan', code: 'TJ'}
        WHEN 'turkmenistan' THEN {name: 'Turkmenistan', code: 'TM'}
        ELSE null
    END
ELSE null
END as nationalityInfo
// Only create nationality relationship if we have valid country info
FOREACH (x IN CASE WHEN nationalityInfo IS NOT NULL THEN [1] ELSE [] END |
    MERGE (country:Country {name: nationalityInfo.name})
    ON CREATE SET country.code = nationalityInfo.code
    MERGE (p)-[:HAS_NATIONALITY]->(country)
)

// Create place of birth relationship if available and different from nationality
// Extract country from place of birth (e.g., "Perm Oblast, Russia" → "Russia")
// Made non-blocking - execution continues even if place of birth is invalid/missing
WITH p,
CASE WHEN $placeOfBirth IS NOT NULL AND $placeOfBirth <> $nationality THEN
    CASE
        // Extract country from comma-separated birth places
        WHEN $placeOfBirth CONTAINS ',' THEN
            CASE toLower(trim(split($placeOfBirth, ',')[-1]))
                WHEN 'russia' THEN {name: 'Russia', code: 'RU'}
                WHEN 'russian federation' THEN {name: 'Russia', code: 'RU'}
                WHEN 'china' THEN {name: 'China', code: 'CN'}
                WHEN "people's republic of china" THEN {name: 'China', code: 'CN'}
                WHEN 'iran' THEN {name: 'Iran', code: 'IR'}
                WHEN 'islamic republic of iran' THEN {name: 'Iran', code: 'IR'}
                WHEN 'north korea' THEN {name: 'North Korea', code: 'KP'}
                WHEN 'democratic people\'s republic of korea' THEN {name: 'North Korea', code: 'KP'}
                WHEN 'dprk' THEN {name: 'North Korea', code: 'KP'}
                WHEN 'united kingdom' THEN {name: 'United Kingdom', code: 'GB'}
                WHEN 'uk' THEN {name: 'United Kingdom', code: 'GB'}
                WHEN 'great britain' THEN {name: 'United Kingdom', code: 'GB'}
                WHEN 'britain' THEN {name: 'United Kingdom', code: 'GB'}
                WHEN 'united states' THEN {name: 'United States', code: 'US'}
                WHEN 'united states of america' THEN {name: 'United States', code: 'US'}
                WHEN 'usa' THEN {name: 'United States', code: 'US'}
                WHEN 'america' THEN {name: 'United States', code: 'US'}
                WHEN 'ukraine' THEN {name: 'Ukraine', code: 'UA'}
                WHEN 'kyrgyzstan' THEN {name: 'Kyrgyzstan', code: 'KG'}
                WHEN 'kyrgyz republic' THEN {name: 'Kyrgyzstan', code: 'KG'}
                WHEN 'kazakhstan' THEN {name: 'Kazakhstan', code: 'KZ'}
                WHEN 'republic of kazakhstan' THEN {name: 'Kazakhstan', code: 'KZ'}
                WHEN 'belarus' THEN {name: 'Belarus', code: 'BY'}
                WHEN 'republic of belarus' THEN {name: 'Belarus', code: 'BY'}
                WHEN 'syria' THEN {name: 'Syria', code: 'SY'}
                WHEN 'syrian arab republic' THEN {name: 'Syria', code: 'SY'}
                WHEN 'myanmar' THEN {name: 'Myanmar', code: 'MM'}
                WHEN 'burma' THEN {name: 'Myanmar', code: 'MM'}
                WHEN 'venezuela' THEN {name: 'Venezuela', code: 'VE'}
                WHEN 'bolivia' THEN {name: 'Bolivia', code: 'BO'}
                WHEN 'nicaragua' THEN {name: 'Nicaragua', code: 'NI'}
                WHEN 'libya' THEN {name: 'Libya', code: 'LY'}
                WHEN 'mali' THEN {name: 'Mali', code: 'ML'}
                WHEN 'zimbabwe' THEN {name: 'Zimbabwe', code: 'ZW'}
                WHEN 'serbia' THEN {name: 'Serbia', code: 'RS'}
                WHEN 'turkey' THEN {name: 'Turkey', code: 'TR'}
                WHEN 'turkiye' THEN {name: 'Turkey', code: 'TR'}
                WHEN 'afghanistan' THEN {name: 'Afghanistan', code: 'AF'}
                WHEN 'lebanon' THEN {name: 'Lebanon', code: 'LB'}
                WHEN 'iraq' THEN {name: 'Iraq', code: 'IQ'}
                WHEN 'somalia' THEN {name: 'Somalia', code: 'SO'}
                WHEN 'sudan' THEN {name: 'Sudan', code: 'SD'}
                WHEN 'yemen' THEN {name: 'Yemen', code: 'YE'}
                WHEN 'cuba' THEN {name: 'Cuba', code: 'CU'}
                WHEN 'moldova' THEN {name: 'Moldova', code: 'MD'}
                WHEN 'georgia' THEN {name: 'Georgia', code: 'GE'}
                WHEN 'armenia' THEN {name: 'Armenia', code: 'AM'}
                WHEN 'azerbaijan' THEN {name: 'Azerbaijan', code: 'AZ'}
                WHEN 'uzbekistan' THEN {name: 'Uzbekistan', code: 'UZ'}
                WHEN 'tajikistan' THEN {name: 'Tajikistan', code: 'TJ'}
                WHEN 'turkmenistan' THEN {name: 'Turkmenistan', code: 'TM'}
                ELSE null
            END
        // Handle direct country names without commas
        ELSE
            CASE toLower($placeOfBirth)
                WHEN 'russia' THEN {name: 'Russia', code: 'RU'}
                WHEN 'russian federation' THEN {name: 'Russia', code: 'RU'}
                WHEN 'china' THEN {name: 'China', code: 'CN'}
                WHEN "people's republic of china" THEN {name: 'China', code: 'CN'}
                WHEN 'iran' THEN {name: 'Iran', code: 'IR'}
                WHEN 'islamic republic of iran' THEN {name: 'Iran', code: 'IR'}
                WHEN 'north korea' THEN {name: 'North Korea', code: 'KP'}
                WHEN 'democratic people\'s republic of korea' THEN {name: 'North Korea', code: 'KP'}
                WHEN 'dprk' THEN {name: 'North Korea', code: 'KP'}
                WHEN 'united kingdom' THEN {name: 'United Kingdom', code: 'GB'}
                WHEN 'uk' THEN {name: 'United Kingdom', code: 'GB'}
                WHEN 'great britain' THEN {name: 'United Kingdom', code: 'GB'}
                WHEN 'britain' THEN {name: 'United Kingdom', code: 'GB'}
                WHEN 'united states' THEN {name: 'United States', code: 'US'}
                WHEN 'united states of america' THEN {name: 'United States', code: 'US'}
                WHEN 'usa' THEN {name: 'United States', code: 'US'}
                WHEN 'america' THEN {name: 'United States', code: 'US'}
                WHEN 'ukraine' THEN {name: 'Ukraine', code: 'UA'}
                WHEN 'kyrgyzstan' THEN {name: 'Kyrgyzstan', code: 'KG'}
                WHEN 'kyrgyz republic' THEN {name: 'Kyrgyzstan', code: 'KG'}
                WHEN 'kazakhstan' THEN {name: 'Kazakhstan', code: 'KZ'}
                WHEN 'republic of kazakhstan' THEN {name: 'Kazakhstan', code: 'KZ'}
                WHEN 'belarus' THEN {name: 'Belarus', code: 'BY'}
                WHEN 'republic of belarus' THEN {name: 'Belarus', code: 'BY'}
                WHEN 'syria' THEN {name: 'Syria', code: 'SY'}
                WHEN 'syrian arab republic' THEN {name: 'Syria', code: 'SY'}
                WHEN 'myanmar' THEN {name: 'Myanmar', code: 'MM'}
                WHEN 'burma' THEN {name: 'Myanmar', code: 'MM'}
                WHEN 'venezuela' THEN {name: 'Venezuela', code: 'VE'}
                WHEN 'bolivia' THEN {name: 'Bolivia', code: 'BO'}
                WHEN 'nicaragua' THEN {name: 'Nicaragua', code: 'NI'}
                WHEN 'libya' THEN {name: 'Libya', code: 'LY'}
                WHEN 'mali' THEN {name: 'Mali', code: 'ML'}
                WHEN 'zimbabwe' THEN {name: 'Zimbabwe', code: 'ZW'}
                WHEN 'serbia' THEN {name: 'Serbia', code: 'RS'}
                WHEN 'turkey' THEN {name: 'Turkey', code: 'TR'}
                WHEN 'turkiye' THEN {name: 'Turkey', code: 'TR'}
                WHEN 'afghanistan' THEN {name: 'Afghanistan', code: 'AF'}
                WHEN 'lebanon' THEN {name: 'Lebanon', code: 'LB'}
                WHEN 'iraq' THEN {name: 'Iraq', code: 'IQ'}
                WHEN 'somalia' THEN {name: 'Somalia', code: 'SO'}
                WHEN 'sudan' THEN {name: 'Sudan', code: 'SD'}
                WHEN 'yemen' THEN {name: 'Yemen', code: 'YE'}
                WHEN 'cuba' THEN {name: 'Cuba', code: 'CU'}
                WHEN 'moldova' THEN {name: 'Moldova', code: 'MD'}
                WHEN 'georgia' THEN {name: 'Georgia', code: 'GE'}
                WHEN 'armenia' THEN {name: 'Armenia', code: 'AM'}
                WHEN 'azerbaijan' THEN {name: 'Azerbaijan', code: 'AZ'}
                WHEN 'uzbekistan' THEN {name: 'Uzbekistan', code: 'UZ'}
                WHEN 'tajikistan' THEN {name: 'Tajikistan', code: 'TJ'}
                WHEN 'turkmenistan' THEN {name: 'Turkmenistan', code: 'TM'}
                ELSE null
            END
    END
ELSE null
END as birthCountryInfo
// Only create place of birth relationship if we have valid country info
FOREACH (x IN CASE WHEN birthCountryInfo IS NOT NULL THEN [1] ELSE [] END |
    MERGE (birthCountry:Country {name: birthCountryInfo.name})
    ON CREATE SET birthCountry.code = birthCountryInfo.code
    MERGE (p)-[:BORN_IN]->(birthCountry)
)

RETURN p.sanctionId as loaded_individual;
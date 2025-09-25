// Cypher query for loading individual addresses into Neo4j
// This is a separate query to handle address creation and relationships

// Find the person by sanctionId and merge address based on addressId
MATCH (p:Person:SanctionedIndividual {sanctionId: $sanctionId})
WITH p
// Use MERGE with the deterministic addressId to avoid duplicates
MERGE (address:Address {addressId: $address.addressId})
ON CREATE SET
    address.rawAddress = $address.rawAddress,
    address.addressLine1 = CASE WHEN $address.addressLine1 IS NOT NULL THEN $address.addressLine1 ELSE null END,
    address.addressLine2 = CASE WHEN $address.addressLine2 IS NOT NULL THEN $address.addressLine2 ELSE null END,
    address.postTown = CASE WHEN $address.postTown IS NOT NULL THEN $address.postTown ELSE null END,
    address.postCode = CASE WHEN $address.postCode IS NOT NULL THEN $address.postCode ELSE null END,
    address.region = CASE WHEN $address.region IS NOT NULL THEN $address.region ELSE null END,
    address.country = CASE WHEN $address.country IS NOT NULL THEN $address.country ELSE null END
// Update fields if the address already exists (in case data has been corrected/updated)
ON MATCH SET
    address.rawAddress = COALESCE($address.rawAddress, address.rawAddress),
    address.addressLine1 = CASE WHEN $address.addressLine1 IS NOT NULL THEN $address.addressLine1 ELSE address.addressLine1 END,
    address.addressLine2 = CASE WHEN $address.addressLine2 IS NOT NULL THEN $address.addressLine2 ELSE address.addressLine2 END,
    address.postTown = CASE WHEN $address.postTown IS NOT NULL THEN $address.postTown ELSE address.postTown END,
    address.postCode = CASE WHEN $address.postCode IS NOT NULL THEN $address.postCode ELSE address.postCode END,
    address.region = CASE WHEN $address.region IS NOT NULL THEN $address.region ELSE address.region END,
    address.country = CASE WHEN $address.country IS NOT NULL THEN $address.country ELSE address.country END

// Create relationship to person
MERGE (p)-[:HAS_ADDRESS]->(address)

// Create relationship to country if country is specified and valid
WITH address
WHERE $address.country IS NOT NULL
// Only create Country nodes for validated country names (prevents regions/cities from becoming countries)
WITH address,
CASE toLower($address.country)
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
END as countryInfo
WHERE countryInfo IS NOT NULL
MERGE (country:Country {name: countryInfo.name})
ON CREATE SET country.code = countryInfo.code
MERGE (address)-[:LOCATED_IN]->(country)

RETURN address.addressId as address_created;
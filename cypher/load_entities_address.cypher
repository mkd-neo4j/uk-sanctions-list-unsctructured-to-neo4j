// Cypher query for loading entity addresses into Neo4j
// This is a separate query to handle address creation and relationships

// Find the organisation by sanctionId and create address relationship
MATCH (o:Organisation:SanctionedEntity {sanctionId: $sanctionId})
WITH o
CREATE (address:Address {
    addressId: $address.addressId,
    rawAddress: $address.rawAddress
})
SET
    address.addressLine1 = CASE WHEN $address.addressLine1 IS NOT NULL THEN $address.addressLine1 ELSE null END,
    address.addressLine2 = CASE WHEN $address.addressLine2 IS NOT NULL THEN $address.addressLine2 ELSE null END,
    address.postTown = CASE WHEN $address.postTown IS NOT NULL THEN $address.postTown ELSE null END,
    address.postCode = CASE WHEN $address.postCode IS NOT NULL THEN $address.postCode ELSE null END,
    address.region = CASE WHEN $address.region IS NOT NULL THEN $address.region ELSE null END,
    address.country = CASE WHEN $address.country IS NOT NULL THEN $address.country ELSE null END

// Create relationship to organisation
MERGE (o)-[:HAS_ADDRESS]->(address)

// Create relationship to country if country is specified
WITH address
WHERE $address.country IS NOT NULL
MERGE (country:Country {name: $address.country})
ON CREATE SET country.code = CASE
    WHEN toLower($address.country) = 'russia' THEN 'RU'
    WHEN toLower($address.country) = 'china' THEN 'CN'
    WHEN toLower($address.country) = 'iran' THEN 'IR'
    WHEN toLower($address.country) = 'north korea' THEN 'KP'
    WHEN toLower($address.country) IN ['united kingdom', 'uk'] THEN 'GB'
    WHEN toLower($address.country) IN ['united states', 'usa'] THEN 'US'
    WHEN toLower($address.country) = 'ukraine' THEN 'UA'
    WHEN toLower($address.country) = 'kyrgyzstan' THEN 'KG'
    WHEN toLower($address.country) = 'kazakhstan' THEN 'KZ'
    ELSE toLower($address.country)
END
MERGE (address)-[:LOCATED_IN]->(country)

RETURN address.addressId as address_created;
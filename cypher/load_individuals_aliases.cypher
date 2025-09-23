// Cypher query for loading individual aliases into Neo4j
// This is a separate query to handle the dynamic nature of aliases

// Find the person by sanctionId and create alias relationships
MATCH (p:Person:SanctionedIndividual {sanctionId: $sanctionId})
WITH p
UNWIND $aliases as aliasData
MERGE (alias:Alias {aliasId: aliasData.aliasId})
ON CREATE SET
    alias.aliasName = aliasData.aliasName,
    alias.aliasType = aliasData.aliasType
MERGE (p)-[:ALSO_KNOWN_AS]->(alias)

RETURN p.sanctionId as person_id, count(alias) as aliases_created;
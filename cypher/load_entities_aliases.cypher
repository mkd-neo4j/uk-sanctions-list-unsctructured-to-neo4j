// Cypher query for loading entity aliases into Neo4j
// This is a separate query to handle the dynamic nature of entity aliases

// Find the organisation by sanctionId and create alias relationships
MATCH (o:Organisation:SanctionedEntity {sanctionId: $sanctionId})
WITH o
UNWIND $aliases as aliasData
MERGE (alias:Alias {aliasId: aliasData.aliasId})
ON CREATE SET
    alias.aliasName = aliasData.aliasName,
    alias.aliasType = aliasData.aliasType
MERGE (o)-[:ALSO_KNOWN_AS]->(alias)

RETURN o.sanctionId as entity_id, count(alias) as aliases_created;
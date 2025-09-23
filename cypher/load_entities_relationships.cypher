// Cypher query for loading entity relationships into Neo4j
// This handles subsidiary, related entities, and other organizational relationships

// Find the organisation by sanctionId
MATCH (o:Organisation:SanctionedEntity {sanctionId: $sanctionId})

// Create subsidiary relationships
WITH o
UNWIND CASE WHEN $subsidiaries IS NOT NULL AND size($subsidiaries) > 0 THEN $subsidiaries ELSE [] END as subsidiary
MERGE (sub:Organisation {organisationName: subsidiary})
MERGE (o)-[:PARENT_OF]->(sub)

// Create related entity relationships
WITH o
UNWIND CASE WHEN $relatedEntities IS NOT NULL AND size($relatedEntities) > 0 THEN $relatedEntities ELSE [] END as relatedEntity
MERGE (related:Organisation {organisationName: relatedEntity})
MERGE (o)-[:RELATED_TO {relationshipType: 'ASSOCIATED'}]->(related)

RETURN o.sanctionId as entity_id,
       size(CASE WHEN $subsidiaries IS NOT NULL THEN $subsidiaries ELSE [] END) as subsidiaries_created,
       size(CASE WHEN $relatedEntities IS NOT NULL THEN $relatedEntities ELSE [] END) as related_entities_created;
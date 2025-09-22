"""
Pydantic model for sanctioned entities (organizations).
Follows Neo4j naming conventions with camelCase properties.
"""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field

from .address import Address


class SanctionedEntity(BaseModel):
    """
    Model for a sanctioned entity/organization entry from UK sanctions list.
    Property names follow Neo4j camelCase conventions.
    """

    # Core identification fields
    sanctionId: str = Field(..., description="Unique identifier for this sanction record")
    ukSanctionsRef: str = Field(..., description="UK Sanctions List Reference (e.g., CYB0097)")

    # Organization details
    organizationName: str = Field(..., description="Primary name of the organization")
    nameNonLatinScript: Optional[str] = Field(None, description="Organization name in non-Latin script if available")

    # Aliases
    aliases: List[str] = Field(default_factory=list, description="Also known as (AKA) names")

    # Organization type/classification
    entityType: Optional[str] = Field(None, description="Type of entity (e.g., BUSINESS, GOVERNMENT, MILITARY)")
    typeOfEntity: Optional[str] = Field(None, description="Type of entity as specified in sanctions document")

    # Address information
    address: Optional[Address] = Field(None, description="Structured address information")

    # Registration details
    registrationNumber: Optional[str] = Field(None, description="Registration or identification number")

    # Parent/subsidiary relationships
    parentCompany: Optional[str] = Field(None, description="Parent company name")
    subsidiaries: List[str] = Field(default_factory=list, description="List of subsidiary organizations")

    # Metadata
    groupId: str = Field(..., description="Group ID from sanctions list")
    listedOn: str = Field(..., description="Date listed on sanctions")
    dateDesignated: str = Field(..., description="UK Sanctions List Date Designated")
    lastUpdated: str = Field(..., description="Last updated date")

    # Sanctions details
    statementOfReasons: str = Field(..., description="UK Statement of Reasons for sanctions")
    otherInformation: Optional[str] = Field(None, description="Additional information")

    # Related entities
    relatedEntities: List[str] = Field(default_factory=list, description="Related organizations or units")

    class Config:
        json_schema_extra = {
            "example": {
                "sanctionId": "CYB0044-16460",
                "ukSanctionsRef": "CYB0044",
                "organizationName": "WUHAN XIAORUIZHI SCIENCE AND TECHNOLOGY COMPANY LIMITED",
                "nameNonLatinScript": "武汉晓睿智科技有限责任公司",
                "aliases": [],
                "entityType": "BUSINESS",
                "typeOfEntity": "Company",
                "address": {
                    "rawAddress": "2nd Floor, No. 16, Huashiyuan North Road, East Lake New Technology Development Zone, Hubei Province, Wuhan, China",
                    "addressLine1": "No. 16, Huashiyuan North Road",
                    "addressLine2": "2nd Floor",
                    "postTown": "Wuhan",
                    "region": "East Lake New Technology Development Zone, Hubei Province",
                    "country": "China"
                },
                "groupId": "16460",
                "listedOn": "25/03/2024",
                "dateDesignated": "25/03/2024",
                "lastUpdated": "25/03/2024",
                "statementOfReasons": "WUHAN XIAORUIZHI SCIENCE AND TECHNOLOGY COMPANY LIMITED is associated with Advanced Persistent Threat Group 31 (APT31)...",
                "otherInformation": "(UK Sanctions List Ref):CYB0044...",
                "parentCompany": None,
                "subsidiaries": [],
                "relatedEntities": ["Advanced Persistent Threat Group 31 (APT31)", "Chinese Ministry of State Security (MSS)"]
            }
        }


class EntitiesList(BaseModel):
    """Container for multiple sanctioned entities."""
    entities: List[SanctionedEntity] = Field(..., description="List of sanctioned entities")
    totalCount: int = Field(..., description="Total number of entities extracted")
    extractionDate: str = Field(..., description="Date when extraction was performed")
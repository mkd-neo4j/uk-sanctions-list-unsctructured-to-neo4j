"""
Pydantic model for structured addresses.
Follows Neo4j transactional data model conventions while preserving raw address data.
"""

from typing import Optional
from pydantic import BaseModel, Field


class Address(BaseModel):
    """
    Structured address model following Neo4j transactional data model patterns.
    Preserves raw address string while providing structured components for graph relationships.
    """

    # Raw address preservation - always maintain original data
    rawAddress: str = Field(..., description="Original address string as it appears in document")

    # Neo4j structured address fields
    addressLine1: Optional[str] = Field(None, description="Primary address line with house/building number and street name")
    addressLine2: Optional[str] = Field(None, description="Secondary address details like room number, floor, or building name")
    postTown: Optional[str] = Field(None, description="City or town name")
    postCode: Optional[str] = Field(None, description="Postal code or zip code")
    region: Optional[str] = Field(None, description="State, province, county, or administrative region")
    country: Optional[str] = Field(None, description="Country name")

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "rawAddress": "Room 1102, Guanfu Mansion, 46 Xinkai Road, Hedong District, Tianjin, China",
                    "addressLine1": "46 Xinkai Road",
                    "addressLine2": "Room 1102, Guanfu Mansion",
                    "postTown": "Tianjin",
                    "region": "Hedong District",
                    "country": "China"
                },
                {
                    "rawAddress": "16a Nagatinskaya Street, Moscow, Russia",
                    "addressLine1": "16a Nagatinskaya Street",
                    "postTown": "Moscow",
                    "country": "Russia"
                },
                {
                    "rawAddress": "Moscow, Russia",
                    "postTown": "Moscow",
                    "country": "Russia"
                },
                {
                    "rawAddress": "Hubei Province, China",
                    "region": "Hubei Province",
                    "country": "China"
                }
            ]
        }
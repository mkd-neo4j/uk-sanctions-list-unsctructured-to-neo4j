"""
Pydantic model for sanctioned individuals.
Follows Neo4j naming conventions with camelCase properties.
"""

from typing import Optional, List
from datetime import date, datetime
from pydantic import BaseModel, Field

from .address import Address


class SanctionedIndividual(BaseModel):
    """
    Model for a sanctioned individual entry from UK sanctions list.
    Property names follow Neo4j camelCase conventions.
    """

    # Core identification fields
    sanctionId: str = Field(..., description="Unique identifier for this sanction record")
    ukSanctionsRef: str = Field(..., description="UK Sanctions List Reference (e.g., CYB0071)")

    # Name components - using numbered format from source
    name1: Optional[str] = Field(None, description="First name")
    name2: Optional[str] = Field(None, description="Middle name or second name")
    name3: Optional[str] = Field(None, description="Additional name")
    name4: Optional[str] = Field(None, description="Additional name")
    name5: Optional[str] = Field(None, description="Additional name")
    name6: Optional[str] = Field(None, description="Last name or surname")

    # Parsed name fields for easier use
    firstName: Optional[str] = Field(None, description="Primary first name")
    middleName: Optional[str] = Field(None, description="Middle name")
    lastName: Optional[str] = Field(None, description="Primary last name")
    fullName: str = Field(..., description="Complete name as it appears in the document")

    # Birth information
    dateOfBirth: Optional[str] = Field(None, description="Date of birth (various formats)")
    placeOfBirth: Optional[str] = Field(None, description="Place of birth")

    # Identification
    nationality: Optional[str] = Field(None, description="Nationality")
    passportNumber: Optional[str] = Field(None, description="Passport number")
    nationalIdentificationNumber: Optional[str] = Field(None, description="National ID number (for non-Western individuals)")
    gender: Optional[str] = Field(None, description="Gender")

    # Aliases
    aliases: List[str] = Field(default_factory=list, description="Also known as (AKA) names")

    # Address information
    address: Optional[Address] = Field(None, description="Structured address information")

    # Professional information
    position: Optional[str] = Field(None, description="Position or role")

    # Metadata
    groupId: str = Field(..., description="Group ID from sanctions list")
    listedOn: str = Field(..., description="Date listed on sanctions")
    dateDesignated: str = Field(..., description="UK Sanctions List Date Designated")
    lastUpdated: str = Field(..., description="Last updated date")
    dateTrustServicesSanctionsImposed: Optional[str] = Field(None, description="Date trust services sanctions imposed (if applicable)")

    # Sanctions details
    statementOfReasons: str = Field(..., description="UK Statement of Reasons for sanctions")
    otherInformation: Optional[str] = Field(None, description="Additional information")

    # Optional non-Latin script name
    nameNonLatinScript: Optional[str] = Field(None, description="Name in non-Latin script if available")

    class Config:
        json_schema_extra = {
            "example": {
                "sanctionId": "CYB0043-16345",
                "ukSanctionsRef": "CYB0043",
                "name1": "ALEKSANDR",
                "name2": "GENNADIEVICH",
                "name6": "ERMAKOV",
                "firstName": "Aleksandr",
                "middleName": "Gennadievich",
                "lastName": "Ermakov",
                "fullName": "ERMAKOV ALEKSANDR GENNADIEVICH",
                "nameNonLatinScript": "Александр Геннадьевич Ермаков",
                "dateOfBirth": "16/05/1990",
                "placeOfBirth": "Russia",
                "nationality": "Russia",
                "gender": "Male",
                "address": {
                    "rawAddress": "Moscow, Russia",
                    "postTown": "Moscow",
                    "country": "Russia"
                },
                "aliases": ["BLADE_RUNNER", "ERMAKOV, Aleksandr, Gennadyevich (non-Latin script: Александр Геннадьевич Ермаков)", "GISTAVEDORE", "GUSTAVEDORE", "JIMJONES"],
                "groupId": "16345",
                "listedOn": "23/01/2024",
                "dateDesignated": "23/01/2024",
                "lastUpdated": "23/01/2024",
                "statementOfReasons": "Aleksandr ERMAKOV is or has been involved in relevant cyber activity, including being responsible for, engaging in, providing support for, malicious cyber activity..."
            }
        }


class IndividualsList(BaseModel):
    """Container for multiple sanctioned individuals."""
    individuals: List[SanctionedIndividual] = Field(..., description="List of sanctioned individuals")
    totalCount: int = Field(..., description="Total number of individuals extracted")
    extractionDate: str = Field(..., description="Date when extraction was performed")
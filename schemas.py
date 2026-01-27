from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field

class ResearchDomain(str, Enum):
    PROGRAMMATIC_PATTERN_DESIGN = "Programmatic Pattern Design & Garment-Code"
    PHYSICS_BASED_MODELING = "Physics-Based Modeling"
    COLLISION_HANDLING = "Collision Handling"
    AI_DATA_DRIVEN_METHODS = "AI & Data-Driven Methods"
    REAL_TIME_VS_HIGH_FIDELITY = "Real-Time vs. High-Fidelity"
    MATERIAL_REALISM = "Material Realism"
    OTHER = "Other"

class ResearchItem(BaseModel):
    title: str = Field(..., description="The title of the paper, codebase, or article.")
    source_link: str = Field(..., description="URL or citation for the source.")
    publication_date: str = Field(..., description="Date of publication or release (YYYY-MM-DD). Must be within the last 1 month.")
    primary_domain: ResearchDomain = Field(..., description="The primary research domain this item belongs to.")
    relevance_explanation: str = Field(..., description="Explanation of why this item is relevant to the domain.")
    key_innovation: str = Field(..., description="The specific problem solved or the key innovation introduced.")
    summary: str = Field(..., description="A concise summary of the item's content.")

class WeeklyResearchDigest(BaseModel):
    topic: str = Field(..., description="The main research topic (e.g., Garment Simulation).")
    report_date: str = Field(..., description="Date of this report generation.")
    items: List[ResearchItem] = Field(..., description="List of max 10 curated research items, ordered by relevance.")

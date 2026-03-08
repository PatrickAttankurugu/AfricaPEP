"""Pydantic request/response models for the API.

Response format follows industry standards (OpenSanctions, ComplyAdvantage,
Dow Jones patterns) for PEP/sanctions screening APIs.
"""
from typing import Optional

from pydantic import BaseModel, Field, field_validator


# ── Request models ──

class ScreeningRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=200, description="Name to screen")
    country: Optional[str] = Field(None, min_length=2, max_length=2, description="ISO 3166-1 alpha-2 country code")
    threshold: float = Field(0.75, ge=0.0, le=1.0, description="Minimum match score (0.0-1.0)")

    model_config = {"json_schema_extra": {
        "examples": [{"name": "Kwame Mensah", "country": "GH", "threshold": 0.75}]
    }}


class SearchParams(BaseModel):
    q: str = Field(..., min_length=1, description="Search query")
    country: Optional[str] = Field(None, min_length=2, max_length=2)
    tier: Optional[int] = Field(None, ge=1, le=3)
    active: Optional[bool] = None
    page: int = Field(1, ge=1)
    limit: int = Field(20, ge=1, le=100)


# ── Response models ──

class PositionResponse(BaseModel):
    title: str
    institution: str = ""
    country: str = ""
    branch: str = ""
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    is_current: bool = True


class SourceResponse(BaseModel):
    source_url: str = ""
    source_type: str = ""
    country: str = ""
    scraped_at: Optional[str] = None


class MatchExplanation(BaseModel):
    """Explains why a match was returned — which scoring components contributed."""
    name_similarity: float = Field(description="Token-sort ratio between query and matched name (0.0-1.0)")
    best_variant_score: float = Field(description="Highest score across all name variants (0.0-1.0)")
    method: str = Field(default="rapidfuzz_token_sort", description="Scoring algorithm used")
    matched_variant: Optional[str] = Field(None, description="Name variant that produced the best score, if different from primary name")


class MatchResult(BaseModel):
    pep_id: str = Field(description="Unique entity identifier")
    matched_name: str = Field(description="Primary name of the matched PEP")
    match_score: float = Field(description="Overall match score (0.0-1.0)")
    match: bool = Field(description="Whether this result meets the screening threshold")
    pep_tier: int = Field(description="FATF risk tier (1=highest, 2=elevated, 3=standard)")
    risk_level: str = Field(description="Human-readable risk level: high, elevated, or standard")
    is_active: bool = Field(description="Whether the person currently holds a PEP position")
    nationality: str = Field(default="", description="ISO 3166-1 alpha-2 country code")
    date_of_birth: Optional[str] = Field(None, description="Date of birth (YYYY-MM-DD) if known")
    aliases: list[str] = Field(default=[], description="Known name variants and aliases")
    positions: list[PositionResponse] = Field(default=[], description="Political positions held")
    sources: list[SourceResponse] = Field(default=[], description="Data sources for this record")
    datasets: list[str] = Field(default=["africapep-wikidata"], description="Datasets this entity appears in")
    first_seen: Optional[str] = Field(None, description="When this entity was first ingested (ISO 8601)")
    last_seen: Optional[str] = Field(None, description="When this entity was last confirmed (ISO 8601)")
    explanation: Optional[MatchExplanation] = Field(None, description="Scoring breakdown explaining the match")


class ScreeningResponse(BaseModel):
    query: str = Field(description="The name that was screened")
    threshold: float = Field(description="Match threshold used for this screening")
    total_matches: int = Field(description="Number of matches found")
    matches: list[MatchResult] = Field(description="Matched PEP entities, sorted by score descending")
    screening_id: str = Field(description="Unique ID for this screening (for audit trail)")
    screened_at: str = Field(description="Timestamp of the screening (ISO 8601)")


class PepProfileResponse(BaseModel):
    id: str
    full_name: str
    aliases: list[str] = []
    date_of_birth: Optional[str] = None
    nationality: str = ""
    gender: str = ""
    pep_tier: int
    risk_level: str = ""
    is_active_pep: bool = True
    positions: list[PositionResponse] = []
    sources: list[SourceResponse] = []
    datasets: list[str] = ["africapep-wikidata"]
    first_seen: Optional[str] = None
    last_seen: Optional[str] = None


class GraphNode(BaseModel):
    id: str
    label: str
    type: str
    properties: dict = {}


class GraphEdge(BaseModel):
    source: str
    target: str
    type: str
    properties: dict = {}


class GraphResponse(BaseModel):
    nodes: list[GraphNode]
    edges: list[GraphEdge]


class SearchResultItem(BaseModel):
    id: str
    full_name: str
    pep_tier: int
    risk_level: str = ""
    is_active: bool
    nationality: str = ""
    positions: list[PositionResponse] = []


class SearchResponse(BaseModel):
    query: str
    total: int
    page: int
    limit: int
    results: list[SearchResultItem]


class StatsResponse(BaseModel):
    total_peps: int = 0
    by_country: dict[str, int] = {}
    by_tier: dict[str, int] = {}
    last_updated: Optional[str] = None
    sources_count: int = 0
    active_peps: int = 0


class HealthResponse(BaseModel):
    status: str
    neo4j: str
    postgres: str
    version: str = "1.0.0"


class ErrorResponse(BaseModel):
    detail: str
    code: str


# ── Batch screening models ──

class BatchNameEntry(BaseModel):
    name: str = Field(..., min_length=2, max_length=200, description="Name to screen")
    country: Optional[str] = Field(None, min_length=2, max_length=2, description="ISO 3166-1 alpha-2 country code")


class BatchScreeningRequest(BaseModel):
    names: list[BatchNameEntry] = Field(..., min_length=1, max_length=50, description="List of names to screen (max 50)")
    threshold: float = Field(0.65, ge=0.0, le=1.0, description="Minimum match score")

    @field_validator("names")
    @classmethod
    def validate_names_count(cls, v):
        if len(v) > 50:
            raise ValueError("Maximum 50 names per batch request")
        return v


class BatchScreeningResultItem(BaseModel):
    query_name: str = Field(description="The name that was screened")
    match_count: int = Field(description="Number of matches found")
    matches: list[MatchResult] = Field(description="Matched PEP entities")


class BatchScreeningResponse(BaseModel):
    results: list[BatchScreeningResultItem]
    total_queries: int
    total_matches: int
    screening_id: str = Field(description="Unique ID for this batch screening")
    screened_at: str = Field(description="Timestamp of the screening (ISO 8601)")
    threshold: float = Field(description="Match threshold used")


# ── Country coverage models ──

class CountryInfo(BaseModel):
    code: str = Field(description="ISO 3166-1 alpha-2 country code")
    name: str = Field(description="Country name")
    region: str = Field(description="African region")
    pep_count: int = Field(description="Number of PEP profiles")


class CountriesResponse(BaseModel):
    total_countries: int
    countries: list[CountryInfo]


# ── Utility ──

def tier_to_risk_level(tier: int) -> str:
    """Convert FATF tier number to human-readable risk level."""
    return {1: "high", 2: "elevated", 3: "standard"}.get(tier, "unknown")

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

    model_config = {"json_schema_extra": {"examples": [{
        "query": "Kwame Mensah",
        "threshold": 0.75,
        "total_matches": 1,
        "matches": [{
            "pep_id": "PEP-GH-00123",
            "matched_name": "Kwame Mensah",
            "match_score": 0.92,
            "match": True,
            "pep_tier": 1,
            "risk_level": "high",
            "is_active": True,
            "nationality": "GH",
            "date_of_birth": "1965-03-15",
            "aliases": ["K. Mensah"],
            "positions": [{"title": "Minister of Finance", "institution": "Government of Ghana", "country": "GH", "branch": "EXECUTIVE", "start_date": "2021-01-01", "end_date": None, "is_current": True}],
            "sources": [{"source_url": "https://wikidata.org/wiki/Q12345", "source_type": "WIKIDATA", "country": "GH", "scraped_at": "2025-01-15T10:30:00Z"}],
            "datasets": ["africapep-wikidata"],
            "first_seen": "2024-06-01T00:00:00Z",
            "last_seen": "2025-01-15T10:30:00Z",
            "explanation": {"name_similarity": 0.92, "best_variant_score": 0.92, "method": "rapidfuzz_token_sort", "matched_variant": None},
        }],
        "screening_id": "scr-abc123-def456",
        "screened_at": "2025-01-20T14:30:00Z",
    }]}}


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

    model_config = {"json_schema_extra": {"examples": [{
        "id": "PEP-GH-00123",
        "full_name": "Kwame Mensah",
        "aliases": ["K. Mensah", "Kwame A. Mensah"],
        "date_of_birth": "1965-03-15",
        "nationality": "GH",
        "gender": "male",
        "pep_tier": 1,
        "risk_level": "high",
        "is_active_pep": True,
        "positions": [{"title": "Minister of Finance", "institution": "Government of Ghana", "country": "GH", "branch": "EXECUTIVE", "start_date": "2021-01-01", "end_date": None, "is_current": True}],
        "sources": [{"source_url": "https://wikidata.org/wiki/Q12345", "source_type": "WIKIDATA", "country": "GH", "scraped_at": "2025-01-15T10:30:00Z"}],
        "datasets": ["africapep-wikidata"],
        "first_seen": "2024-06-01T00:00:00Z",
        "last_seen": "2025-01-15T10:30:00Z",
    }]}}


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

    model_config = {"json_schema_extra": {"examples": [{
        "query": "Mensah",
        "total": 1,
        "page": 1,
        "limit": 20,
        "results": [{
            "id": "PEP-GH-00123",
            "full_name": "Kwame Mensah",
            "pep_tier": 1,
            "risk_level": "high",
            "is_active": True,
            "nationality": "GH",
            "positions": [{"title": "Minister of Finance", "institution": "Government of Ghana", "country": "GH", "branch": "EXECUTIVE", "start_date": "2021-01-01", "end_date": None, "is_current": True}],
        }],
    }]}}


class StatsResponse(BaseModel):
    total_peps: int = 0
    by_country: dict[str, int] = {}
    by_tier: dict[str, int] = {}
    last_updated: Optional[str] = None
    sources_count: int = 0
    active_peps: int = 0

    model_config = {"json_schema_extra": {"examples": [{
        "total_peps": 15420,
        "by_country": {"GH": 1200, "NG": 3500, "KE": 980, "ZA": 2100},
        "by_tier": {"1": 2500, "2": 5800, "3": 7120},
        "last_updated": "2025-01-20T14:30:00Z",
        "sources_count": 48500,
        "active_peps": 9800,
    }]}}


class HealthResponse(BaseModel):
    status: str
    neo4j: str
    postgres: str
    version: str = "1.0.0"

    model_config = {"json_schema_extra": {"examples": [{
        "status": "healthy",
        "neo4j": "connected",
        "postgres": "connected",
        "version": "1.0.0",
    }]}}


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

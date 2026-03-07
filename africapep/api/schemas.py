"""Pydantic request/response models for the API."""
from datetime import date, datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


# ── Request models ──

class ScreeningRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=200, description="Name to screen")
    country: Optional[str] = Field(None, min_length=2, max_length=2, description="ISO 3166-1 alpha-2 country code")
    threshold: float = Field(0.75, ge=0.0, le=1.0, description="Minimum match score")

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


class MatchResult(BaseModel):
    pep_id: str
    matched_name: str
    match_score: float
    pep_tier: int
    is_active: bool
    positions: list[PositionResponse] = []
    nationality: str = ""
    sources: list[SourceResponse] = []


class ScreeningResponse(BaseModel):
    query: str
    matches: list[MatchResult]
    screening_id: str
    screened_at: str


class PepProfileResponse(BaseModel):
    id: str
    full_name: str
    name_variants: list[str] = []
    date_of_birth: Optional[str] = None
    nationality: str = ""
    gender: str = ""
    pep_tier: int
    is_active_pep: bool = True
    positions: list[PositionResponse] = []
    sources: list[SourceResponse] = []


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
    query: str
    matches: list["MatchResult"]
    screening_id: str
    screened_at: str


class BatchScreeningResponse(BaseModel):
    results: list[BatchScreeningResultItem]
    total_queries: int
    total_matches: int

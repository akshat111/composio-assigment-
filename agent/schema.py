from typing import List, Optional, Literal
from pydantic import BaseModel, Field

class Evidence(BaseModel):
    claim: str = Field(description="The specific claim being backed up by evidence")
    url: str = Field(description="The source URL backing up the claim")
    accessed: str = Field(description="The date/timestamp when the URL was accessed")

class ApiSurface(BaseModel):
    type: Literal["REST", "GraphQL", "REST+GraphQL", "SOAP", "none-found"]
    breadth: Literal["narrow", "moderate", "broad"]
    existing_mcp: Literal[True, False, "unclear"]
    mcp_source: Optional[str] = Field(None, description="Link to the MCP server source or registry listing if it exists")

class AppResearchRecord(BaseModel):
    name: str
    category: str
    one_liner: str
    auth_methods: List[Literal["OAuth2", "API key", "Basic", "Token", "Other", "Unknown"]]
    access_tier: Literal["self-serve-free", "self-serve-trial", "paid-plan-gated", "admin-approval", "contact-sales"]
    api_surface: ApiSurface
    buildability_verdict: Literal["ready-today", "buildable-with-friction", "blocked"]
    primary_blocker: Optional[str] = Field(None, description="The primary reason why the app is blocked or has friction, null if ready-today")
    evidence: List[Evidence] = Field(default_factory=list)
    confidence: Literal["high", "medium", "low"]
    research_pass: int
    notes: Optional[str] = None

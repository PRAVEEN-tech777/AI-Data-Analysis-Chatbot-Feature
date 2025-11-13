"""
Pydantic Models for Structured LLM Output


Defines the expected JSON schema for LLM-generated views.
Requirement 2: LLM Interface with structured outputs (Pydantic schemas)
"""


from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator




class JoinSpecification(BaseModel):
    """Represents a single join in a SQL query"""
    type: str = Field(
        description="JOIN type: INNER, LEFT, RIGHT, FULL, CROSS",
        default="INNER"
    )
    table: str = Field(description="Table name with optional alias (e.g., 'customers c')")
    on: str = Field(description="Join condition (e.g., 'o.customer_id = c.id')")
   
    @validator('type')
    def validate_join_type(cls, v):
        valid_types = {'INNER', 'LEFT', 'RIGHT', 'FULL', 'CROSS'}
        v_upper = v.upper()
        if v_upper not in valid_types:
            raise ValueError(f"Invalid join type: {v}. Must be one of {valid_types}")
        return v_upper
   
    class Config:
        extra = "allow"  # Allow additional fields from LLM




class QuerySpecification(BaseModel):
    """Represents the SQL query structure"""
    select: List[str] = Field(
        description="List of columns/expressions to select"
    )
    from_table: str = Field(
        alias="from",
        description="Base table with optional alias"
    )
    joins: List[JoinSpecification] = Field(default_factory=list)
    where: Optional[List[str]] = Field(
        default=None,
        description="WHERE conditions (AND combined)"
    )
    group_by: Optional[List[str]] = Field(
        default=None,
        description="GROUP BY columns"
    )
    having: Optional[List[str]] = Field(
        default=None,
        description="HAVING conditions"
    )
    order_by: Optional[List[str]] = Field(
        default=None,
        description="ORDER BY columns"
    )
   
    class Config:
        populate_by_name = True
        extra = "allow"




class ViewDefinition(BaseModel):
    """Complete view definition"""
    name: str = Field(
        description="View name (lowercase, underscore-separated)"
    )
    description: str = Field(
        description="Business purpose and semantic meaning of the view"
    )
    query: QuerySpecification
    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional metadata (raw SQL, confidence scores, etc.)"
    )
   
    @validator('name')
    def validate_view_name(cls, v):
        # Remove any SQL-unsafe characters
        v = v.lower().strip()
        # Replace spaces and hyphens with underscores
        v = v.replace(' ', '_').replace('-', '_')
        # Only allow alphanumeric and underscore
        if not v.replace('_', '').replace('_', '').isalnum():
            # Remove invalid characters
            v = ''.join(c for c in v if c.isalnum() or c == '_')
       
        if not v:
            raise ValueError("View name cannot be empty after sanitization")
       
        return v
   
    class Config:
        extra = "allow"




class ViewGenerationResponse(BaseModel):
    """LLM response containing multiple view definitions"""
    views: List[ViewDefinition] = Field(
        description="List of generated database views"
    )
    reasoning: Optional[str] = Field(
        default=None,
        description="Explanation of design choices and rationale"
    )
   
    class Config:
        extra = "allow"




class ValidationResult(BaseModel):
    """Result of view validation"""
    is_valid: bool
    view_name: str
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    sql: Optional[str] = None
    semantic_score: Optional[float] = None




class AnalysisResult(BaseModel):
    """Complete analysis result"""
    total_generated: int
    valid_views: int
    invalid_views: int
    views: List[ValidationResult]
    summary: Dict[str, Any] = Field(default_factory=dict)




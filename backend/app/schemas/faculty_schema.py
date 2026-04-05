from pydantic import BaseModel, Field


class ComplaintResolutionSchema(BaseModel):
    """Schema for submitting a complaint resolution."""

    resolution: str = Field(..., min_length=20, max_length=2000, description="Detailed explanation of the resolution provided.")


class ComplaintResolutionResponse(BaseModel):
    """Response schema after resolving a complaint."""
    message: str
    complaint_id: str
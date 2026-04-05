from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.models.complaint_model import ComplaintPriority, ComplaintStatus


class ComplaintCreate(BaseModel):
    title: str
    description: str
    department_id: str
    priority: Optional[ComplaintPriority] = ComplaintPriority.MEDIUM


class ComplaintOut(BaseModel):
    id: str = Field(..., alias="_id")
    complaint_id: str
    title: str
    description: str
    created_by: str
    department_id: str
    priority: ComplaintPriority
    status: ComplaintStatus
    created_at: datetime
    updated_at: datetime
    deadline: Optional[datetime] = None
    image_url: Optional[str] = None
    resolution: Optional[str] = None
    resolved_at: Optional[datetime] = None

    class Config:
        populate_by_name = True

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import Field

from app.models.base_model import PyObjectId, TimestampMixin
from app.utils.token_utils import generate_complaint_ticket_id


class ComplaintStatus(str, Enum):
    OPEN = "OPEN"
    ASSIGNED = "ASSIGNED"
    IN_PROGRESS = "IN_PROGRESS"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"


class ComplaintPriority(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class Complaint(TimestampMixin):
    complaint_id: str = Field(
        default_factory=generate_complaint_ticket_id,
        description="Human-readable complaint ticket id",
        examples=["#CMP-20260403-7F3A9B"],
    )
    title: str
    description: str
    created_by: PyObjectId = Field(..., description="Foreign key reference to users._id")
    department_id: PyObjectId = Field(..., description="Foreign key reference to departments._id")
    status: ComplaintStatus = ComplaintStatus.OPEN
    priority: ComplaintPriority = ComplaintPriority.MEDIUM
    deadline: Optional[datetime] = None
    escalated_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    resolution_explanation: Optional[str] = None

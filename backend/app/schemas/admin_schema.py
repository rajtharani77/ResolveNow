from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class AdminUserListItem(BaseModel):
    id: str
    name: str
    email: str
    role: str
    user_status: str
    is_email_verified: bool
    created_at: datetime


class PaginatedAdminUsersResponse(BaseModel):
    items: List[AdminUserListItem]
    total: int
    page: int
    page_size: int
    total_pages: int


# Schemas for Department Listing
class DepartmentListItem(BaseModel):
    id: str
    name: str
    description: str
    default_priority: str
    faculty_count: int


class FacultyMemberItem(BaseModel):
    id: str
    name: str
    email: str


class DepartmentDetailItem(BaseModel):
    id: str
    name: str
    description: str
    default_priority: str
    faculty_members: List[FacultyMemberItem]


class FacultyAssignmentRequest(BaseModel):
    user_id: str
    department_id: str


class FacultyAssignmentResponse(BaseModel):
    message: str
    user: AdminUserListItem
    department: DepartmentListItem


class AdminComplaintListItem(BaseModel):
    id: str
    complaint_id: str
    title: str
    description: str
    status: str
    priority: str
    created_at: datetime
    created_by_name: Optional[str] = None
    department_name: Optional[str] = None


class PaginatedAdminComplaintsResponse(BaseModel):
    items: List[AdminComplaintListItem]
    total: int
    page: int
    page_size: int
    total_pages: int
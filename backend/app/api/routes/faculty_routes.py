from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_current_user
from app.core.logger import get_logger
from app.models.user_model import User, UserRole
from app.schemas.complaint_schema import ComplaintOut
from app.schemas.faculty_schema import (ComplaintResolutionResponse,
                                        ComplaintResolutionSchema)
from app.services.faculty_service import FacultyService

router = APIRouter()
logger = get_logger(__name__)


def get_current_faculty_user(current_user: User = Depends(get_current_user)) -> User:
    """Dependency to ensure the current user is a faculty member."""
    if current_user.role != UserRole.FACULTY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: This resource is available for faculty only.",
        )
    return current_user


@router.get(
    "/complaints",
    response_model=list[ComplaintOut],
    summary="List Complaints Assigned to Faculty",
    description="Fetches a list of all complaints that are currently assigned to the logged-in faculty member.",
)
async def get_assigned_complaints(
    faculty_user: User = Depends(get_current_faculty_user),
    faculty_service: FacultyService = Depends(),
) -> Any:
    complaints = await faculty_service.list_assigned_complaints(faculty_id=faculty_user.id)
    return complaints


@router.patch(
    "/complaints/{complaint_id}/resolve",
    response_model=ComplaintResolutionResponse,
    summary="Resolve a Complaint",
    description="Allows a faculty member to mark a complaint as resolved and provide a resolution text.",
    status_code=status.HTTP_200_OK,
)
async def resolve_complaint(
    complaint_id: str,
    resolution_data: ComplaintResolutionSchema,
    faculty_user: User = Depends(get_current_faculty_user),
    faculty_service: FacultyService = Depends(),
) -> Any:
    await faculty_service.resolve_complaint(
        complaint_id=complaint_id, faculty_id=faculty_user.id, resolution_text=resolution_data.resolution
    )
    return {"message": "Complaint has been successfully resolved.", "complaint_id": complaint_id}
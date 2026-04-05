from fastapi import APIRouter, Depends, HTTPException, status
from typing import List

from app.api.deps import get_current_faculty_user
from app.services.complaint_service import ComplaintService
from app.schemas.complaint_schema import ComplaintListItem, ComplaintResolve


router = APIRouter(prefix="/faculty/complaints", tags=["Faculty Complaints"])
complaint_service = ComplaintService()


@router.get("/", response_model=List[ComplaintListItem])
async def get_assigned_complaints(
    current_user: dict = Depends(get_current_faculty_user),
) -> List[ComplaintListItem]:
    """
    Get all complaints assigned to the currently logged-in faculty user.
    This endpoint is protected and only accessible by users with the 'FACULTY' role.
    """
    faculty_id = str(current_user["_id"])
    return await complaint_service.get_faculty_assigned_complaints(faculty_id)


@router.post("/{complaint_id}/resolve", response_model=dict)
async def resolve_complaint(
    complaint_id: str,
    body: ComplaintResolve,
    current_user: dict = Depends(get_current_faculty_user),
):
    """Resolve a complaint assigned to the current faculty user."""
    faculty_id = str(current_user["_id"])
    await complaint_service.resolve_complaint_by_faculty(
        faculty_id, complaint_id, body.resolution_explanation
    )
    return {"message": "Complaint resolved successfully"}

from datetime import datetime, timezone
from typing import Any

from fastapi import Depends, HTTPException, status

from app.core.logger import get_logger
from app.models.complaint_model import ComplaintStatus
from app.repositories.complaint_repository import ComplaintRepository
from app.repositories.facultyAssignmentRepository import FacultyAssignmentRepository
from app.services.notification_service import NotificationService

logger = get_logger(__name__)


class FacultyService:
    def __init__(
        self,
        complaint_repo: ComplaintRepository = Depends(),
        assignment_repo: FacultyAssignmentRepository = Depends(),
        notification_service: NotificationService = Depends(),
    ):
        self.complaint_repo = complaint_repo
        self.assignment_repo = assignment_repo
        self.notification_service = notification_service

    async def list_assigned_complaints(self, faculty_id: Any) -> list[dict[str, Any]]:
        """Fetches all complaints assigned to a specific faculty member."""
        logger.info(f"Fetching complaints for faculty_id: {faculty_id}")
        assignments = await self.assignment_repo.list_by_faculty_id(faculty_id)
        if not assignments:
            logger.info(f"No assignments found for faculty {faculty_id}")
            return []

        complaint_ids = [assignment["complaint_ref_id"] for assignment in assignments]
        if not complaint_ids:
            logger.warning(f"Assignments found for faculty {faculty_id}, but list of complaint_ids is empty.")
            return []

        # Directly fetch the complaints. The repository will handle normalization and sorting.
        complaints = await self.complaint_repo.list_by_ids(complaint_ids)

        logger.info(f"Found {len(complaints)} complaints for faculty_id: {faculty_id}")
        return complaints

    async def resolve_complaint(
        self, complaint_id: Any, faculty_id: Any, resolution_text: str
    ) -> dict[str, Any]:
        """Allows a faculty member to resolve an assigned complaint."""
        logger.info(f"Faculty {faculty_id} attempting to resolve complaint {complaint_id}")

        complaint = await self.complaint_repo.get_one_by_any_id(complaint_id)
        if not complaint:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Complaint not found")

        assignment = await self.assignment_repo.get_by_complaint(complaint["_id"])
        if not assignment or str(assignment.get("faculty_id")) != str(faculty_id):
            logger.warning(f"Forbidden attempt by faculty {faculty_id} to resolve unassigned complaint {complaint_id}")
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not assigned to this complaint")

        if complaint.get("status") == ComplaintStatus.RESOLVED:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Complaint is already resolved")

        update_data = {
            "status": ComplaintStatus.RESOLVED,
            "resolution": resolution_text,
            "resolved_at": datetime.now(timezone.utc),
        }
        updated_complaint = await self.complaint_repo.update(complaint_id, update_data)

        student_id = complaint.get("created_by")
        if student_id:
            try:
                await self.notification_service.create_resolution_notification(
                    user_id=student_id,
                    complaint_id=complaint_id,
                    complaint_title=complaint.get("title", "N/A"),
                )
                logger.info(f"Resolution notification sent for complaint {complaint_id} to student {student_id}")
            except Exception as e:
                logger.error(f"Failed to send resolution notification for complaint {complaint_id}: {e}")

        return updated_complaint
from datetime import datetime

from fastapi import HTTPException, status

from app.core.logger import get_logger
from app.models.base_model import ObjectId
from app.models.complaint_model import ComplaintStatus
from app.repositories.complaint_repository import ComplaintRepository
from app.repositories.department_repository import DepartmentRepository
from app.repositories.facultyAssignmentRepository import FacultyAssignmentRepository
from app.utils.round_robin import get_next_faculty_id

logger = get_logger("service.assignment")


class AssignmentService:
    def __init__(self) -> None:
        self.department_repository = DepartmentRepository()
        self.faculty_assignment_repository = FacultyAssignmentRepository()
        self.complaint_repository = ComplaintRepository()

    async def assign_complaint(self, complaint: dict) -> dict:
        complaint_ref = complaint.get("complaint_id") or str(complaint.get("_id"))
        logger.info("Assignment started: complaint=%s department_id=%s", complaint_ref, complaint.get("department_id"))

        department = await self.department_repository.find_by_id(complaint["department_id"])
        if not department:
            logger.error("Assignment failed – department not found: department_id=%s", complaint.get("department_id"))
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Department not found for complaint assignment.",
            )

        faculty_user_ids = department.get("faculty_user_ids", [])
        if not faculty_user_ids:
            logger.warning(
                "Assignment failed – no faculty in department: department_id=%s name=%s",
                complaint.get("department_id"),
                department.get("name"),
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No faculty available for the selected department.",
            )

        latest_assignment = await self.faculty_assignment_repository.get_latest_by_department(
            complaint["department_id"]
        )
        last_assigned_faculty_id = (
            latest_assignment.get("faculty_id") if latest_assignment else None
        )

        logger.debug(
            "Round-robin state: department=%s faculty_count=%d last_faculty_id=%s",
            department.get("name"),
            len(faculty_user_ids),
            str(last_assigned_faculty_id) if last_assigned_faculty_id else "none",
        )

        next_faculty_id = get_next_faculty_id(faculty_user_ids, last_assigned_faculty_id)
        assigned_at = datetime.utcnow()

        complaint_object_id = (
            ObjectId(complaint["_id"])
            if isinstance(complaint["_id"], str) and ObjectId.is_valid(complaint["_id"])
            else complaint["_id"]
        )
        department_object_id = (
            ObjectId(complaint["department_id"])
            if isinstance(complaint["department_id"], str)
            and ObjectId.is_valid(complaint["department_id"])
            else complaint["department_id"]
        )

        assignment_record = {
            "complaint_id": complaint_object_id,
            "faculty_id": next_faculty_id,
            "department_id": department_object_id,
            "assigned_at": assigned_at,
            "assigned_by": None,
            "created_at": assigned_at,
            "updated_at": assigned_at,
        }
        await self.faculty_assignment_repository.create(assignment_record)
        await self.complaint_repository.update_assignment_status(
            complaint["_id"],
            status=ComplaintStatus.ASSIGNED.value,
            updated_at=assigned_at,
        )

        logger.info(
            "Assignment complete: complaint=%s faculty_id=%s department=%s",
            complaint_ref,
            str(next_faculty_id),
            department.get("name"),
        )

        return {
            "faculty_id": str(next_faculty_id),
            "assigned_at": assigned_at,
            "status": ComplaintStatus.ASSIGNED.value,
        }
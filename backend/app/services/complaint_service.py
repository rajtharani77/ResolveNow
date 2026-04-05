from datetime import datetime, timedelta

from bson import ObjectId
from bson.errors import InvalidId
from fastapi import HTTPException, status

from app.config.settings import settings
from app.core.logger import get_logger
from app.models.complaint_model import ComplaintPriority
from app.repositories.complaint_repository import ComplaintRepository
from app.repositories.department_repository import DepartmentRepository
from app.schemas.complaint_schema import ComplaintCreate
from app.services.assignment_service import AssignmentService
from app.utils.s3_utils import generate_filename, upload_file
from app.utils.token_utils import generate_complaint_ticket_id

logger = get_logger("service.complaint")


class ComplaintService:

    def __init__(self):
        self.repo = ComplaintRepository()
        self.department_repository = DepartmentRepository()
        self.assignment_service = AssignmentService()

    async def create_complaint(self, user_id: str, data: ComplaintCreate, file):
        logger.info(
            "Complaint creation started: user_id=%s department_id=%s priority=%s",
            user_id,
            data.department_id,
            data.priority,
        )

        image_url = None

        # Upload file to S3 if provided and credentials are configured
        if file and settings.aws_access_key_id and settings.aws_secret_access_key:
            logger.debug("Uploading attachment to S3: filename=%s", file.filename)
            try:
                filename = generate_filename(file.filename)
                image_url = upload_file(file.file, filename)
                logger.info("Attachment uploaded: url=%s", image_url)
            except Exception as exc:
                logger.error("S3 upload failed: %s", repr(exc), exc_info=True)
                image_url = None

        try:
            created_by = ObjectId(user_id)
            department_id = ObjectId(data.department_id)
        except InvalidId as exc:
            logger.warning(
                "Invalid IDs in complaint creation: user_id=%s department_id=%s",
                user_id,
                data.department_id,
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid department or user identifier.",
            ) from exc

        department = await self.department_repository.find_by_id(department_id)
        if not department:
            logger.warning("Complaint creation failed – department not found: department_id=%s", data.department_id)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Department not found.",
            )

        if not department.get("faculty_user_ids"):
            logger.warning(
                "Complaint creation failed – no faculty in department: department_id=%s name=%s",
                data.department_id,
                department.get("name"),
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No faculty available for the selected department.",
            )

        created_at = datetime.now()
        deadline = created_at + timedelta(days=4)

        complaint_data = {
            "complaint_id": generate_complaint_ticket_id(),
            "title": data.title,
            "description": data.description,
            "created_by": created_by,
            "department_id": department_id,
            "priority": data.priority or ComplaintPriority.MEDIUM,
            "deadline": deadline,
            "image_url": image_url,
            "status": "OPEN",
            "created_at": created_at,
            "updated_at": created_at,
        }

        created_complaint = await self.repo.create(complaint_data)
        logger.info(
            "Complaint saved: complaint_id=%s user_id=%s department=%s deadline=%s",
            created_complaint.get("complaint_id"),
            user_id,
            department.get("name"),
            deadline.isoformat(),
        )

        assignment_result = await self.assignment_service.assign_complaint(created_complaint)

        if assignment_result:
            created_complaint["status"] = assignment_result.get("status", "OPEN")
            created_complaint["assigned_faculty_id"] = assignment_result.get("faculty_id")
            created_complaint["assigned_at"] = assignment_result.get("assigned_at")
            logger.info(
                "Complaint assigned: complaint_id=%s faculty_id=%s status=%s",
                created_complaint.get("complaint_id"),
                assignment_result.get("faculty_id"),
                assignment_result.get("status"),
            )

        return created_complaint

    async def get_user_complaints(self, user_id: str):
        logger.debug("Fetching complaints for user: user_id=%s", user_id)
        try:
            user_obj_id = ObjectId(user_id)
        except InvalidId as exc:
            logger.warning("Invalid user_id in get_user_complaints: user_id=%s", user_id)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid user identifier.",
            ) from exc

        complaints = await self.repo.get_by_user(user_obj_id)
        logger.debug("Complaints fetched: user_id=%s count=%d", user_id, len(complaints))
        return complaints
        print("user_id:", user_obj_id)
        print("userid", user_id)
        return await self.repo.get_by_user(user_obj_id)

    async def get_user_complaint_by_id(self, user_id: str, identifier: str):
        """
        Return a single complaint by either Mongo _id or complaint_id,
        ensuring it belongs to the requesting user.
        """
        try:
            user_obj_id = ObjectId(user_id)
        except InvalidId as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid user identifier.",
            ) from exc

        complaint = await self.repo.get_one_by_any_id(identifier)
        if not complaint:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Complaint not found.",
            )

        # Enforce ownership
        if str(complaint.get("created_by")) != str(user_obj_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Complaint not found.",
            )

        return complaint

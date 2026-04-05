from datetime import datetime, timedelta
from bson.errors import InvalidId
from fastapi import HTTPException, status
from bson import ObjectId  # ✅ IMPORTANT

from app.repositories.complaint_repository import ComplaintRepository
from app.repositories.department_repository import DepartmentRepository
from app.repositories.user_repository import UserRepository
from app.services.assignment_service import AssignmentService
from app.schemas.complaint_schema import ComplaintCreate
from app.utils.s3_utils import upload_file, generate_filename
from app.models.complaint_model import ComplaintPriority
from app.utils.token_utils import generate_complaint_ticket_id
from app.config.settings import settings
from app.config.email import send_complaint_resolved_email

class ComplaintService:

    async def resolve_complaint_by_faculty(self, faculty_user_id: str, complaint_id: str, resolution_explanation: str):
        
        complaint = await self.repo.get_by_id(complaint_id)
        if not complaint:
            raise HTTPException(status_code=404, detail="Complaint not found")
        
        if str(complaint.get("assigned_faculty_id")) != str(faculty_user_id):
            raise HTTPException(status_code=403, detail="Not authorized to resolve this complaint")

        if complaint.get("status") == "RESOLVED":
            return complaint

        # Update fields
        try:
            obj_id = ObjectId(complaint_id)
        except InvalidId:
            raise HTTPException(status_code=400, detail="Invalid complaint ID")

        update_result = await self.repo.collection.update_one(
            {"_id": obj_id},
            {"$set": {
                "status": "RESOLVED",
                "resolved_at": datetime.utcnow(),
                "resolution_explanation": resolution_explanation,
                "updated_at": datetime.utcnow(),
            }}
        )

        if update_result.modified_count > 0:
            student_id = complaint.get("created_by")
            student = await self.user_repository.find_by_id(str(student_id))
            if student and student.get("email"):
                send_complaint_resolved_email(
                    recipient=student["email"],
                    recipient_name=student["name"],
                    complaint_title=complaint["title"],
                    complaint_id_str=complaint["complaint_id"]
                )

        updated = await self.repo.get_by_id(complaint_id)
        return updated

    async def get_faculty_assigned_complaints(self, faculty_user_id: str):
        return await self.repo.get_by_assigned_faculty(faculty_user_id)

    def __init__(self):
        self.repo = ComplaintRepository()
        self.department_repository = DepartmentRepository()
        self.assignment_service = AssignmentService()
        self.user_repository = UserRepository()

    async def create_complaint(self, user_id: str, data: ComplaintCreate, file):
        image_url = None

        if file and settings.aws_access_key_id:
            try:
                filename = generate_filename(file.filename)
                image_url = upload_file(file.file, filename)
            except Exception as e:
                print("S3 ERROR:", str(e))
                image_url = None

        try:
            created_by = ObjectId(user_id)
            department_id = ObjectId(data.department_id)
        except InvalidId as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid department or user identifier.",
            ) from exc

        department = await self.department_repository.find_by_id(department_id)
        if not department:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Department not found.",
            )

        if not department.get("faculty_user_ids"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No faculty available for the selected department.",
            )

        deadline = datetime.utcnow() + timedelta(days=4)
        created_at = datetime.utcnow()

        complaint_data = {
            "complaint_id": generate_complaint_ticket_id(),
            "title": data.title,
            "description": data.description,
            "created_by": ObjectId(user_id),                 # ✅ FIX
            "department_id": ObjectId(data.department_id),   # ✅ FIX
            "priority": data.priority or ComplaintPriority.MEDIUM,
            "deadline": deadline,
            "image_url": image_url,
        }

        complaint_data["created_by"] = created_by
        complaint_data["department_id"] = department_id
        complaint_data["status"] = "OPEN"
        complaint_data["created_at"] = created_at
        complaint_data["updated_at"] = created_at

        created_complaint = await self.repo.create(complaint_data)
        assignment_result = await self.assignment_service.assign_complaint(created_complaint)
        created_complaint["status"] = assignment_result["status"]
        created_complaint["assigned_faculty_id"] = assignment_result["faculty_id"]
        created_complaint["assigned_at"] = assignment_result["assigned_at"]
        return created_complaint

    async def get_user_complaints(self, user_id: str):
        return await self.repo.get_by_user(user_id)

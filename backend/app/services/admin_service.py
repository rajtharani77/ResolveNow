from datetime import datetime

from fastapi import HTTPException, status

from app.models.base_model import ObjectId
from app.models.complaint_model import ComplaintPriority
from app.models.user_model import UserRole, UserStatus
from app.repositories.complaint_repository import ComplaintRepository
from app.repositories.department_repository import DepartmentRepository
from app.repositories.user_repository import UserRepository
from app.schemas.admin_schema import (
    AdminComplaintListItem,
    AdminUserListItem,
    DepartmentDetailItem,
    DepartmentListItem,
    FacultyAssignmentResponse,
    FacultyMemberItem,
    PaginatedAdminComplaintsResponse,
    PaginatedAdminUsersResponse,
)


class AdminService:
    def __init__(self) -> None:
        self.user_repository = UserRepository()
        self.department_repository = DepartmentRepository()
        self.complaint_repository = ComplaintRepository()

    @staticmethod
    def _map_user(user: dict) -> AdminUserListItem:
        return AdminUserListItem(
            id=str(user["_id"]),
            name=user["name"],
            email=user["email"],
            role=user["role"],
            user_status=user.get("user_status") or UserStatus.ACTIVE.value,
            is_email_verified=user.get("is_email_verified", False),
            created_at=user["created_at"],
        )

    @staticmethod
    def _map_department(department: dict) -> DepartmentListItem:
        return DepartmentListItem(
            id=str(department["_id"]),
            name=department["name"],
            description=department["description"],
            default_priority=department["default_priority"],
            faculty_count=len(department.get("faculty_user_ids", [])),
        )

    @staticmethod
    def _map_faculty_member(user: dict) -> FacultyMemberItem:
        return FacultyMemberItem(
            id=str(user["_id"]),
            name=user["name"],
            email=user["email"],
        )

    @staticmethod
    def _map_complaint(
        complaint: dict,
        *,
        users_by_id: dict[str, dict],
        departments_by_id: dict[str, dict],
    ) -> AdminComplaintListItem:
        created_by = users_by_id.get(str(complaint.get("created_by")))
        department = departments_by_id.get(str(complaint.get("department_id")))
        return AdminComplaintListItem(
            id=str(complaint["_id"]),
            complaint_id=complaint.get("complaint_id", "N/A"),
            title=complaint.get("title", "No Title Provided"),
            description=complaint.get("description", "No description available."),
            priority=complaint.get("priority", "UNKNOWN"),
            status=complaint.get("status", "UNKNOWN"),
            created_at=complaint.get("created_at", datetime.utcnow()),
            created_by_name=created_by.get("name") if created_by else None,
            department_name=department.get("name") if department else None,
        )

    async def list_regular_users(
        self,
        *,
        page: int,
        page_size: int,
    ) -> PaginatedAdminUsersResponse:
        filters = {
            "role": UserRole.FACULTY.value,
            "user_status": UserStatus.PENDING_APPROVAL.value,
        }
        total = await self.user_repository.count_by_filters(filters)
        users = await self.user_repository.list_by_filters(
            filters,
            skip=(page - 1) * page_size,
            limit=page_size,
        )
        total_pages = (total + page_size - 1) // page_size if total > 0 else 0
        return PaginatedAdminUsersResponse(
            items=[self._map_user(user) for user in users],
            page=page,
            page_size=page_size,
            total=total,
            total_pages=total_pages,
        )

    async def list_departments(self) -> list[DepartmentListItem]:
        departments = await self.department_repository.list_all()
        return [self._map_department(department) for department in departments]

    async def list_department_details(self) -> list[DepartmentDetailItem]:
        departments = await self.department_repository.list_all()
        department_details: list[DepartmentDetailItem] = []

        for department in departments:
            faculty_user_ids = department.get("faculty_user_ids", [])
            faculty_users = await self.user_repository.list_by_ids(faculty_user_ids)
            department_details.append(
                DepartmentDetailItem(
                    id=str(department["_id"]),
                    name=department["name"],
                    description=department["description"],
                    default_priority=department["default_priority"],
                    faculty_members=[
                        self._map_faculty_member(user) for user in faculty_users
                    ],
                )
            )

        return department_details

    async def list_complaints(
        self,
        *,
        page: int,
        page_size: int,
        priority: str | None = None,
        title_query: str | None = None,
    ) -> PaginatedAdminComplaintsResponse:
        filters: dict[str, object] = {}

        if priority:
            normalized_priority = priority.upper()
            if normalized_priority not in {item.value for item in ComplaintPriority}:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid priority filter.",
                )
            filters["priority"] = normalized_priority

        if title_query:
            filters["title"] = {"$regex": title_query, "$options": "i"}

        total = await self.complaint_repository.count_with_filters(filters)
        complaints = await self.complaint_repository.list_with_filters(
            filters,
            skip=(page - 1) * page_size,
            limit=page_size,
        )

        user_ids_set = {c.get("created_by") for c in complaints}
        user_ids_set.discard(None)
        user_ids = list(user_ids_set)

        department_ids_set = {c.get("department_id") for c in complaints}
        department_ids_set.discard(None)
        department_ids = list(department_ids_set)

        users = await self.user_repository.list_by_ids(user_ids)
        departments = await self.department_repository.list_by_ids(department_ids)
        users_by_id = {str(user["_id"]): user for user in users}
        departments_by_id = {str(department["_id"]): department for department in departments}
        total_pages = (total + page_size - 1) // page_size if total > 0 else 0

        return PaginatedAdminComplaintsResponse(
            items=[
                self._map_complaint(
                    complaint,
                    users_by_id=users_by_id,
                    departments_by_id=departments_by_id,
                )
                for complaint in complaints
            ],
            page=page,
            page_size=page_size,
            total=total,
            total_pages=total_pages,
        )

    async def assign_faculty_to_department(
        self,
        *,
        user_id: str,
        department_id: str,
    ) -> FacultyAssignmentResponse:
        if not ObjectId.is_valid(user_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid user id.",
            )

        if not ObjectId.is_valid(department_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid department id.",
            )

        user = await self.user_repository.find_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found.",
            )

        if user.get("role") != UserRole.FACULTY.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only faculty users can be assigned to departments.",
            )

        if user.get("user_status") != UserStatus.PENDING_APPROVAL.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only faculty users pending approval can be assigned to departments.",
            )

        department = await self.department_repository.find_by_id(department_id)
        if not department:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Department not found.",
            )

        now = datetime.utcnow()
        await self.user_repository.update_user(
            user["_id"],
            {
                "user_status": UserStatus.ACTIVE.value,
                "updated_at": now,
            },
        )
        await self.department_repository.remove_faculty_from_all_departments(
            user["_id"],
            now,
        )
        await self.department_repository.assign_faculty_to_department(
            department["_id"],
            user["_id"],
            now,
        )

        updated_user = await self.user_repository.find_by_id(user["_id"])
        updated_department = await self.department_repository.find_by_id(department["_id"])
        return FacultyAssignmentResponse(
            message="Faculty approved and department mapping updated successfully.",
            user=self._map_user(updated_user),
            department=self._map_department(updated_department),
        )
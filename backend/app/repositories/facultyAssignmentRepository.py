from typing import Any, Optional

from app.config.database import get_database
from app.models.base_model import ObjectId


class FacultyAssignmentRepository:
    @property
    def collection(self) -> Any:
        return get_database()["faculty_assignments"]

    async def create(self, assignment_dict: dict[str, Any]) -> dict[str, Any]:
        result = await self.collection.insert_one(assignment_dict)
        assignment_dict["_id"] = result.inserted_id
        return assignment_dict

    async def get_latest_by_department(self, department_id: Any) -> Optional[dict[str, Any]]:
        normalized_department_id = department_id
        if (
            isinstance(department_id, str)
            and hasattr(ObjectId, "is_valid")
            and ObjectId.is_valid(department_id)
        ):
            normalized_department_id = ObjectId(department_id)

        return await self.collection.find_one(
            {"department_id": normalized_department_id},
            sort=[("assigned_at", -1)],
        )

    async def get_latest_by_complaint(self, complaint_id: Any) -> Optional[dict[str, Any]]:
        """
        Find the most recent faculty assignment record for a given complaint (_id).
        """
        normalized_complaint_id = complaint_id
        if (
            isinstance(complaint_id, str)
            and hasattr(ObjectId, "is_valid")
            and ObjectId.is_valid(complaint_id)
        ):
            normalized_complaint_id = ObjectId(complaint_id)

        return await self.collection.find_one(
            {"complaint_ref_id": normalized_complaint_id},
            sort=[("assigned_at", -1)],
        )

    async def get_by_complaint(self, complaint_id: Any) -> Optional[dict[str, Any]]:
        """
        Fetch the faculty assignment record for a given complaint.
        Assumes at most one assignment per complaint.
        """
        normalized_complaint_id = complaint_id
        if (
            isinstance(complaint_id, str)
            and hasattr(ObjectId, "is_valid")
            and ObjectId.is_valid(complaint_id)
        ):
            normalized_complaint_id = ObjectId(complaint_id)
        return await self.collection.find_one({"complaint_ref_id": normalized_complaint_id})

    async def list_by_complaint_ids(self, complaint_ids: list[Any]) -> list[dict[str, Any]]:
        """
        Fetch assignment records for multiple complaint ids.
        """
        if not complaint_ids:
            return []
        normalized_ids: list[Any] = []
        for cid in complaint_ids:
            if isinstance(cid, str) and hasattr(ObjectId, "is_valid") and ObjectId.is_valid(cid):
                normalized_ids.append(ObjectId(cid))
            else:
                normalized_ids.append(cid)
        cursor = self.collection.find({"complaint_ref_id": {"$in": normalized_ids}})
        return await cursor.to_list(length=None)

    async def list_by_faculty_id(self, faculty_id: Any) -> list[dict[str, Any]]:
        """
        Fetch all assignment records for a given faculty member, sorted by most recent.
        """
        normalized_faculty_id = faculty_id
        if isinstance(faculty_id, str) and ObjectId.is_valid(faculty_id):
            normalized_faculty_id = ObjectId(faculty_id)

        cursor = self.collection.find({"faculty_id": normalized_faculty_id}).sort(
            "assigned_at", -1
        )
        return await cursor.to_list(length=None)

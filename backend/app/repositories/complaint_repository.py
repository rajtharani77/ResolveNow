from typing import Any

from app.config.database import get_database
from app.config.database import get_database
from bson import ObjectId
from typing import List


class ComplaintRepository:
    @property
    def collection(self) -> Any:
        return get_database()["complaints"]

    async def count_with_filters(self, filters: dict[str, Any]) -> int:
        return await self.collection.count_documents(filters)

    async def list_with_filters(
        self,
        filters: dict[str, Any],
        *,
        skip: int,
        limit: int,
    ) -> list[dict[str, Any]]:
        complaints_cursor = (
            self.collection.find(filters).sort("created_at", -1).skip(skip).limit(limit)
        )
        return await complaints_cursor.to_list(length=None)

    async def update_assignment_status(
        self,
        complaint_id: Any,
        *,
        status: str,
        updated_at: Any,
    ) -> None:
        db = get_database()
        normalized_complaint_id = complaint_id
        if isinstance(complaint_id, str) and ObjectId.is_valid(complaint_id):
            normalized_complaint_id = ObjectId(complaint_id)

        await db["complaints"].update_one(
            {"_id": normalized_complaint_id},
            {
                "$set": {
                    "status": status,
                    "updated_at": updated_at,
                }
            },
        )



class ComplaintRepository:

    @property
    def collection(self) -> Any:
        return get_database()["complaints"]

    async def create(self, data: dict):
        db = get_database()

        result = await db["complaints"].insert_one(data)
        data["_id"] = str(result.inserted_id)

        # ✅ FIX: convert ObjectId fields
        data["created_by"] = str(data["created_by"])
        data["department_id"] = str(data["department_id"])

        return data

    async def get_by_user(self, user_id: str) -> List[dict]:
        db = get_database()

        complaints = await db["complaints"].find(
            {"created_by": ObjectId(user_id)}
        ).to_list(length=100)

        # ✅ FIX: convert all ObjectIds
        for c in complaints:
            c["_id"] = str(c["_id"])
            c["created_by"] = str(c["created_by"])
            c["department_id"] = str(c["department_id"])

        return complaints

    async def get_by_id(self, complaint_id: str):
        db = get_database()

        complaint = await db["complaints"].find_one(
            {"complaint_id": complaint_id}
        )

        if complaint:
            complaint["_id"] = str(complaint["_id"])
            complaint["created_by"] = str(complaint["created_by"])
            complaint["department_id"] = str(complaint["department_id"])

        return complaint

    async def update_assignment_status(
        self,
        complaint_id: Any,
        *,
        status: str,
        updated_at: Any,
    ) -> None:
        normalized_complaint_id = complaint_id
        if isinstance(complaint_id, str) and ObjectId.is_valid(complaint_id):
            normalized_complaint_id = ObjectId(complaint_id)

        await self.collection.update_one(
            {"_id": normalized_complaint_id},
            {
                "$set": {
                    "status": status,
                    "updated_at": updated_at,
                }
            },
        )
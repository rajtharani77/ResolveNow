from typing import Any, List

from app.models.base_model import ObjectId

from app.config.database import get_database


class ComplaintRepository:
    @property
    def collection(self) -> Any:
        return get_database()["complaints"]

    # Admin listing helpers (keep raw ObjectIds to allow efficient $in lookups)
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

    # Creation (normalize returned ids to strings for client-side use)
    async def create(self, data: dict):
        db = get_database()
        result = await db["complaints"].insert_one(data)
        data["_id"] = str(result.inserted_id)
        # Normalize ObjectId fields to strings
        data["created_by"] = str(data["created_by"])
        data["department_id"] = str(data["department_id"])
        return data

    # Student listing (normalize to strings)
    async def get_by_user(self, user_id: str) -> List[dict]:
        complaints_cursor = self.collection.find(
            {"created_by": ObjectId(user_id)}
        ).sort("created_at", -1)
        complaints = await complaints_cursor.to_list(length=None)
        for c in complaints:
            c["_id"] = str(c["_id"])
            if c.get("created_by"):
                c["created_by"] = str(c["created_by"])
            if c.get("department_id"):
                c["department_id"] = str(c["department_id"])
        return complaints

    # Fetch by human-readable complaint_id (normalize to strings)
    async def get_by_id(self, complaint_id: str):
        db = get_database()
        complaint = await db["complaints"].find_one({"complaint_id": complaint_id})
        if complaint:
            complaint["_id"] = str(complaint["_id"])
            complaint["created_by"] = str(complaint["created_by"])
            complaint["department_id"] = str(complaint["department_id"])
        return complaint

    # Fetch by either Mongo _id or complaint_id (normalize to strings)
    async def get_one_by_any_id(self, identifier: str):
        query = {"_id": ObjectId(identifier)} if ObjectId.is_valid(identifier) else {"complaint_id": identifier}
        complaint = await self.collection.find_one(query)
        if not complaint:
            return None
        complaint["_id"] = str(complaint["_id"])
        if complaint.get("created_by") is not None:
            try:
                complaint["created_by"] = str(complaint["created_by"])
            except Exception:
                pass
        if complaint.get("department_id") is not None:
            try:
                complaint["department_id"] = str(complaint["department_id"])
            except Exception:
                pass
        return complaint

    async def list_by_ids(self, complaint_ids: list[Any]) -> list[dict[str, Any]]:
        """
        Fetch all complaints for a given list of complaint ObjectIds, sorted by most recent.
        """
        if not complaint_ids:
            return []

        normalized_ids: list[ObjectId] = []
        for cid in complaint_ids:
            if isinstance(cid, str) and ObjectId.is_valid(cid):
                normalized_ids.append(ObjectId(cid))
            elif isinstance(cid, ObjectId):
                normalized_ids.append(cid)

        if not normalized_ids:
            return []

        cursor = self.collection.find({"_id": {"$in": normalized_ids}}).sort("created_at", -1)
        complaints = await cursor.to_list(length=None)

        for c in complaints:
            c["_id"] = str(c["_id"])
            if c.get("created_by"):
                c["created_by"] = str(c["created_by"])
            if c.get("department_id"):
                c["department_id"] = str(c["department_id"])

        return complaints

    async def update(self, complaint_id: Any, update_data: dict[str, Any]) -> dict[str, Any] | None:
        """
        Updates a complaint by its MongoDB _id and returns the updated document.
        """
        normalized_id = complaint_id
        if isinstance(complaint_id, str) and ObjectId.is_valid(complaint_id):
            normalized_id = ObjectId(complaint_id)

        result = await self.collection.find_one_and_update(
            {"_id": normalized_id},
            {"$set": update_data},
            return_document=True,
        )

        if result:
            result["_id"] = str(result["_id"])
            if result.get("created_by"):
                result["created_by"] = str(result["created_by"])
            if result.get("department_id"):
                result["department_id"] = str(result["department_id"])

        return result

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

from datetime import datetime
from typing import Optional

from bson import ObjectId
from pydantic import BaseModel, Field


# Helper for ObjectId serialization/validation in Pydantic models
class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v, field):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid objectid")
        return ObjectId(v)

    @classmethod
    def __get_pydantic_json_schema__(cls, core_schema, handler):
        # For Pydantic V2
        json_schema = handler(core_schema)
        json_schema.update(type="string")
        return json_schema


class ComplaintListItem(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    complaint_id: str
    title: str
    description: str
    status: str
    priority: str
    department_id: PyObjectId
    deadline: Optional[datetime] = None
    image_url: Optional[str] = None
    resolution_explanation: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        populate_by_name = True
        from_attributes = True
        json_encoders = {ObjectId: str}


class ComplaintResolve(BaseModel):
    resolution_explanation: str


class ComplaintCreate(BaseModel):
    title: str
    description: str
    department_id: str
    priority: Optional[str] = "MEDIUM"

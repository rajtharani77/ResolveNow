from datetime import datetime

from app.config.security import hash_password
from app.config.database import get_database
from app.models.user_model import UserRole, UserStatus
from app.models.department_model import DepartmentName


def build_sample_faculty() -> list[dict]:
    current_time = datetime.utcnow()
    return [
        {
            "name": "Dr. Vivek Sharma",
            "email": "vivek.sharma@example.com",
            "password_hash": hash_password("Password123"),
            "role": UserRole.FACULTY.value,
            "user_status": UserStatus.ACTIVE.value,
            "is_email_verified": True,
            "is_active": True,
            "email_verification": None,
            "refresh_tokens": [],
            "created_at": current_time,
            "updated_at": current_time,
            "department": DepartmentName.BEHAVIOURAL.value,
        },
        {
            "name": "Prof. Anita Desai",
            "email": "anita.desai@example.com",
            "password_hash": hash_password("Password123"),
            "role": UserRole.FACULTY.value,
            "user_status": UserStatus.ACTIVE.value,
            "is_email_verified": True,
            "is_active": True,
            "email_verification": None,
            "refresh_tokens": [],
            "created_at": current_time,
            "updated_at": current_time,
            "department": DepartmentName.INFRASTRUCTURAL.value,
        },
        {
            "name": "Dr. Rajesh Kumar",
            "email": "rajesh.kumar@example.com",
            "password_hash": hash_password("Password123"),
            "role": UserRole.FACULTY.value,
            "user_status": UserStatus.ACTIVE.value,
            "is_email_verified": True,
            "is_active": True,
            "email_verification": None,
            "refresh_tokens": [],
            "created_at": current_time,
            "updated_at": current_time,
            "department": DepartmentName.ACADEMIC.value,
        },
        {
            "name": "Prof. Sunita Singh",
            "email": "sunita.singh@example.com",
            "password_hash": hash_password("Password123"),
            "role": UserRole.FACULTY.value,
            "user_status": UserStatus.ACTIVE.value,
            "is_email_verified": True,
            "is_active": True,
            "email_verification": None,
            "refresh_tokens": [],
            "created_at": current_time,
            "updated_at": current_time,
            "department": DepartmentName.GENERAL.value,
        },
    ]


async def seed_faculty() -> None:
    """
    Ensures sample faculty exist and synchronizes related data.
    - Inserts a sample faculty member if they don't exist by email.
    - Links the most recent faculty user ID to the correct department.
    - Finds any assignments pointing to stale/old faculty user IDs (from previous
      seeding runs) and updates them to point to the current faculty user ID.
    """
    db = get_database()
    user_collection = db["users"]
    dept_collection = db["departments"]
    assignments_collection = db["faculty_assignments"]

    sample_faculty = build_sample_faculty()

    for faculty_data in sample_faculty:
        email = faculty_data["email"]
        dept_name = faculty_data.pop("department")

        # Find all users with this email, newest first
        cursor = user_collection.find({"email": email}).sort("created_at", -1)
        all_users_with_email = await cursor.to_list(length=None)

        current_user_id = None
        if not all_users_with_email:
            # If user doesn't exist at all, create them
            result = await user_collection.insert_one(faculty_data)
            current_user_id = result.inserted_id
        else:
            # The first one in the sorted list is the current one
            current_user_id = all_users_with_email[0]["_id"]

        # Ensure the current user is linked to the department
        await dept_collection.update_one(
            {"name": dept_name}, {"$addToSet": {"faculty_user_ids": current_user_id}}
        )

        # Find all other (stale) IDs for this email
        stale_ids = [user["_id"] for user in all_users_with_email[1:]]

        if stale_ids:
            # Update any assignments pointing to old IDs
            await assignments_collection.update_many(
                {"faculty_id": {"$in": stale_ids}}, {"$set": {"faculty_id": current_user_id}}
            )

import asyncio
import sys
import os

# This allows the script to import the application's settings
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.config.database import get_database, connect_to_mongo, close_mongo_connection
from app.seeds.department_seed import seed_departments
from app.seeds.faculty_seed import seed_faculty
from app.seeds.user_seed import seed_users
from app.services.auth_service import AuthService


async def main():
    await connect_to_mongo()
    db = get_database()

    collections_to_drop = ["users", "departments", "complaints", "faculty_assignments"]
    print(f"Dropping collections: {', '.join(collections_to_drop)}")
    for collection_name in collections_to_drop:
        await db.drop_collection(collection_name)
    print("Collections dropped successfully.")

    print("\nSeeding initial data...")
    await seed_departments()
    print("- Departments seeded.")
    await seed_users()
    print("- Sample students seeded.")
    await seed_faculty()
    print("- Sample faculty seeded and assignments synchronized.")

    auth_service = AuthService()
    await auth_service.ensure_initial_admin()
    print("- Initial admin account ensured.")

    print("\nDatabase reset and seed complete.")
    await close_mongo_connection()

if __name__ == "__main__":
    if input("This will WIPE collections from the database. Are you sure? (y/N) ").lower() != "y":
        print("Aborted.")
        exit()
    asyncio.run(main())
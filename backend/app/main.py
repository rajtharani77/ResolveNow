from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.admin_routes import router as admin_router
from app.api.routes.auth_routes import router as auth_router
from app.config.database import close_mongo_connection, connect_to_mongo, initialize_database
from app.config.settings import settings
from app.seeds.department_seed import seed_departments
from app.seeds.faculty_seed import seed_faculty
from app.seeds.user_seed import seed_users
from app.services.auth_service import AuthService

from app.api.routes.complaint_routes import router as complaint_router
from app.api.routes.faculty_routes import router as faculty_router


auth_service = AuthService()


@asynccontextmanager
async def lifespan(_: FastAPI):
    await connect_to_mongo()
    await initialize_database()
    await seed_departments()
    await seed_users()
    await seed_faculty()
    await auth_service.ensure_initial_admin()
    try:
        yield
    finally:
        await close_mongo_connection()


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    debug=settings.debug,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix=settings.api_prefix)
app.include_router(admin_router, prefix=settings.api_prefix)

app.include_router(
    complaint_router,
    prefix="/api/v1/complaints",
    tags=["Complaints"]
)
app.include_router(
    faculty_router,
    prefix="/api/v1",
)


@app.get("/", tags=["Health"])
async def root() -> dict[str, str]:
    return {"message": f"{settings.app_name} API is running"}


@app.get("/health", tags=["Health"])
async def health_check() -> dict[str, str]:
    return {"status": "ok", "environment": settings.app_env}


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )

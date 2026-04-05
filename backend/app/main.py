from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.admin_routes import router as admin_router
from app.api.routes.auth_routes import router as auth_router
from app.api.routes.complaint_routes import router as complaint_router
from app.config.database import close_mongo_connection, connect_to_mongo, initialize_database
from app.config.settings import settings
from app.core.logger import get_logger
from app.middleware.logging_middleware import RequestLoggingMiddleware
from app.seeds.department_seed import seed_departments
from app.seeds.faculty_seed import seed_faculty
from app.seeds.user_seed import seed_users
from app.services.auth_service import AuthService

logger = get_logger("app.main")
auth_service = AuthService()


@asynccontextmanager
async def lifespan(_: FastAPI):
    logger.info("=== ResolveNow starting up | env=%s ===", settings.app_env)
    try:
        await connect_to_mongo()
        logger.info("MongoDB connected: db=%s", settings.mongodb_db_name)
        await initialize_database()
        logger.info("Database collections initialised")
        await seed_departments()
        logger.info("Department seed complete")
        await seed_users()
        logger.info("User seed complete")
        await seed_faculty()
        logger.info("Faculty seed complete")
        await auth_service.ensure_initial_admin()
        logger.info("Initial admin check complete")
    except Exception as exc:
        logger.critical("Startup failed: %s", repr(exc), exc_info=True)
        raise

    logger.info("=== ResolveNow is ready | host=%s port=%d ===", settings.host, settings.port)
    try:
        yield
    finally:
        logger.info("=== ResolveNow shutting down ===")
        await close_mongo_connection()
        logger.info("MongoDB connection closed")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    debug=settings.debug,
    lifespan=lifespan,
)

# ── Middleware (order matters: logging wraps everything) ───────────────────
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ────────────────────────────────────────────────────────────────
app.include_router(auth_router, prefix=settings.api_prefix)
app.include_router(admin_router, prefix=settings.api_prefix)
app.include_router(complaint_router, prefix="/api/v1/complaints", tags=["Complaints"])


@app.get("/", tags=["Health"])
async def root() -> dict[str, str]:
    logger.debug("Health root endpoint hit")
    return {"message": f"{settings.app_name} API is running"}


@app.get("/health", tags=["Health"])
async def health_check() -> dict[str, str]:
    logger.debug("Health check endpoint hit")
    return {"status": "ok", "environment": settings.app_env}


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )
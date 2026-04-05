import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from pydantic_settings import BaseSettings



# Use backend directory as base for .env
BASE_DIR = Path(__file__).resolve().parent.parent.parent
ENV_FILE = BASE_DIR / ".env"


def load_env_file(env_path: Path = ENV_FILE) -> None:
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        cleaned_value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key.strip(), cleaned_value)


def get_bool_env(key: str, default: bool) -> bool:
    value = os.getenv(key)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def get_int_env(key: str, default: int) -> int:
    value = os.getenv(key)
    if value is None:
        return default
    return int(value)


def get_list_env(key: str, default: str) -> list[str]:
    raw_value = os.getenv(key, default)
    return [item.strip() for item in raw_value.split(",") if item.strip()]


def get_required_env(key: str) -> str:
    value = os.getenv(key)
    if value is None or not value.strip():
        raise ValueError(f"Missing required environment variable: {key}")
    return value.strip()


@dataclass(frozen=True)
class Settings:
    app_name: str
    app_version: str
    app_env: str
    debug: bool
    api_prefix: str
    host: str
    port: int
    frontend_url: str
    cors_origins: list[str]
    mongodb_uri: str
    mongodb_db_name: str
    jwt_secret_key: str
    refresh_token_secret_key: str
    jwt_algorithm: str
    access_token_expire_minutes: int
    refresh_token_expire_days: int
    initial_admin_name: str
    initial_admin_email: str
    initial_admin_password: str
    smtp_host: str
    smtp_port: int
    smtp_username: str
    smtp_password: str
    smtp_from_email: str
    smtp_from_name: str
    aws_access_key_id: str
    aws_secret_access_key: str
    aws_region: str
    s3_bucket_name: str


@lru_cache
def get_settings() -> Settings:
    load_env_file()
    return Settings(
        app_name=os.getenv("APP_NAME", "Complaint Management System"),
        app_version=os.getenv("APP_VERSION", "1.0.0"),
        app_env=os.getenv("APP_ENV", "development"),
        debug=get_bool_env("DEBUG", True),
        api_prefix=os.getenv("API_PREFIX", "/api/v1"),
        host=os.getenv("HOST", "0.0.0.0"),
        port=get_int_env("PORT", 8000),
        frontend_url=os.getenv("FRONTEND_URL", "http://localhost:5173"),
        cors_origins=get_list_env(
            "BACKEND_CORS_ORIGINS",
            "http://localhost:3000,http://127.0.0.1:3000,http://localhost:5173,http://127.0.0.1:5173",
        ),
        mongodb_uri=get_required_env("MONGODB_URI"),
        mongodb_db_name=os.getenv("MONGODB_DB_NAME", "complaint_management_db"),
        jwt_secret_key=get_required_env("JWT_SECRET_KEY"),
        refresh_token_secret_key=get_required_env("REFRESH_TOKEN_SECRET_KEY"),
        jwt_algorithm=os.getenv("JWT_ALGORITHM", "HS256"),
        access_token_expire_minutes=get_int_env("ACCESS_TOKEN_EXPIRE_MINUTES", 30),
        refresh_token_expire_days=get_int_env("REFRESH_TOKEN_EXPIRE_DAYS", 7),
        initial_admin_name=os.getenv("INITIAL_ADMIN_NAME", "").strip(),
        initial_admin_email=os.getenv("INITIAL_ADMIN_EMAIL", "").strip(),
        initial_admin_password=os.getenv("INITIAL_ADMIN_PASSWORD", "").strip(),
        smtp_host=os.getenv("SMTP_HOST", "smtp.gmail.com"),
        smtp_port=get_int_env("SMTP_PORT", 587),
        smtp_username=os.getenv("SMTP_USERNAME", ""),
        smtp_password=os.getenv("SMTP_PASSWORD", ""),
        smtp_from_email=os.getenv("SMTP_FROM_EMAIL", "noreply@example.com"),
        smtp_from_name=os.getenv("SMTP_FROM_NAME", "Complaint Management System"),
        aws_access_key_id=os.getenv("aws_access_key_id", ""),
        aws_secret_access_key=os.getenv("aws_secret_access_key", ""),
        aws_region=os.getenv("aws_region", "ap-south-1"),
        s3_bucket_name=os.getenv("s3_bucket_name", "complaint-management-files"),
    )


settings = get_settings()

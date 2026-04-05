from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from app.config.security import decode_token
from app.models.user_model import UserRole, UserStatus
from app.repositories.user_repository import UserRepository


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login-oauth")


async def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    try:
        payload = decode_token(token, token_type="access")
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token.",
        ) from exc

    user_repository = UserRepository()
    user = await user_repository.find_by_id(payload["sub"])
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found.",
        )

    if not user.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive.",
        )

    user_status = user.get("user_status")
    if user_status and user_status != UserStatus.ACTIVE.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is not active.",
        )

    return user


def require_roles(*allowed_roles: UserRole):
    async def dependency(current_user: dict = Depends(get_current_user)) -> dict:
        allowed_values = {role.value for role in allowed_roles}
        if current_user.get("role") not in allowed_values:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to perform this action.",
            )
        return current_user

    return dependency


get_current_admin = require_roles(UserRole.ADMIN)
get_current_faculty_user = require_roles(UserRole.FACULTY)

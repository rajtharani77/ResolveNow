from datetime import datetime, timedelta

from fastapi import HTTPException, status

from app.config.email import send_verification_email
from app.config.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    generate_email_verification_token,
    hash_email_verification_token,
    hash_password,
    hash_refresh_token,
    verify_password,
)
from app.config.settings import settings
from app.core.logger import get_logger
from app.models.user_model import UserRole, UserStatus
from app.repositories.user_repository import UserRepository
from app.schemas.auth_schema import (
    AdminCreateRequest,
    AuthUserResponse,
    LoginResponse,
    LogoutResponse,
    RegisterResponse,
    UserLoginRequest,
    UserRegisterRequest,
    VerifyEmailResponse,
)

logger = get_logger("service.auth")


class AuthService:
    def __init__(self) -> None:
        self.user_repository = UserRepository()

    @staticmethod
    def _resolve_user_status(user: dict) -> str:
        stored_status = user.get("user_status")
        if stored_status:
            return stored_status
        if not user.get("is_email_verified"):
            return UserStatus.PENDING_EMAIL_VERIFICATION.value
        return UserStatus.ACTIVE.value

    @staticmethod
    def _map_user_response(user: dict) -> AuthUserResponse:
        return AuthUserResponse(
            id=str(user["_id"]),
            name=user["name"],
            email=user["email"],
            role=user["role"],
            user_status=AuthService._resolve_user_status(user),
            is_email_verified=user["is_email_verified"],
            created_at=user["created_at"],
        )

    async def create_admin_account(
        self,
        *,
        name: str,
        email: str,
        password: str,
        bootstrap: bool = False,
    ) -> AuthUserResponse:
        normalized_email = email.lower()
        existing_user = await self.user_repository.find_by_email(normalized_email)
        if existing_user:
            if bootstrap and existing_user.get("role") == UserRole.ADMIN.value:
                logger.info("Bootstrap admin already exists: email=%s", normalized_email)
                return self._map_user_response(existing_user)
            logger.warning("Admin creation failed – email already in use: email=%s", normalized_email)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A user with this email already exists.",
            )

        current_time = datetime.utcnow()
        admin_document = {
            "name": name,
            "email": normalized_email,
            "password_hash": hash_password(password),
            "role": UserRole.ADMIN.value,
            "user_status": UserStatus.ACTIVE.value,
            "is_email_verified": True,
            "is_active": True,
            "email_verification": None,
            "refresh_tokens": [],
            "created_at": current_time,
            "updated_at": current_time,
        }
        created_admin = await self.user_repository.create_user(admin_document)
        logger.info("Admin account created: email=%s id=%s", normalized_email, str(created_admin["_id"]))
        return self._map_user_response(created_admin)

    async def ensure_initial_admin(self) -> None:
        if not (
            settings.initial_admin_name
            and settings.initial_admin_email
            and settings.initial_admin_password
        ):
            logger.debug("No initial admin env vars set – skipping bootstrap")
            return

        logger.info("Ensuring initial admin account: email=%s", settings.initial_admin_email)
        await self.create_admin_account(
            name=settings.initial_admin_name,
            email=settings.initial_admin_email,
            password=settings.initial_admin_password,
            bootstrap=True,
        )

    async def create_admin_by_admin(self, payload: AdminCreateRequest) -> AuthUserResponse:
        logger.info("Admin-created admin account request: email=%s", payload.email)
        return await self.create_admin_account(
            name=payload.name,
            email=payload.email,
            password=payload.password,
        )

    async def _issue_tokens(self, user: dict) -> tuple[str, str]:
        current_time = datetime.utcnow()
        access_token = create_access_token(
            subject=str(user["_id"]),
            extra_claims={"email": user["email"], "role": user["role"]},
        )
        refresh_token = create_refresh_token(
            subject=str(user["_id"]),
            extra_claims={"email": user["email"], "role": user["role"]},
        )
        refresh_payload = decode_token(refresh_token, token_type="refresh")
        await self.user_repository.append_refresh_token(
            user["_id"],
            {
                "token_hash": hash_refresh_token(refresh_token),
                "expires_at": datetime.utcfromtimestamp(refresh_payload["exp"]),
                "created_at": current_time,
                "revoked_at": None,
                "last_used_at": None,
            },
        )
        logger.debug("Tokens issued for user: id=%s role=%s", str(user["_id"]), user["role"])
        return access_token, refresh_token

    async def register_user(self, payload: UserRegisterRequest) -> RegisterResponse:
        logger.info("Registration attempt: email=%s role=%s", payload.email, payload.role)
        existing_user = await self.user_repository.find_by_email(payload.email.lower())
        if existing_user:
            logger.warning("Registration failed – email already in use: email=%s", payload.email)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A user with this email already exists.",
            )

        if payload.role not in {UserRole.STUDENT, UserRole.FACULTY}:
            logger.warning("Registration failed – unsupported role: role=%s", payload.role)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only student and faculty registrations are supported.",
            )

        verification_token = generate_email_verification_token()
        current_time = datetime.utcnow()
        user_document = {
            "name": payload.name,
            "email": payload.email.lower(),
            "password_hash": hash_password(payload.password),
            "role": payload.role.value,
            "user_status": UserStatus.PENDING_EMAIL_VERIFICATION.value,
            "is_email_verified": False,
            "is_active": True,
            "email_verification": {
                "token_hash": hash_email_verification_token(verification_token),
                "expires_at": current_time + timedelta(hours=24),
                "sent_at": current_time,
                "verified_at": None,
            },
            "refresh_tokens": [],
            "created_at": current_time,
            "updated_at": current_time,
        }

        created_user = await self.user_repository.create_user(user_document)
        logger.info(
            "User registered: id=%s email=%s role=%s",
            str(created_user["_id"]),
            created_user["email"],
            created_user["role"],
        )

        email_sent = send_verification_email(
            recipient=created_user["email"],
            recipient_name=created_user["name"],
            verification_token=verification_token,
        )
        logger.debug("Verification email sent=%s to=%s", email_sent, created_user["email"])

        return RegisterResponse(
            message="Registration successful! A verification link has been sent to your email. Please verify your account to continue.",
            user=self._map_user_response(created_user),
            verification_email_sent=email_sent,
            verification_token=verification_token if settings.debug else None,
        )

    async def verify_email(self, token: str) -> VerifyEmailResponse:
        logger.info("Email verification attempt")
        user = await self.user_repository.find_by_verification_token_hash(
            hash_email_verification_token(token)
        )
        if not user:
            logger.warning("Email verification failed – invalid token")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid verification token.",
            )

        verification_object = user.get("email_verification") or {}
        expires_at = verification_object.get("expires_at")
        if expires_at is None or expires_at < datetime.utcnow():
            logger.warning("Email verification failed – expired token: email=%s", user.get("email"))
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Verification token has expired.",
            )

        if user.get("is_email_verified"):
            current_status = self._resolve_user_status(user)
            logger.info("Email already verified: email=%s status=%s", user.get("email"), current_status)
            if current_status == UserStatus.PENDING_APPROVAL.value:
                return VerifyEmailResponse(
                    message="Email is already verified. Your faculty account is still waiting for admin approval."
                )
            return VerifyEmailResponse(message="Email is already verified.")

        now = datetime.utcnow()
        user_role = user.get("role")
        next_status = (
            UserStatus.PENDING_APPROVAL.value
            if user_role == UserRole.FACULTY.value
            else UserStatus.ACTIVE.value
        )
        await self.user_repository.update_user(
            user["_id"],
            {
                "is_email_verified": True,
                "user_status": next_status,
                "updated_at": now,
                "email_verification.verified_at": now,
            },
        )
        logger.info(
            "Email verified: email=%s role=%s new_status=%s",
            user.get("email"),
            user_role,
            next_status,
        )

        if next_status == UserStatus.PENDING_APPROVAL.value:
            return VerifyEmailResponse(
                message="Email verified successfully. Your faculty account is pending admin approval."
            )
        return VerifyEmailResponse(
            message="Email verified successfully. Your student account is now active."
        )

    async def login_user(self, payload: UserLoginRequest) -> LoginResponse:
        logger.info("Login attempt: email=%s", payload.email)
        user = await self.user_repository.find_by_email(payload.email.lower())
        if not user or not verify_password(payload.password, user["password_hash"]):
            logger.warning("Login failed – invalid credentials: email=%s", payload.email)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password.",
            )

        if not user.get("is_email_verified"):
            logger.warning("Login blocked – email not verified: email=%s", payload.email)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Please verify your email before logging in.",
            )

        user_status = self._resolve_user_status(user)
        if user_status != UserStatus.ACTIVE.value:
            logger.warning(
                "Login blocked – account not active: email=%s status=%s",
                payload.email,
                user_status,
            )
            if user_status == UserStatus.PENDING_APPROVAL.value:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Your faculty account is pending admin approval.",
                )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Your account is not active yet.",
            )

        if not user.get("is_active", True):
            logger.warning("Login blocked – account inactive: email=%s", payload.email)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This account is inactive.",
            )

        await self.user_repository.clear_expired_refresh_tokens(user["_id"], datetime.utcnow())
        access_token, refresh_token = await self._issue_tokens(user)
        logger.info(
            "Login successful: id=%s email=%s role=%s",
            str(user["_id"]),
            user["email"],
            user["role"],
        )
        return LoginResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            user=self._map_user_response(user),
        )

    async def refresh_access_token(self, refresh_token: str) -> LoginResponse:
        logger.debug("Token refresh attempt")
        try:
            payload = decode_token(refresh_token, token_type="refresh")
        except Exception as exc:
            logger.warning("Token refresh failed – invalid/expired token: %s", repr(exc))
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token.",
            ) from exc

        user = await self.user_repository.find_by_id(payload["sub"])
        if not user:
            logger.warning("Token refresh failed – user not found: sub=%s", payload["sub"])
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found for this refresh token.",
            )

        if self._resolve_user_status(user) != UserStatus.ACTIVE.value:
            logger.warning("Token refresh blocked – account not active: id=%s", str(user["_id"]))
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Your account is not active.",
            )

        stored_token_hash = hash_refresh_token(refresh_token)
        matching_session = next(
            (
                session
                for session in user.get("refresh_tokens", [])
                if session.get("token_hash") == stored_token_hash
            ),
            None,
        )
        if matching_session is None or matching_session.get("revoked_at") is not None:
            logger.warning("Token refresh failed – token revoked or not found: id=%s", str(user["_id"]))
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token has been revoked.",
            )

        expires_at = matching_session.get("expires_at")
        if expires_at is None or expires_at < datetime.utcnow():
            logger.warning("Token refresh failed – token expired: id=%s", str(user["_id"]))
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token has expired.",
            )

        revoked_at = datetime.utcnow()
        await self.user_repository.mark_refresh_token_used(user["_id"], stored_token_hash, revoked_at)
        await self.user_repository.revoke_refresh_token(user["_id"], stored_token_hash, revoked_at)
        await self.user_repository.clear_expired_refresh_tokens(user["_id"], revoked_at)
        access_token, new_refresh_token = await self._issue_tokens(user)
        logger.info("Token refreshed successfully: id=%s", str(user["_id"]))
        return LoginResponse(
            access_token=access_token,
            refresh_token=new_refresh_token,
            user=self._map_user_response(user),
        )

    async def logout_user(self, refresh_token: str) -> LogoutResponse:
        logger.debug("Logout attempt")
        try:
            payload = decode_token(refresh_token, token_type="refresh")
        except Exception as exc:
            logger.warning("Logout failed – invalid/expired token: %s", repr(exc))
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token.",
            ) from exc

        user = await self.user_repository.find_by_id(payload["sub"])
        if not user:
            logger.warning("Logout failed – user not found: sub=%s", payload["sub"])
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found for this refresh token.",
            )

        await self.user_repository.revoke_refresh_token(
            user["_id"],
            hash_refresh_token(refresh_token),
            datetime.utcnow(),
        )
        await self.user_repository.clear_expired_refresh_tokens(user["_id"], datetime.utcnow())
        logger.info("Logout successful: id=%s email=%s", str(user["_id"]), user.get("email"))
        return LogoutResponse(message="Logged out successfully.")
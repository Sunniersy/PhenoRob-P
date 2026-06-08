import json
import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from backend.app.errors import ConflictError
from backend.app.models import RefreshToken, Role, User
from shared.security import (
    create_refresh_token,
    decode_token,
    encode_token,
    hash_password,
    verify_password,
    verify_refresh_token,
)

logger = logging.getLogger(__name__)


class AuthService:
    def __init__(self, db, config):
        self.db = db
        self.config = config

    def ensure_roles(self) -> None:
        session = self.db.session()
        try:
            self._ensure_roles_with_retry(session)
        finally:
            session.close()

    def bootstrap_admin(self, username: str, password: str) -> dict:
        session = self.db.session()
        try:
            if self._has_users(session):
                raise ConflictError("bootstrap admin already exists")

            roles = self._ensure_roles_for_session(session)
            user = User(
                username=username,
                password_hash=hash_password(password),
                role_id=roles["admin"].id,
                is_active=True,
                must_change_password=False,
            )
            session.add(user)
            session.commit()
            session.refresh(user)
            return self._build_auth_response(user)
        finally:
            session.close()

    def sync_demo_admin(self, username: str, password: str) -> dict:
        session = self.db.session()
        try:
            if not username.strip() or not password:
                raise ValueError("username and password are required")

            roles = self._ensure_roles_for_session(session)
            user = session.scalar(select(User).where(User.username == username))
            if user:
                if user.role.name != "admin":
                    raise ValueError("configured demo admin username belongs to a non-admin user")
                user.password_hash = hash_password(password)
                user.is_active = True
                user.must_change_password = False
            else:
                user = User(
                    username=username,
                    password_hash=hash_password(password),
                    role_id=roles["admin"].id,
                    is_active=True,
                    must_change_password=False,
                )
                session.add(user)

            session.commit()
            session.refresh(user)
            return self._build_auth_response(user)
        finally:
            session.close()

    def login(self, username: str, password: str) -> dict | None:
        session = self.db.session()
        try:
            user = session.scalar(select(User).where(User.username == username))
            if not user or not user.is_active or not verify_password(user.password_hash, password):
                logger.warning(json.dumps({
                    "event": "login_failed",
                    "username": username,
                    "reason": "invalid_credentials",
                }, ensure_ascii=False))
                return None
            logger.info(json.dumps({
                "event": "login_success",
                "user_id": user.id,
                "username": user.username,
                "role": user.role.name,
            }, ensure_ascii=False))
            return self._build_auth_response(user)
        finally:
            session.close()

    def current_user(self, token: str) -> dict:
        claims = decode_token(token, self.config["JWT_SECRET"])
        if claims.get("type") == "refresh":
            from jwt import InvalidTokenError
            raise InvalidTokenError("refresh tokens cannot be used for authentication")
        session = self.db.session()
        try:
            user = session.get(User, claims["sub"])
            if not user:
                raise ValueError("user not found")
            if not user.is_active:
                raise ValueError("user is inactive")
            return self.serialize_user(user)
        finally:
            session.close()

    def get_user_by_id(self, user_id: int) -> dict:
        session = self.db.session()
        try:
            user = session.get(User, user_id)
            if not user:
                raise ValueError("user not found")
            if not user.is_active:
                raise ValueError("user is inactive")
            return self.serialize_user(user)
        finally:
            session.close()

    def has_users(self) -> bool:
        session = self.db.session()
        try:
            return self._has_users(session)
        finally:
            session.close()

    @staticmethod
    def _has_users(session) -> bool:
        return bool(session.scalar(select(func.count(User.id))))

    @staticmethod
    def _ensure_roles_for_session(session) -> dict[str, Role]:
        roles = {role.name: role for role in session.scalars(select(Role)).all()}
        for role_name in ("admin", "operator"):
            if role_name not in roles:
                role = Role(name=role_name)
                session.add(role)
                session.flush()
                roles[role_name] = role
        return roles

    @staticmethod
    def _ensure_roles_with_retry(session) -> dict[str, Role]:
        try:
            roles = AuthService._ensure_roles_for_session(session)
            session.commit()
            return roles
        except IntegrityError:
            session.rollback()
            roles = {role.name: role for role in session.scalars(select(Role)).all()}
            missing_roles = {"admin", "operator"} - set(roles)
            if missing_roles:
                raise
            return roles

    def _build_auth_response(self, user: User) -> dict:
        # Serialize user first (accesses lazy-loaded role) while original session is open
        user_data = self.serialize_user(user)
        payload = {"sub": user.id, "username": user.username, "role": user_data["role"]}
        access_token = encode_token(payload, self.config["JWT_SECRET"])
        refresh_token_str = create_refresh_token(payload, self.config["JWT_SECRET"])

        session = self.db.session()
        try:
            rt = RefreshToken(
                token=refresh_token_str,
                user_id=user.id,
                expires_at=datetime.now(timezone.utc) + timedelta(days=7),
            )
            session.add(rt)
            session.commit()
        finally:
            session.close()

        return {
            "token": access_token,
            "refresh_token": refresh_token_str,
            "user": user_data,
        }

    def refresh_access_token(self, refresh_token_str: str) -> dict | None:
        """Validate a refresh token and issue a new access token + refresh token pair."""
        try:
            claims = verify_refresh_token(refresh_token_str, self.config["JWT_SECRET"])
        except Exception:
            return None

        session = self.db.session()
        try:
            rt = session.scalar(
                select(RefreshToken).where(
                    RefreshToken.token == refresh_token_str,
                    RefreshToken.revoked == False,  # noqa: E712
                )
            )
            if not rt:
                return None
            if rt.expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
                return None

            user = session.get(User, claims["sub"])
            if not user or not user.is_active:
                return None

            # Revoke the old refresh token (rotation)
            rt.revoked = True
            session.commit()

            logger.info(json.dumps({
                "event": "token_refresh",
                "user_id": user.id,
                "username": user.username,
            }, ensure_ascii=False))

            return self._build_auth_response(user)
        finally:
            session.close()

    def logout(self, refresh_token_str: str | None) -> None:
        """Revoke the given refresh token (or all tokens for the user if none provided)."""
        if not refresh_token_str:
            return
        session = self.db.session()
        try:
            rt = session.scalar(
                select(RefreshToken).where(
                    RefreshToken.token == refresh_token_str,
                    RefreshToken.revoked == False,  # noqa: E712
                )
            )
            if rt:
                rt.revoked = True
                session.commit()
                logger.info(json.dumps({
                    "event": "logout",
                    "user_id": rt.user_id,
                }, ensure_ascii=False))
        finally:
            session.close()

    @staticmethod
    def serialize_user(user: User) -> dict:
        return {
            "id": user.id,
            "username": user.username,
            "role": user.role.name,
            "is_active": user.is_active,
            "must_change_password": user.must_change_password,
        }

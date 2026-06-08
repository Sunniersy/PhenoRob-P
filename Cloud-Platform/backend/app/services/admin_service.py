from sqlalchemy import func, select

from backend.app.models import Role, User
from backend.app.pagination import build_paginated_payload
from backend.app.validators import escape_like_wildcards
from shared.security import hash_password


class AdminService:
    def __init__(self, db, config):
        self.db = db
        self.config = config

    def list_users(self, filters: dict | None = None) -> dict:
        filters = filters or {}
        with self.db.session_scope() as session:
            query = select(User)
            if filters.get("q"):
                query = query.where(User.username.ilike(f"%{escape_like_wildcards(filters['q'])}%"))
            if filters.get("status") == "active":
                query = query.where(User.is_active.is_(True))
            elif filters.get("status") == "inactive":
                query = query.where(User.is_active.is_(False))
            total = session.scalar(select(func.count()).select_from(query.subquery())) or 0
            users = session.scalars(
                query.order_by(User.created_at.asc())
                .offset((filters["page"] - 1) * filters["page_size"])
                .limit(filters["page_size"])
            ).all()
            return build_paginated_payload(
                [self.serialize_user(user) for user in users], total, filters["page"], filters["page_size"]
            )

    def list_roles(self, filters: dict | None = None) -> dict:
        filters = filters or {}
        with self.db.session_scope() as session:
            roles = session.scalars(select(Role).order_by(Role.created_at.asc())).all()
            items = [{"id": role.id, "name": role.name, "created_at": role.created_at.isoformat()} for role in roles]
            return build_paginated_payload(items, len(items), filters.get("page", 1), filters.get("page_size", len(items) or 1))

    def create_user(self, payload: dict) -> dict:
        with self.db.session_scope() as session:
            username = (payload.get("username") or "").strip()
            password = payload.get("password") or ""
            role_name = (payload.get("role") or "").strip()
            if not username or not password or not role_name:
                raise ValueError("username, password and role are required")
            if session.scalar(select(User).where(User.username == username)):
                raise ValueError("username already exists")
            role = session.scalar(select(Role).where(Role.name == role_name))
            if not role:
                raise ValueError("role not found")
            user = User(
                username=username,
                password_hash=hash_password(password),
                role_id=role.id,
                is_active=True,
                must_change_password=True,
            )
            session.add(user)
            session.commit()
            session.refresh(user)
            return self.serialize_user(user)

    def update_user_status(self, user_id: str, is_active: bool) -> dict:
        with self.db.session_scope() as session:
            user = session.get(User, user_id)
            if not user:
                raise ValueError("user not found")
            if not is_active:
                admin_count = session.scalar(
                    select(func.count(User.id)).where(User.is_active.is_(True), User.role.has(name="admin"))
                )
                if user.role.name == "admin" and admin_count <= 1:
                    raise ValueError("cannot disable the last active admin")
            user.is_active = is_active
            session.commit()
            return self.serialize_user(user)

    def reset_password(self, user_id: str, password: str) -> dict:
        with self.db.session_scope() as session:
            user = session.get(User, user_id)
            if not user:
                raise ValueError("user not found")
            user.password_hash = hash_password(password)
            user.must_change_password = False
            session.commit()
            return self.serialize_user(user)

    @staticmethod
    def serialize_user(user: User) -> dict:
        return {
            "id": user.id,
            "username": user.username,
            "role": user.role.name,
            "is_active": user.is_active,
            "must_change_password": user.must_change_password,
            "created_at": user.created_at.isoformat(),
        }

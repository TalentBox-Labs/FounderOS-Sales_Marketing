from __future__ import annotations

import uuid
from enum import Enum
from typing import Optional

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from revenue_os.auth import get_current_user
from revenue_os.database import get_db
from revenue_os.models.user import User


class Role(str, Enum):
    ADMIN = "admin"
    MANAGER = "manager"
    MEMBER = "member"
    VIEWER = "viewer"


ROLE_HIERARCHY = {
    Role.ADMIN: 100,
    Role.MANAGER: 80,
    Role.MEMBER: 50,
    Role.VIEWER: 10,
}

ROLE_PERMISSIONS = {
    Role.ADMIN: {
        "contacts": ["create", "read", "update", "delete", "export", "import"],
        "deals": ["create", "read", "update", "delete", "export", "import"],
        "companies": ["create", "read", "update", "delete"],
        "tasks": ["create", "read", "update", "delete", "assign"],
        "workflows": ["create", "read", "update", "delete"],
        "reports": ["create", "read", "export"],
        "settings": ["read", "update"],
        "users": ["create", "read", "update", "delete"],
    },
    Role.MANAGER: {
        "contacts": ["create", "read", "update", "delete", "export", "import"],
        "deals": ["create", "read", "update", "delete", "export"],
        "companies": ["create", "read", "update", "delete"],
        "tasks": ["create", "read", "update", "delete", "assign"],
        "workflows": ["create", "read", "update"],
        "reports": ["create", "read", "export"],
        "settings": ["read"],
        "users": ["read"],
    },
    Role.MEMBER: {
        "contacts": ["create", "read", "update", "export"],
        "deals": ["create", "read", "update", "export"],
        "companies": ["create", "read", "update"],
        "tasks": ["create", "read", "update"],
        "workflows": ["read"],
        "reports": ["read"],
        "settings": [],
        "users": [],
    },
    Role.VIEWER: {
        "contacts": ["read"],
        "deals": ["read"],
        "companies": ["read"],
        "tasks": ["read"],
        "workflows": ["read"],
        "reports": ["read"],
        "settings": [],
        "users": [],
    },
}


def has_permission(user: User, resource: str, action: str) -> bool:
    try:
        role = Role(user.role)
    except ValueError:
        role = Role.MEMBER
    perms = ROLE_PERMISSIONS.get(role, {})
    return action in perms.get(resource, [])


def require_permission(resource: str, action: str):
    async def permission_dep(current_user: User = Depends(get_current_user)):
        if not has_permission(current_user, resource, action):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{current_user.role}' requires '{action}' on '{resource}'",
            )
        return current_user
    return permission_dep


def require_role(min_role: str):
    async def role_dep(current_user: User = Depends(get_current_user)):
        try:
            user_role = Role(current_user.role)
            min_role_enum = Role(min_role)
        except ValueError:
            raise HTTPException(status_code=403, detail="Invalid role")
        if ROLE_HIERARCHY.get(user_role, 0) < ROLE_HIERARCHY.get(min_role_enum, 0):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires at least '{min_role}' role, user has '{current_user.role}'",
            )
        return current_user
    return role_dep


def can_access_entity(
    db: Session,
    user: User,
    entity_type: str,
    entity_id: uuid.UUID,
    owner_id: Optional[uuid.UUID] = None,
) -> bool:
    try:
        role = Role(user.role)
    except ValueError:
        role = Role.MEMBER

    if role == Role.ADMIN or role == Role.MANAGER:
        return True

    if owner_id and str(owner_id) == str(user.id):
        return True

    return False

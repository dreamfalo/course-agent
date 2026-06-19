"""
权限控制模块 - 基于角色的访问控制 (RBAC)
区分学生(student)和管理员(admin)角色
拦截跨用户数据查询、批量删除等高风险操作
"""
import functools
import logging
from enum import Enum
from typing import Set, Callable, Any, Dict, Optional

logger = logging.getLogger(__name__)


class Role(str, Enum):
    STUDENT = "student"
    ADMIN = "admin"


ROLE_PERMISSIONS: Dict[Role, Set[str]] = {
    Role.STUDENT: {
        "schedule:add_own",
        "schedule:update_own",
        "schedule:delete_own",
        "schedule:query_own",
        "schedule:export_own",
        "rag:ingest_own",
        "rag:search_own",
        "rag:list_own",
        "rag:delete_own",
        "task:generate_own",
        "task:list_own",
        "task:adjust_own",
        "file:upload_own",
        "file:download_own",
        "file:list_own",
        "file:delete_own",
    },
    Role.ADMIN: {
        "schedule:add_own",
        "schedule:update_own",
        "schedule:delete_own",
        "schedule:query_own",
        "schedule:export_own",
        "schedule:add_any",
        "schedule:update_any",
        "schedule:delete_any",
        "schedule:query_any",
        "schedule:export_any",
        "rag:ingest_own",
        "rag:search_own",
        "rag:list_own",
        "rag:delete_own",
        "rag:ingest_any",
        "rag:search_any",
        "rag:list_any",
        "rag:delete_any",
        "task:generate_own",
        "task:list_own",
        "task:adjust_own",
        "task:generate_any",
        "task:list_any",
        "task:adjust_any",
        "file:upload_own",
        "file:download_own",
        "file:list_own",
        "file:delete_own",
        "file:upload_any",
        "file:download_any",
        "file:list_any",
        "file:delete_any",
        "file:cleanup",
    },
}

HIGH_RISK_ACTIONS: Set[str] = {
    "schedule:delete_any",
    "file:delete_any",
    "file:cleanup",
    "rag:delete_any",
}


class AccessControl:
    """访问控制器"""

    def __init__(self, settings: Optional[Any] = None):
        self._allowed_roles = (Role.STUDENT, Role.ADMIN)

    def has_permission(self, role: Role, action: str) -> bool:
        """检查角色是否拥有某项操作权限"""
        if role not in ROLE_PERMISSIONS:
            logger.warning(f"Unknown role: {role}")
            return False
        return action in ROLE_PERMISSIONS[role]

    def is_high_risk(self, action: str) -> bool:
        """判断操作是否为高风险"""
        return action in HIGH_RISK_ACTIONS

    def validate_user_access(
        self,
        role: Role,
        action: str,
        target_user_id: Optional[str] = None,
        current_user_id: Optional[str] = None,
    ) -> bool:
        """验证用户操作权限，拦截跨用户数据访问"""
        if not self.has_permission(role, action):
            logger.warning(f"Permission denied: role={role.value}, action={action}")
            return False
        if action.endswith("_own") and target_user_id and current_user_id:
            if target_user_id != current_user_id:
                logger.warning(
                    f"Cross-user access blocked: current={current_user_id}, target={target_user_id}"
                )
                return False
        if self.is_high_risk(action) and role != Role.ADMIN:
            logger.warning(f"High-risk action blocked for non-admin: {action}")
            return False
        return True

    def require_permission(self, action: str):
        """权限校验装饰器"""

        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            def wrapper(self_or_cls, *args, **kwargs):
                role_str = kwargs.pop("_role", getattr(self_or_cls, "_role", None))
                if role_str is None:
                    raise PermissionError("No role provided for authorization")
                role = Role(role_str) if isinstance(role_str, str) else role_str
                user_id = kwargs.pop("_user_id", getattr(self_or_cls, "_user_id", None))
                target_user_id = kwargs.get("user_id") or kwargs.get("target_user_id")
                if not self.validate_user_access(role, action, target_user_id, user_id):
                    raise PermissionError(
                        f"Access denied: role={role}, action={action}"
                    )
                return func(self_or_cls, *args, **kwargs)

            return wrapper

        return decorator

    def get_role_permissions(self, role: Role) -> Set[str]:
        """获取角色的所有权限"""
        return ROLE_PERMISSIONS.get(role, set())

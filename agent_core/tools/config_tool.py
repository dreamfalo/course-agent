"""
ConfigTool - 系统配置管理工具
功能：DeepSeek API密钥/模型参数、向量库配置、用户个人信息读写
"""
import json
import logging
from typing import Type, Optional, Dict, Any

from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class ConfigInput(BaseModel):
    """配置工具输入 Schema"""
    action: str = Field(description="操作类型: get(读取配置), set(写入配置), list_all(列出全部), update_user(修改用户信息)")
    config_key: Optional[str] = Field(default=None, description="配置键名，如 deepseek.temperature / chroma.chunk_size / user.name")
    config_value: Optional[str] = Field(default=None, description="配置值")
    config_type: Optional[str] = Field(default=None, description="配置类型: string, json, int, bool, secret")
    category: Optional[str] = Field(default=None, description="配置分类: general, llm, vector, storage, notification")
    user_id: Optional[str] = Field(default=None, description="用户ID")


class ConfigTool(BaseTool):
    """系统配置读写：DeepSeek参数、向量库、用户信息"""

    name: str = "config_tool"
    description: str = (
        "系统配置管理工具。读取和写入 DeepSeek 模型参数（temperature、top_p、上下文长度等）、"
        "Chroma 向量库配置（存储路径、分片大小）、用户个人信息（姓名、身份等）。"
        "操作类型: get(读取), set(写入), list_all(列出全部配置), update_user(修改用户信息)。"
    )
    args_schema: Type[BaseModel] = ConfigInput

    # 内存配置存储
    _configs: Dict[str, Dict[str, Any]] = {
        "deepseek.temperature": {"value": "0.7", "type": "float", "category": "llm", "description": "模型温度参数"},
        "deepseek.top_p": {"value": "0.9", "type": "float", "category": "llm", "description": "核采样参数"},
        "deepseek.max_tokens": {"value": "4096", "type": "int", "category": "llm", "description": "最大输出token"},
        "deepseek.model": {"value": "deepseek-chat", "type": "string", "category": "llm", "description": "当前模型"},
        "chroma.persist_dir": {"value": "./chroma_db", "type": "string", "category": "vector", "description": "向量库存储路径"},
        "chroma.chunk_size": {"value": "500", "type": "int", "category": "vector", "description": "文档分块大小"},
        "chroma.chunk_overlap": {"value": "50", "type": "int", "category": "vector", "description": "分块重叠大小"},
        "chroma.collection_name": {"value": "course_documents", "type": "string", "category": "vector", "description": "集合名称"},
        "storage.bucket": {"value": "course-files", "type": "string", "category": "storage", "description": "MinIO存储桶"},
        "storage.temp_ttl": {"value": "24", "type": "int", "category": "storage", "description": "临时文件有效期(小时)"},
        "notification.enabled": {"value": "true", "type": "bool", "category": "notification", "description": "消息提醒开关"},
        "notification.time": {"value": "08:00", "type": "string", "category": "notification", "description": "每日提醒时间"},
    }

    # 用户信息存储
    _users: Dict[str, Dict[str, Any]] = {}

    class Config:
        arbitrary_types_allowed = True

    def _run(
        self,
        action: str,
        config_key: Optional[str] = None,
        config_value: Optional[str] = None,
        config_type: Optional[str] = None,
        category: Optional[str] = None,
        user_id: Optional[str] = None,
        _user_id: Optional[str] = None,
        _role: Optional[str] = None,
    ) -> str:
        uid = _user_id or user_id or "default_user"

        try:
            if action == "get":
                return self._get_config(config_key)
            elif action == "set":
                return self._set_config(config_key, config_value, config_type, category, uid, _role)
            elif action == "list_all":
                return self._list_all(category)
            elif action == "update_user":
                return self._update_user(uid, config_key, config_value)
            else:
                return json.dumps({"success": False, "error": f"未知操作: {action}"}, ensure_ascii=False)
        except Exception as e:
            logger.exception(f"ConfigTool failed: {e}")
            return json.dumps({"success": False, "error": str(e)}, ensure_ascii=False)

    def _get_config(self, config_key: Optional[str]) -> str:
        if not config_key:
            return json.dumps({"success": False, "error": "请指定 config_key"}, ensure_ascii=False)
        cfg = self._configs.get(config_key)
        if cfg:
            return json.dumps({"success": True, "config": {"key": config_key, **cfg}}, ensure_ascii=False)
        return json.dumps({"success": False, "error": f"配置 {config_key} 不存在"}, ensure_ascii=False)

    def _set_config(self, config_key: Optional[str], config_value: Optional[str],
                    config_type: Optional[str], category: Optional[str], uid: str, _role: Optional[str]) -> str:
        if not config_key or config_value is None:
            return json.dumps({"success": False, "error": "config_key 和 config_value 必填"}, ensure_ascii=False)
        # 管理员可写全部配置，学生只能写用户相关配置
        if _role not in ("admin",) and not config_key.startswith("user."):
            return json.dumps({"success": False, "error": "权限不足，只有管理员可修改系统配置"}, ensure_ascii=False)

        existing = self._configs.get(config_key, {})
        self._configs[config_key] = {
            "value": config_value,
            "type": config_type or existing.get("type", "string"),
            "category": category or existing.get("category", "general"),
            "description": existing.get("description", ""),
        }
        logger.info(f"Config set: {config_key} = {config_value} by {uid}")
        return json.dumps({
            "success": True,
            "msg": f"配置 {config_key} 已更新",
            "config": {"key": config_key, **self._configs[config_key]},
        }, ensure_ascii=False)

    def _list_all(self, category: Optional[str]) -> str:
        items = self._configs
        if category:
            items = {k: v for k, v in items.items() if v.get("category") == category}
        return json.dumps({
            "success": True,
            "count": len(items),
            "configs": [{"key": k, **v} for k, v in items.items()],
        }, ensure_ascii=False)

    def _update_user(self, uid: str, config_key: Optional[str], config_value: Optional[str]) -> str:
        """更新用户个人信息（姓名、手机等）"""
        if uid not in self._users:
            self._users[uid] = {"name": uid, "role": "student", "phone": ""}
        if config_key and config_value is not None:
            self._users[uid][config_key] = config_value
        return json.dumps({
            "success": True,
            "msg": "用户信息已更新",
            "user": self._users[uid],
        }, ensure_ascii=False)
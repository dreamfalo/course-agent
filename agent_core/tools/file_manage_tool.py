"""
FileManageTool - 课件文件管理工具
功能：课件上传、临时文件存储、过期文件自动清理
"""
import json
import logging
import os
import shutil
import tempfile
from typing import Type, Optional, List, Dict, Any
from datetime import datetime, timedelta

from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field
from minio import Minio
from minio.error import S3Error

from agent_core.config import MinIOConfig
from agent_core.auth.access_control import AccessControl, Role

logger = logging.getLogger(__name__)


class FileManageInput(BaseModel):
    """文件管理工具输入 Schema"""
    action: str = Field(description="操作类型: upload(上传), download(下载), list(列出), delete(删除), cleanup(清理过期)")
    file_path: Optional[str] = Field(default=None, description="本地文件路径（上传）")
    object_name: Optional[str] = Field(default=None, description="MinIO中的对象名（下载/删除）")
    course_id: Optional[str] = Field(default=None, description="关联课程ID")
    user_id: Optional[str] = Field(default=None, description="用户ID")
    is_temp: bool = Field(default=False, description="是否为临时文件")
    ttl_hours: Optional[int] = Field(default=None, description="临时文件有效期（小时）")


class FileManageTool(BaseTool):
    """课件上传、临时文件存储、过期文件自动清理"""

    name: str = "file_manage_tool"
    description: str = (
        "课件文件管理工具。支持课件上传到 MinIO、下载、列出文件、删除文件，"
        "以及临时文件的过期自动清理。"
        "操作类型: upload(上传课件), download(获取下载链接), list(列出文件), "
        "delete(删除文件), cleanup(清理过期临时文件)。"
    )
    args_schema: Type[BaseModel] = FileManageInput

    _minio_config: MinIOConfig
    _client: Optional[Minio] = None
    _access_control: AccessControl = AccessControl()
    _file_metadata: Dict[str, Dict[str, Any]] = {}
    _local_temp_dir: str

    class Config:
        arbitrary_types_allowed = True

    def __init__(self, minio_config: Optional[MinIOConfig] = None, **kwargs):
        super().__init__(**kwargs)
        self._minio_config = minio_config or MinIOConfig()
        self._init_client()
        self._local_temp_dir = os.path.join(tempfile.gettempdir(), "course_agent_uploads")
        os.makedirs(self._local_temp_dir, exist_ok=True)

    def _init_client(self):
        """初始化 MinIO 客户端"""
        try:
            self._client = Minio(
                endpoint=self._minio_config.endpoint,
                access_key=self._minio_config.access_key,
                secret_key=self._minio_config.secret_key,
                secure=self._minio_config.secure,
            )
            self._client._http.headers["Connection"] = "close"
            import socket
            default_timeout = socket.getdefaulttimeout()
            socket.setdefaulttimeout(3)
            self._client.bucket_exists(self._minio_config.bucket_name)
            socket.setdefaulttimeout(default_timeout)
            logger.info(f"MinIO client initialized: {self._minio_config.endpoint}")
        except Exception as e:
            logger.warning(f"MinIO client init failed (will use local fallback): {e}")
            self._client = None

    def _run(
        self,
        action: str,
        file_path: Optional[str] = None,
        object_name: Optional[str] = None,
        course_id: Optional[str] = None,
        user_id: Optional[str] = None,
        is_temp: bool = False,
        ttl_hours: Optional[int] = None,
        _role: str = "student",
        _user_id: str = "",
        **kwargs,
    ) -> str:
        """执行文件管理操作"""
        uid = user_id or _user_id
        try:
            if action == "upload":
                return self._upload_file(file_path, course_id, uid, is_temp, ttl_hours)
            elif action == "download":
                return self._download_file(object_name, uid)
            elif action == "list":
                return self._list_files(uid, course_id)
            elif action == "delete":
                return self._delete_file(object_name, uid, _role)
            elif action == "cleanup":
                return self._cleanup_expired(_role)
            else:
                return json.dumps({"error": f"Unknown action: {action}"}, ensure_ascii=False)
        except Exception as e:
            logger.exception(f"FileManageTool error: {e}")
            return json.dumps({"error": str(e)}, ensure_ascii=False)

    def _upload_file(
        self, file_path: Optional[str], course_id: Optional[str],
        uid: str, is_temp: bool, ttl_hours: Optional[int],
    ) -> str:
        """上传文件到 MinIO 或本地存储"""
        if not file_path or not os.path.exists(file_path):
            return json.dumps({"error": f"File not found: {file_path}"}, ensure_ascii=False)

        file_name = os.path.basename(file_path)
        obj_name = f"{uid}/{course_id or 'general'}/{datetime.now().strftime('%Y%m%d%H%M%S')}_{file_name}"

        effective_ttl = ttl_hours or (self._minio_config.temp_file_ttl_hours if is_temp else None)
        expires_at = (
            (datetime.now() + timedelta(hours=effective_ttl)).isoformat()
            if effective_ttl else None
        )

        # 使用 MinIO 或本地回退
        if self._client:
            try:
                with open(file_path, "rb") as f:
                    file_stat = os.stat(file_path)
                    self._client.put_object(
                        bucket_name=self._minio_config.bucket_name,
                        object_name=obj_name,
                        data=f,
                        length=file_stat.st_size,
                        content_type="application/octet-stream",
                    )
                logger.info(f"File uploaded to MinIO: {obj_name}")
                storage = "minio"
            except S3Error as e:
                logger.error(f"MinIO upload failed: {e}")
                return json.dumps({"error": f"Upload failed: {e}"}, ensure_ascii=False)
        else:
            dest_path = os.path.join(self._local_temp_dir, obj_name.replace("/", "_"))
            os.makedirs(os.path.dirname(dest_path), exist_ok=True)
            shutil.copy2(file_path, dest_path)
            storage = "local"
            logger.info(f"File saved locally: {dest_path}")

        meta = {
            "object_name": obj_name,
            "file_name": file_name,
            "course_id": course_id,
            "user_id": uid,
            "is_temp": is_temp,
            "ttl_hours": effective_ttl,
            "expires_at": expires_at,
            "storage": storage,
            "uploaded_at": datetime.now().isoformat(),
        }
        self._file_metadata[obj_name] = meta

        return json.dumps({"success": True, "file": meta}, ensure_ascii=False)

    def _download_file(self, object_name: Optional[str], uid: str) -> str:
        """获取文件下载信息"""
        if not object_name:
            return json.dumps({"error": "object_name is required"}, ensure_ascii=False)
        meta = self._file_metadata.get(object_name)
        if not meta:
            return json.dumps({"error": f"File not found: {object_name}"}, ensure_ascii=False)
        if meta.get("expires_at") and datetime.now() > datetime.fromisoformat(meta["expires_at"]):
            return json.dumps({"error": "File has expired"}, ensure_ascii=False)

        if self._client and meta.get("storage") == "minio":
            try:
                url = self._client.presigned_get_object(
                    bucket_name=self._minio_config.bucket_name,
                    object_name=object_name,
                    expires=timedelta(hours=1),
                )
                return json.dumps({
                    "success": True,
                    "download_url": url,
                    "file": meta,
                }, ensure_ascii=False)
            except S3Error as e:
                return json.dumps({"error": f"Download failed: {e}"}, ensure_ascii=False)
        else:
            local_path = os.path.join(
                self._local_temp_dir, object_name.replace("/", "_")
            )
            return json.dumps({
                "success": True,
                "local_path": local_path,
                "file": meta,
            }, ensure_ascii=False)

    def _list_files(self, uid: str, course_id: Optional[str] = None) -> str:
        """列出用户文件"""
        files = []
        for name, meta in self._file_metadata.items():
            if meta.get("user_id") != uid:
                continue
            if course_id and meta.get("course_id") != course_id:
                continue
            is_expired = (
                meta.get("expires_at")
                and datetime.now() > datetime.fromisoformat(meta["expires_at"])
            )
            files.append({**meta, "is_expired": is_expired})
        return json.dumps({
            "success": True,
            "total": len(files),
            "files": files,
        }, ensure_ascii=False)

    def _delete_file(self, object_name: Optional[str], uid: str, role: str) -> str:
        """删除文件"""
        if not object_name:
            return json.dumps({"error": "object_name is required"}, ensure_ascii=False)
        meta = self._file_metadata.get(object_name)
        if not meta:
            return json.dumps({"error": f"File not found: {object_name}"}, ensure_ascii=False)

        if meta["user_id"] != uid and role != "admin":
            return json.dumps({"error": "Permission denied: cannot delete other user's file"}, ensure_ascii=False)

        if self._client and meta.get("storage") == "minio":
            try:
                self._client.remove_object(
                    bucket_name=self._minio_config.bucket_name,
                    object_name=object_name,
                )
            except S3Error as e:
                logger.warning(f"MinIO delete warning: {e}")
        else:
            local_path = os.path.join(self._local_temp_dir, object_name.replace("/", "_"))
            if os.path.exists(local_path):
                os.remove(local_path)

        del self._file_metadata[object_name]
        logger.info(f"File deleted: {object_name}")
        return json.dumps({"success": True, "deleted": object_name}, ensure_ascii=False)

    def _cleanup_expired(self, role: str) -> str:
        """清理过期临时文件（仅管理员可执行）"""
        if role != "admin":
            return json.dumps({"error": "Only admin can perform cleanup"}, ensure_ascii=False)

        now = datetime.now()
        expired = []
        for name, meta in list(self._file_metadata.items()):
            if meta.get("expires_at") and now > datetime.fromisoformat(meta["expires_at"]):
                expired.append(name)
                if self._client and meta.get("storage") == "minio":
                    try:
                        self._client.remove_object(
                            bucket_name=self._minio_config.bucket_name,
                            object_name=name,
                        )
                    except S3Error:
                        pass
                else:
                    local_path = os.path.join(self._local_temp_dir, name.replace("/", "_"))
                    if os.path.exists(local_path):
                        os.remove(local_path)
                del self._file_metadata[name]

        logger.info(f"Cleanup: {len(expired)} expired files removed")
        return json.dumps({
            "success": True,
            "cleaned": len(expired),
            "expired_files": expired,
        }, ensure_ascii=False)


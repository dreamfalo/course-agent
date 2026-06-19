"""
MinIO 文件存储工具类
课件上传、导出文件存储、预签名下载URL、过期清理
"""
import logging
import os
from datetime import timedelta
from typing import Optional, BinaryIO

from django.conf import settings
from minio import Minio
from minio.error import S3Error

logger = logging.getLogger(__name__)


class MinIOClient:
    """MinIO 客户端单例"""

    _instance: Optional[Minio] = None
    _disabled: bool = False  # 标记 MinIO 不可用，避免重复重试
    """MinIO 客户端单例"""

    _instance: Optional[Minio] = None

    @classmethod
    def get_client(cls) -> Optional[Minio]:
        if cls._instance is None:
            try:
                cls._instance = Minio(
                    endpoint=settings.MINIO_ENDPOINT,
                    access_key=settings.MINIO_ACCESS_KEY,
                    secret_key=settings.MINIO_SECRET_KEY,
                    secure=settings.MINIO_SECURE,
                )
                import socket
                old = socket.getdefaulttimeout()
                socket.setdefaulttimeout(3)
                bucket = settings.MINIO_BUCKET
                if not cls._instance.bucket_exists(bucket):
                    cls._instance.make_bucket(bucket)
                socket.setdefaulttimeout(old)
                logger.info(f"MinIO connected: {settings.MINIO_ENDPOINT}")
            except Exception as e:
                logger.warning(f"MinIO unavailable: {e}")
                cls._instance = None
        return cls._instance

    @classmethod
    def upload_file(cls, file_path: str, object_name: str, content_type: str = "application/octet-stream") -> bool:
        """上传本地文件到 MinIO"""
        client = cls.get_client()
        if not client:
            return False
        try:
            client.fput_object(
                bucket_name=settings.MINIO_BUCKET,
                object_name=object_name,
                file_path=file_path,
                content_type=content_type,
            )
            logger.info(f"Uploaded: {object_name}")
            return True
        except S3Error as e:
            logger.error(f"MinIO upload failed: {e}")
            return False

    @classmethod
    def upload_stream(cls, data: BinaryIO, object_name: str, length: int, content_type: str = "application/octet-stream") -> bool:
        """上传数据流到 MinIO"""
        client = cls.get_client()
        if not client:
            return False
        try:
            client.put_object(
                bucket_name=settings.MINIO_BUCKET,
                object_name=object_name,
                data=data,
                length=length,
                content_type=content_type,
            )
            logger.info(f"Stream uploaded: {object_name}")
            return True
        except S3Error as e:
            logger.error(f"MinIO stream upload failed: {e}")
            return False

    @classmethod
    def get_presigned_url(cls, object_name: str, expires_hours: int = 1) -> Optional[str]:
        """获取预签名下载 URL"""
        client = cls.get_client()
        if not client:
            return None
        try:
            return client.presigned_get_object(
                bucket_name=settings.MINIO_BUCKET,
                object_name=object_name,
                expires=timedelta(hours=expires_hours),
            )
        except S3Error as e:
            logger.error(f"MinIO presigned URL failed: {e}")
            return None

    @classmethod
    def delete_file(cls, object_name: str) -> bool:
        """删除 MinIO 文件"""
        client = cls.get_client()
        if not client:
            return False
        try:
            client.remove_object(settings.MINIO_BUCKET, object_name)
            logger.info(f"Deleted: {object_name}")
            return True
        except S3Error as e:
            logger.error(f"MinIO delete failed: {e}")
            return False

    @classmethod
    def file_exists(cls, object_name: str) -> bool:
        """检查文件是否存在"""
        client = cls.get_client()
        if not client:
            return False
        try:
            client.stat_object(settings.MINIO_BUCKET, object_name)
            return True
        except S3Error:
            return False

from django.db import models
from django.contrib.auth.models import AbstractUser


class SystemUser(AbstractUser):
    """扩展用户模型"""
    role = models.CharField("角色", max_length=16, default="student", choices=[
        ("student", "学生"), ("admin", "管理员")
    ])
    avatar = models.URLField("头像URL", blank=True)
    phone = models.CharField("手机号", max_length=20, blank=True)

    class Meta:
        db_table = "system_user"


class SystemConfig(models.Model):
    """系统配置表"""
    config_key = models.CharField("配置键", max_length=128, unique=True)
    config_value = models.TextField("配置值")
    config_type = models.CharField("配置类型", max_length=32, default="string", choices=[
        ("string", "字符串"), ("json", "JSON"), ("int", "整数"), ("bool", "布尔"), ("secret", "密钥")
    ])
    category = models.CharField("分类", max_length=32, default="general", choices=[
        ("general", "通用"), ("llm", "大模型"), ("vector", "向量库"), ("storage", "存储"), ("notification", "通知")
    ])
    description = models.CharField("描述", max_length=256, blank=True)
    is_active = models.BooleanField("是否启用", default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "system_config"
        ordering = ["category", "config_key"]

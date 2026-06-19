"""
Django 4.2 课程助手后端全局配置
"""
import os as _os
from pathlib import Path

# 自动加载 .env 文件
try:
    from dotenv import load_dotenv
    _env_path = Path(__file__).resolve().parent.parent / ".env"
    load_dotenv(_env_path)
except ImportError:
    pass

from datetime import timedelta

BASE_DIR = Path(__file__).resolve().parent.parent
VUE_DIST = BASE_DIR / "frontend" / "dist"

SECRET_KEY = _os.environ.get("DJANGO_SECRET_KEY", "course-agent-secret-key-dev")

DEBUG = _os.environ.get("DJANGO_DEBUG", "True").lower() == "true"

ALLOWED_HOSTS = ["*"]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "rest_framework_simplejwt",
    "corsheaders",
    "drf_spectacular",
    "schedule",
    "knowledge",
    "task",
    "config",
    "agent_chat",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "course_agent_backend.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [VUE_DIST],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "course_agent_backend.wsgi.application"

# ── 数据库：有 MYSQL_PASSWORD 用 MySQL，否则 SQLite ──
_mysql_pass = _os.environ.get("MYSQL_PASSWORD", "")
if _mysql_pass:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.mysql",
            "NAME": _os.environ.get("MYSQL_DATABASE", "course_agent_db"),
            "USER": _os.environ.get("MYSQL_USER", "root"),
            "PASSWORD": _mysql_pass,
            "HOST": _os.environ.get("MYSQL_HOST", "localhost"),
            "PORT": _os.environ.get("MYSQL_PORT", "3306"),
            "OPTIONS": {"charset": "utf8mb4"},
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

AUTH_USER_MODEL = "config.SystemUser"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", "OPTIONS": {"min_length": 6}},
]

LANGUAGE_CODE = "zh-hans"
TIME_ZONE = "Asia/Shanghai"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# CORS
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True

# DRF
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": ["rest_framework_simplejwt.authentication.JWTAuthentication"],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
    "DEFAULT_PAGINATION_CLASS": "course_agent_backend.pagination.StandardPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "EXCEPTION_HANDLER": "course_agent_backend.exceptions.custom_exception_handler",
    "DATETIME_FORMAT": "%Y-%m-%d %H:%M:%S",
    "DATE_FORMAT": "%Y-%m-%d",
    "TIME_FORMAT": "%H:%M",
}

# JWT
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(hours=24),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "AUTH_HEADER_TYPES": ("Bearer",),
}

# drf-spectacular
SPECTACULAR_SETTINGS = {
    "TITLE": "智能课程助手 API",
    "VERSION": "1.0.0",
    "DESCRIPTION": "基于 LangChain + DeepSeek + Chroma 的智能课程助手后端服务",
}

# MinIO
MINIO_ENDPOINT = _os.environ.get("MINIO_ENDPOINT", "localhost:9000")
MINIO_ACCESS_KEY = _os.environ.get("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = _os.environ.get("MINIO_SECRET_KEY", "minioadmin")
MINIO_BUCKET = _os.environ.get("MINIO_BUCKET", "course-files")
MINIO_SECURE = _os.environ.get("MINIO_SECURE", "False").lower() == "true"

# 文件上传
MEDIA_ROOT = BASE_DIR / "media"
MEDIA_URL = "/media/"
FILE_UPLOAD_MAX_MEMORY_SIZE = 50 * 1024 * 1024

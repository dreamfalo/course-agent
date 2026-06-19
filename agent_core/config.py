"""
agent_core 全局配置模块
统一管理 DeepSeek LLM、Chroma 向量库、MinIO 文件存储、MySQL 对话记录等参数
"""
import os
from dataclasses import dataclass, field
from typing import Optional, Dict, Any


@dataclass
class DeepSeekConfig:
    """DeepSeek API 配置"""
    api_key: str = field(default_factory=lambda: os.getenv("DEEPSEEK_API_KEY", ""))
    api_base: str = field(default_factory=lambda: os.getenv("DEEPSEEK_API_BASE", "https://api.deepseek.com/v1"))
    chat_model: str = "deepseek-chat"
    code_model: str = "deepseek-coder"
    default_temperature: float = 0.7
    default_max_tokens: int = 4096
    default_top_p: float = 0.9
    max_context_length: int = 32000
    request_timeout: int = 60


@dataclass
class ChromaConfig:
    """Chroma 向量数据库配置"""
    persist_directory: str = field(default_factory=lambda: os.getenv("CHROMA_PERSIST_DIR", "./chroma_db"))
    collection_name: str = "course_documents"
    embedding_model: str = "text-embedding-3-small"
    embedding_dim: int = 1536
    embedding_provider: str = "openai"
    chunk_size: int = 500
    chunk_overlap: int = 50


@dataclass
class MinIOConfig:
    """MinIO 文件存储配置"""
    endpoint: str = field(default_factory=lambda: os.getenv("MINIO_ENDPOINT", "localhost:9000"))
    access_key: str = field(default_factory=lambda: os.getenv("MINIO_ACCESS_KEY", "minioadmin"))
    secret_key: str = field(default_factory=lambda: os.getenv("MINIO_SECRET_KEY", "minioadmin"))
    bucket_name: str = "course-files"
    secure: bool = False
    temp_file_ttl_hours: int = 24
    auto_cleanup_interval_hours: int = 6


@dataclass
class MySQLConfig:
    """MySQL 数据库配置"""
    host: str = field(default_factory=lambda: os.getenv("MYSQL_HOST", "localhost"))
    port: int = int(os.getenv("MYSQL_PORT", "3306"))
    user: str = field(default_factory=lambda: os.getenv("MYSQL_USER", "root"))
    password: str = field(default_factory=lambda: os.getenv("MYSQL_PASSWORD", ""))
    database: str = field(default_factory=lambda: os.getenv("MYSQL_DATABASE", "course_agent"))
    pool_size: int = 5
    pool_recycle: int = 3600


@dataclass
class AgentConfig:
    """Agent 调度器配置"""
    max_iterations: int = 5
    max_execution_time: int = 60
    verbose: bool = False
    early_stopping_method: str = "force"
    allowed_roles: tuple = ("student", "admin")
    default_role: str = "student"
    memory_max_token_limit: int = 4000


@dataclass
class Settings:
    """全局设置聚合"""
    deepseek: DeepSeekConfig = field(default_factory=DeepSeekConfig)
    chroma: ChromaConfig = field(default_factory=ChromaConfig)
    minio: MinIOConfig = field(default_factory=MinIOConfig)
    mysql: MySQLConfig = field(default_factory=MySQLConfig)
    agent: AgentConfig = field(default_factory=AgentConfig)

    @classmethod
    def from_env(cls) -> "Settings":
        """从环境变量加载配置"""
        return cls(
            deepseek=DeepSeekConfig(),
            chroma=ChromaConfig(),
            minio=MinIOConfig(),
            mysql=MySQLConfig(),
            agent=AgentConfig(),
        )

    def dict(self) -> Dict[str, Any]:
        """导出为字典"""
        return {
            "deepseek": {k: v for k, v in self.deepseek.__dict__.items() if not k.startswith("_")},
            "chroma": {k: v for k, v in self.chroma.__dict__.items() if not k.startswith("_")},
            "minio": {k: v for k, v in self.minio.__dict__.items() if not k.startswith("_")},
            "mysql": {k: v for k, v in self.mysql.__dict__.items() if not k.startswith("_")},
            "agent": {k: v for k, v in self.agent.__dict__.items() if not k.startswith("_")},
        }

"""
MemoryManager - 多轮对话记忆管理
基于 LangChain ConversationBufferMemory，对话记录持久存入 MySQL
"""
import json
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime

import pymysql
from langchain_classic.memory import ConversationBufferMemory
from langchain_core.messages import HumanMessage, AIMessage

from agent_core.config import MySQLConfig

logger = logging.getLogger(__name__)


class MemoryManager:
    """对话记忆管理器：LangChain BufferMemory + MySQL 持久化"""

    def __init__(self, mysql_config: Optional[MySQLConfig] = None, max_token_limit: int = 4000):
        self._mysql_config = mysql_config or MySQLConfig()
        self._max_token_limit = max_token_limit
        self._connection: Optional[pymysql.Connection] = None
        self._memories: Dict[str, ConversationBufferMemory] = {}
        self._init_db()

    def _init_db(self):
        """初始化 MySQL 连接与对话记录表"""
        try:
            self._connection = pymysql.connect(
                host=self._mysql_config.host,
                port=self._mysql_config.port,
                user=self._mysql_config.user,
                password=self._mysql_config.password,
                database=self._mysql_config.database,
                charset="utf8mb4",
                autocommit=True,
            )
            with self._connection.cursor() as cursor:
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS conversation_history (
                        id BIGINT AUTO_INCREMENT PRIMARY KEY,
                        session_id VARCHAR(128) NOT NULL,
                        user_id VARCHAR(64) NOT NULL,
                        role ENUM('user', 'assistant') NOT NULL,
                        content TEXT NOT NULL,
                        metadata JSON,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        INDEX idx_session (session_id),
                        INDEX idx_user (user_id),
                        INDEX idx_created (created_at)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                """)
            logger.info("MySQL conversation_history table ready")
        except pymysql.Error as e:
            logger.warning(f"MySQL connection failed, using in-memory only: {e}")
            self._connection = None

    def get_or_create_memory(
        self,
        session_id: str,
        user_id: str,
        memory_key: str = "chat_history",
    ) -> ConversationBufferMemory:
        """获取或创建对话记忆"""
        key = f"{user_id}:{session_id}"
        if key not in self._memories:
            self._memories[key] = ConversationBufferMemory(
                memory_key=memory_key,
                return_messages=True,
                max_token_limit=self._max_token_limit,
            )
            self._load_history(key, user_id, session_id)
        return self._memories[key]

    def _load_history(self, key: str, user_id: str, session_id: str):
        """从 MySQL 加载历史对话进 Memory"""
        if not self._connection:
            return
        try:
            with self._connection.cursor(pymysql.cursors.DictCursor) as cursor:
                cursor.execute(
                    "SELECT role, content FROM conversation_history "
                    "WHERE user_id=%s AND session_id=%s ORDER BY created_at ASC LIMIT 50",
                    (user_id, session_id),
                )
                rows = cursor.fetchall()
                for row in rows:
                    if row["role"] == "user":
                        self._memories[key].chat_memory.add_user_message(row["content"])
                    else:
                        self._memories[key].chat_memory.add_ai_message(row["content"])
                logger.info(f"Loaded {len(rows)} history records for {key}")
        except pymysql.Error as e:
            logger.warning(f"Failed to load history: {e}")

    def save_message(
        self,
        session_id: str,
        user_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """持久化单条对话到 MySQL"""
        if not self._connection:
            return
        try:
            with self._connection.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO conversation_history (session_id, user_id, role, content, metadata) "
                    "VALUES (%s, %s, %s, %s, %s)",
                    (session_id, user_id, role, content, json.dumps(metadata or {})),
                )
        except pymysql.Error as e:
            logger.warning(f"Failed to save message: {e}")

    def get_history(
        self,
        session_id: str,
        user_id: str,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """从 MySQL 查询历史对话"""
        if not self._connection:
            return []
        try:
            with self._connection.cursor(pymysql.cursors.DictCursor) as cursor:
                cursor.execute(
                    "SELECT id, role, content, created_at FROM conversation_history "
                    "WHERE session_id=%s AND user_id=%s ORDER BY created_at DESC LIMIT %s",
                    (session_id, user_id, limit),
                )
                return list(cursor.fetchall())
        except pymysql.Error as e:
            logger.warning(f"Failed to get history: {e}")
            return []

    def clear_memory(self, session_id: str, user_id: str):
        """清除会话记忆"""
        key = f"{user_id}:{session_id}"
        if key in self._memories:
            self._memories[key].clear()
        if self._connection:
            try:
                with self._connection.cursor() as cursor:
                    cursor.execute(
                        "DELETE FROM conversation_history WHERE session_id=%s AND user_id=%s",
                        (session_id, user_id),
                    )
            except pymysql.Error as e:
                logger.warning(f"Failed to clear history: {e}")

    def list_sessions(self, user_id: str) -> List[Dict[str, Any]]:
        """列出用户所有会话"""
        if not self._connection:
            return []
        try:
            with self._connection.cursor(pymysql.cursors.DictCursor) as cursor:
                cursor.execute(
                    "SELECT session_id, MAX(created_at) as last_active, COUNT(*) as msg_count "
                    "FROM conversation_history WHERE user_id=%s "
                    "GROUP BY session_id ORDER BY last_active DESC",
                    (user_id,),
                )
                return list(cursor.fetchall())
        except pymysql.Error as e:
            logger.warning(f"Failed to list sessions: {e}")
            return []

    def close(self):
        """关闭数据库连接"""
        if self._connection:
            try:
                self._connection.close()
            except pymysql.Error:
                pass

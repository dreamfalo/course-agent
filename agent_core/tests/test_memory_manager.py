"""
MemoryManager 单元测试
测试对话记忆创建、持久化、历史加载、会话管理
"""
import unittest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent_core.config import MySQLConfig
from agent_core.agent.memory_manager import MemoryManager


class TestMemoryManager(unittest.TestCase):
    """MemoryManager 单元测试"""

    def setUp(self):
        self.manager = MemoryManager()
        self.uid = "user_mem_001"
        self.session_id = "session_test_001"

    def test_create_memory(self):
        """测试创建对话记忆"""
        memory = self.manager.get_or_create_memory(self.session_id, self.uid)
        self.assertIsNotNone(memory)
        self.assertEqual(memory.memory_key, "chat_history")

    def test_memory_persistence(self):
        """测试同一 session 复用记忆"""
        mem1 = self.manager.get_or_create_memory(self.session_id, self.uid)
        mem2 = self.manager.get_or_create_memory(self.session_id, self.uid)
        self.assertIs(mem1, mem2)

    def test_different_sessions(self):
        """测试不同会话的记忆隔离"""
        mem1 = self.manager.get_or_create_memory("session_a", self.uid)
        mem2 = self.manager.get_or_create_memory("session_b", self.uid)
        self.assertIsNot(mem1, mem2)

    def test_different_users(self):
        """测试不同用户记忆隔离"""
        mem1 = self.manager.get_or_create_memory(self.session_id, "user_a")
        mem2 = self.manager.get_or_create_memory(self.session_id, "user_b")
        self.assertIsNot(mem1, mem2)

    def test_add_and_retrieve_messages(self):
        """测试添加消息后可从记忆获取"""
        memory = self.manager.get_or_create_memory(self.session_id, self.uid)
        memory.chat_memory.add_user_message("用户消息1")
        memory.chat_memory.add_ai_message("助手回复1")
        messages = memory.chat_memory.messages
        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[0].content, "用户消息1")
        self.assertEqual(messages[1].content, "助手回复1")

    def test_save_message_to_db(self):
        """测试消息持久化（MySQL 不可用时静默回退）"""
        self.manager.save_message(self.session_id, self.uid, "user", "测试消息")
        # 不抛异常即为通过

    def test_clear_memory(self):
        """测试清除记忆"""
        memory = self.manager.get_or_create_memory(self.session_id, self.uid)
        memory.chat_memory.add_user_message("消息")
        self.manager.clear_memory(self.session_id, self.uid)
        self.assertEqual(len(memory.chat_memory.messages), 0)

    def test_list_sessions(self):
        """测试列出会话"""
        sessions = self.manager.list_sessions(self.uid)
        self.assertIsInstance(sessions, list)

    def test_close_connection(self):
        """测试关闭连接"""
        self.manager.close()
        self.assertIsNone(self.manager._connection)

    def test_get_history_returns_empty_when_no_db(self):
        """测试无数据库时返回空列表"""
        manager = MemoryManager()
        # 强制断开
        manager._connection = None
        history = manager.get_history(self.session_id, self.uid)
        self.assertEqual(history, [])


if __name__ == "__main__":
    unittest.main()

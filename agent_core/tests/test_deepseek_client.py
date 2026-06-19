"""
DeepSeekClient 单元测试
测试 LLM 封装、模型切换、参数配置、消息格式转换
"""
import unittest
from unittest.mock import MagicMock, patch

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent_core.config import DeepSeekConfig
from agent_core.llm.deepseek_client import DeepSeekClient
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage


class TestDeepSeekClient(unittest.TestCase):
    """DeepSeekClient 单元测试"""

    def setUp(self):
        self.config = DeepSeekConfig(
            api_key="test-key",
            api_base="https://api.deepseek.com/v1",
            chat_model="deepseek-chat",
            code_model="deepseek-coder",
            default_temperature=0.5,
            default_max_tokens=2048,
            default_top_p=0.8,
        )

    @patch("agent_core.llm.deepseek_client.OpenAI")
    def test_init_creates_openai_client(self, mock_openai):
        """测试初始化时创建 OpenAI 客户端"""
        client = DeepSeekClient(config=self.config)
        mock_openai.assert_called_once()
        call_kwargs = mock_openai.call_args.kwargs
        self.assertEqual(call_kwargs["api_key"], "test-key")
        self.assertEqual(call_kwargs["base_url"], "https://api.deepseek.com/v1")

    @patch("agent_core.llm.deepseek_client.OpenAI")
    def test_llm_type_is_deepseek(self, mock_openai):
        """测试 _llm_type 属性"""
        client = DeepSeekClient(config=self.config)
        self.assertEqual(client._llm_type, "deepseek")

    @patch("agent_core.llm.deepseek_client.OpenAI")
    def test_identifying_params(self, mock_openai):
        """测试识别参数"""
        client = DeepSeekClient(config=self.config)
        params = client._identifying_params
        self.assertEqual(params["model"], "deepseek-chat")
        self.assertEqual(params["temperature"], 0.5)
        self.assertEqual(params["max_tokens"], 2048)
        self.assertEqual(params["top_p"], 0.8)

    @patch("agent_core.llm.deepseek_client.OpenAI")
    def test_convert_messages_to_openai_format(self, mock_openai):
        """测试消息格式转换"""
        client = DeepSeekClient(config=self.config)
        messages = [
            SystemMessage(content="你是一个助手"),
            HumanMessage(content="你好"),
            AIMessage(content="你好，有什么可以帮助你的？"),
        ]
        result = client._convert_messages_to_openai_format(messages)
        self.assertEqual(len(result), 3)
        self.assertEqual(result[0]["role"], "system")
        self.assertEqual(result[0]["content"], "你是一个助手")
        self.assertEqual(result[1]["role"], "user")
        self.assertEqual(result[2]["role"], "assistant")

    @patch("agent_core.llm.deepseek_client.OpenAI")
    def test_switch_to_code_model(self, mock_openai):
        """测试切换到 Code 模型"""
        client = DeepSeekClient(config=self.config)
        client.switch_to_code_model()
        self.assertEqual(client.config.chat_model, "deepseek-coder")

    @patch("agent_core.llm.deepseek_client.OpenAI")
    def test_switch_to_chat_model(self, mock_openai):
        """测试切换到 Chat 模型"""
        client = DeepSeekClient(config=self.config)
        client.switch_to_code_model()
        client.switch_to_chat_model()
        self.assertEqual(client.config.chat_model, "deepseek-chat")

    @patch("agent_core.llm.deepseek_client.OpenAI")
    def test_chat_method_calls_generate(self, mock_openai):
        """测试 chat 便捷方法"""
        client = DeepSeekClient(config=self.config)
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message = MagicMock(content="你好，用户！")
        mock_response.choices[0].finish_reason = "stop"
        mock_response.usage = MagicMock(prompt_tokens=10, completion_tokens=5, total_tokens=15)
        client._client.chat.completions.create.return_value = mock_response

        result = client.chat("你好", system_prompt="你是助手", temperature=0.3)
        self.assertEqual(result, "你好，用户！")

    @patch("agent_core.llm.deepseek_client.OpenAI")
    def test_default_config_from_env(self, mock_openai):
        """测试从环境变量加载默认配置"""
        config = DeepSeekConfig()
        client = DeepSeekClient(config=config)
        self.assertIsNotNone(client.config.api_base)


class TestAccessControl(unittest.TestCase):
    """权限控制单元测试"""

    def setUp(self):
        from agent_core.auth.access_control import AccessControl, Role
        self.ac = AccessControl()
        self.Role = Role

    def test_student_has_own_permissions(self):
        """测试学生有自有数据操作权限"""
        self.assertTrue(self.ac.has_permission(self.Role.STUDENT, "schedule:query_own"))
        self.assertTrue(self.ac.has_permission(self.Role.STUDENT, "schedule:add_own"))

    def test_student_no_any_permissions(self):
        """测试学生无跨用户权限"""
        self.assertFalse(self.ac.has_permission(self.Role.STUDENT, "schedule:query_any"))

    def test_admin_has_all_permissions(self):
        """测试管理员拥有全部权限"""
        self.assertTrue(self.ac.has_permission(self.Role.ADMIN, "schedule:query_any"))
        self.assertTrue(self.ac.has_permission(self.Role.ADMIN, "file:cleanup"))

    def test_high_risk_actions(self):
        """测试高风险操作识别"""
        self.assertTrue(self.ac.is_high_risk("file:cleanup"))
        self.assertTrue(self.ac.is_high_risk("file:cleanup"))
        self.assertFalse(self.ac.is_high_risk("schedule:query_own"))

    def test_cross_user_access_blocked(self):
        """测试跨用户数据访问被拦截"""
        result = self.ac.validate_user_access(
            role=self.Role.STUDENT,
            action="schedule:query_own",
            target_user_id="user_b",
            current_user_id="user_a",
        )
        self.assertFalse(result)

    def test_admin_high_risk_allowed(self):
        """测试管理员可以执行高风险操作"""
        result = self.ac.validate_user_access(
            role=self.Role.ADMIN,
            action="schedule:delete_any",
        )
        self.assertTrue(result)

    def test_student_high_risk_blocked(self):
        """测试学生被拦截高风险操作"""
        result = self.ac.validate_user_access(
            role=self.Role.STUDENT,
            action="schedule:delete_any",
        )
        self.assertFalse(result)


if __name__ == "__main__":
    unittest.main()



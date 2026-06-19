"""
集成测试 - 自然语言指令验证 Agent 自主意图识别与工具调用
测试 CourseAgentCore 完整调度链路
"""
import json
import unittest
from unittest.mock import MagicMock, patch
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault("DEEPSEEK_API_KEY", "test-key")
os.environ.setdefault("OPENAI_API_KEY", "test-key")

from agent_core.config import Settings
from agent_core.agent.course_agent import CourseAgentCore


def _mock_invoke(return_data):
    """工厂函数：创建 mock executor"""
    mock_exec = MagicMock()
    mock_exec.invoke.return_value = return_data
    return mock_exec


class TestAgentIntegration(unittest.TestCase):
    """CourseAgentCore 集成测试"""

    @classmethod
    def setUpClass(cls):
        cls.agent = CourseAgentCore()

    def test_tools_registered(self):
        """4 个工具已正确注册"""
        tool_names = [t.name for t in self.agent.tools]
        self.assertIn("schedule_tool", tool_names)
        self.assertIn("rag_retrieve_tool", tool_names)
        self.assertIn("task_plan_tool", tool_names)
        self.assertIn("file_manage_tool", tool_names)
        self.assertEqual(len(tool_names), 4)

    def test_get_tools_info(self):
        """获取工具信息"""
        info = self.agent.get_tools_info()
        self.assertEqual(len(info), 4)

    def test_invalid_role_rejected(self):
        """无效角色被拒绝"""
        result = self.agent.chat("查看课表", user_id="u1", role="super_admin")
        self.assertFalse(result["success"])

    def test_direct_tool_call_schedule(self):
        """直接调用课表工具"""
        result = self.agent.direct_tool_call(
            tool_name="schedule_tool",
            action="add",
            user_id="test_direct",
            course_name="数据结构",
            weekday="周三",
            start_time="10:00",
            end_time="11:30",
        )
        self.assertTrue(result["success"])

    def test_direct_tool_call_permission_denied(self):
        """权限拒绝"""
        result = self.agent.direct_tool_call(
            tool_name="file_manage_tool",
            action="cleanup",
            user_id="test_user",
            role="student",
        )
        self.assertFalse(result["success"])

    def test_session_history(self):
        """会话历史"""
        history = self.agent.get_history("test_session", "test_user")
        self.assertIsInstance(history, list)

    def test_chat_with_mock(self):
        """模拟 Agent 对话（课表查询）"""
        self.agent.executor = _mock_invoke({
            "output": "已为您添加课程「高等数学」，周一08:00-09:30。",
            "intermediate_steps": [
                (MagicMock(tool="schedule_tool", tool_input={"action": "add"}), '{"success":true}'),
            ],
        })
        result = self.agent.chat("帮我添加周一8点到9点半的高等数学", user_id="s1")
        self.assertTrue(result["success"])
        self.assertEqual(result["tool_calls"][0]["tool"], "schedule_tool")

    def test_chat_rag_intent(self):
        """RAG 检索意图"""
        self.agent.executor = _mock_invoke({
            "output": "微积分资料检索结果如下...",
            "intermediate_steps": [
                (MagicMock(tool="rag_retrieve_tool", tool_input={"action": "search"}), "[]"),
            ],
        })
        result = self.agent.chat("搜索微积分相关课件", user_id="s1")
        self.assertEqual(result["tool_calls"][0]["tool"], "rag_retrieve_tool")

    def test_chat_task_plan_intent(self):
        """任务规划意图"""
        self.agent.executor = _mock_invoke({
            "output": "已生成25个学习任务。",
            "intermediate_steps": [
                (MagicMock(tool="task_plan_tool", tool_input={"action": "generate"}), "{}"),
            ],
        })
        result = self.agent.chat("根据课表生成学习计划", user_id="s1")
        self.assertEqual(result["tool_calls"][0]["tool"], "task_plan_tool")

    def test_chat_file_upload_intent(self):
        """文件上传意图"""
        self.agent.executor = _mock_invoke({
            "output": "已上传讲义。",
            "intermediate_steps": [
                (MagicMock(tool="file_manage_tool", tool_input={"action": "upload"}), "{}"),
            ],
        })
        result = self.agent.chat("上传数据结构讲义", user_id="s1")
        self.assertEqual(result["tool_calls"][0]["tool"], "file_manage_tool")


class TestNaturalLanguageIntentRecognition(unittest.TestCase):
    """自然语言意图识别场景测试"""

    test_cases = [
        ("帮我查一下周三有什么课", "schedule_tool"),
        ("加一门周一上午10点的线性代数", "schedule_tool"),
        ("把周二的英语课删掉", "schedule_tool"),
        ("把课表导出成Excel", "schedule_tool"),
        ("搜索人工智能相关课件", "rag_retrieve_tool"),
        ("上传PDF文件到高等数学课程", "file_manage_tool"),
        ("根据课表生成这周学习计划", "task_plan_tool"),
        ("调整学习计划把数学往后推", "task_plan_tool"),
        ("清理过期临时文件", "file_manage_tool"),
        ("列出所有已上传课件", "file_manage_tool"),
        ("找找微积分复习资料", "rag_retrieve_tool"),
    ]

    def test_intent_recognition(self):
        """验证多种自然语言指令的意图识别"""
        agent = CourseAgentCore()
        for utterance, expected_tool in self.test_cases:
            with self.subTest(utterance=utterance):
                agent.executor = _mock_invoke({
                    "output": f"[mock] {utterance}",
                    "intermediate_steps": [
                        (MagicMock(tool=expected_tool, tool_input={}), "{}"),
                    ],
                })
                result = agent.chat(utterance, user_id="test_user")
                self.assertTrue(result["success"])
                called_tool = result["tool_calls"][0]["tool"]
                self.assertEqual(
                    called_tool, expected_tool,
                    f"「{utterance}」期望 {expected_tool}，实际 {called_tool}"
                )


if __name__ == "__main__":
    unittest.main()

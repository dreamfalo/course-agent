"""
CourseAgentCore - 智能课程助手 Agent 主调度器
基于 LangChain AgentExecutor + 4 个标准工具 + ConversationBufferMemory
实现自主工具调用与意图识别
"""
import json
import logging
import uuid
from typing import Optional, Dict, Any, List, Tuple

from langchain_classic.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from agent_core.config import Settings, AgentConfig
from agent_core.llm.deepseek_client import DeepSeekClient
from agent_core.agent.memory_manager import MemoryManager
from agent_core.auth.access_control import AccessControl, Role
from agent_core.tools.schedule_tool import ScheduleTool
from agent_core.tools.rag_retrieve_tool import RAGRetrieveTool
from agent_core.tools.task_plan_tool import TaskPlanTool
from agent_core.tools.file_manage_tool import FileManageTool
from agent_core.tools.note_tool import NoteTool
from agent_core.tools.stat_tool import StatTool
from agent_core.tools.config_tool import ConfigTool

logger = logging.getLogger(__name__)


# Tool Calling Agent 系统提示词
COURSE_AGENT_SYSTEM = """你是智能课程助手，名为"课程小助手"。你可以使用工具帮助用户管理课程相关的所有事务。

你的能力包括：
1. **课表管理**：添加、修改、删除、查询课程，检查时间冲突，导出课表文件
2. **资料检索**：上传课件文档（PDF/Word/TXT），进行智能语义搜索
3. **任务规划**：根据课表自动生成学习计划，输出甘特图数据
4. **文件管理**：上传、下载、管理课件文件
5. **笔记管理**：创建、修改、删除、检索学习笔记，导出笔记文件
6. **数据统计**：统计每日学习时长，生成一周学习折线图，汇总课程与任务数据
7. **系统配置**：读写 DeepSeek 模型参数、向量库配置、用户个人信息

**重要规则：**
- 你必须使用工具来完成所有操作，不要凭空编造数据
- 操作前先确认用户身份
- 涉及用户数据时，使用参数 _role 和 _user_id 传递当前用户信息
- 如果用户的请求含糊不清，先询问具体信息再操作
- 返回结果时用中文友好地总结
- 遇到工具不可用时，如实告知用户并给出替代建议"""

COURSE_AGENT_PROMPT = ChatPromptTemplate.from_messages([
    ("system", COURSE_AGENT_SYSTEM),
    MessagesPlaceholder(variable_name="chat_history"),
    ("human", "{input}"),
    MessagesPlaceholder(variable_name="agent_scratchpad"),
])

class CourseAgentCore:
    """智能课程助手 Agent 核心调度器"""

    def __init__(self, settings: Optional[Settings] = None):
        self.settings = settings or Settings()
        self._init_components()

    def _init_components(self):
        """初始化所有组件"""
        # LLM 客户端
        self.llm = DeepSeekClient(config=self.settings.deepseek)

        # 访问控制
        self.access_control = AccessControl()

        # 记忆管理器
        self.memory_manager = MemoryManager(
            mysql_config=self.settings.mysql,
            max_token_limit=self.settings.agent.memory_max_token_limit,
        )

        # 4 个业务工具实例
        self.schedule_tool = ScheduleTool()
        self.rag_tool = RAGRetrieveTool(chroma_config=self.settings.chroma)
        self.task_plan_tool = TaskPlanTool()
        self.file_manage_tool = FileManageTool(minio_config=self.settings.minio)
        self.note_tool = NoteTool()
        self.stat_tool = StatTool()
        self.config_tool = ConfigTool()

        # 工具列表
        self.tools = [
            self.schedule_tool,
            self.rag_tool,
            self.task_plan_tool,
            self.file_manage_tool,
        ]

        # Agent Executor
        self.agent = create_tool_calling_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=COURSE_AGENT_PROMPT,
        )

        self.executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            verbose=self.settings.agent.verbose,
            max_iterations=self.settings.agent.max_iterations,
            max_execution_time=self.settings.agent.max_execution_time,
            early_stopping_method=self.settings.agent.early_stopping_method,
            handle_parsing_errors=True,
        )

        logger.info("CourseAgentCore initialized with %d tools", len(self.tools))

    def get_tools_info(self) -> List[Dict[str, str]]:
        """获取已注册工具列表"""
        return [
            {"name": t.name, "description": t.description[:80] + "..."}
            for t in self.tools
        ]

    def chat(
        self,
        user_message: str,
        user_id: str = "default_user",
        session_id: Optional[str] = None,
        role: str = "student",
    ) -> Dict[str, Any]:
        """核心对话接口：接收自然语言，自动路由到对应工具

        Args:
            user_message: 用户自然语言输入
            user_id: 用户唯一标识
            session_id: 会话ID（不传则自动生成）
            role: 用户角色 (student/admin)

        Returns:
            {
                "success": bool,
                "response": str,
                "session_id": str,
                "tool_calls": [...],
            }
        """
        if not session_id:
            session_id = str(uuid.uuid4())[:8]

        # 角色校验
        if role not in self.settings.agent.allowed_roles:
            return {
                "success": False,
                "response": f"角色 '{role}' 不被允许，支持的角色: {self.settings.agent.allowed_roles}",
                "session_id": session_id,
            }

        role_enum = Role(role)

        # 获取或创建对话记忆
        memory = self.memory_manager.get_or_create_memory(session_id, user_id)

        # 将用户上下文注入消息
        enriched_message = (
            f"（当前用户: {user_id}, 角色: {role}）\n"
            f"{user_message}"
        )

        # 保存用户消息到记忆
        memory.chat_memory.add_user_message(user_message)
        self.memory_manager.save_message(session_id, user_id, "user", user_message)

        try:
            import signal
            import functools

            def _invoke():
                return self.executor.invoke({
                    "input": enriched_message,
                    "chat_history": memory.chat_memory.messages,
                })

            result = _invoke()
            response_text = result.get("output", "抱歉，我无法处理您的请求。")
            intermediate_steps = result.get("intermediate_steps", [])
            tool_calls = []
            for step in intermediate_steps:
                if len(step) >= 2:
                    action = step[0]
                    tool_calls.append({
                        "tool": action.tool,
                        "input": action.tool_input,
                        "output": str(step[1])[:200],
                    })

            # 保存助手回复
            memory.chat_memory.add_ai_message(response_text)
            self.memory_manager.save_message(session_id, user_id, "assistant", response_text)

            return {
                "success": True,
                "response": response_text,
                "session_id": session_id,
                "tool_calls": tool_calls,
            }
        except Exception as e:
            logger.exception(f"Agent execution failed: {e}")
            error_msg = str(e)
            if "iteration limit" in str(e).lower() or "time limit" in str(e).lower():
                error_msg = "抱歉，处理超时。请尝试简化您的问题，或分步骤提问。"
            self.memory_manager.save_message(session_id, user_id, "assistant", error_msg)
            return {
                "success": False,
                "response": error_msg,
                "session_id": session_id,
            }

    def direct_tool_call(
        self,
        tool_name: str,
        action: str,
        user_id: str = "default_user",
        role: str = "student",
        **kwargs,
    ) -> Dict[str, Any]:
        """直接调用指定工具（绕过 Agent 推理，用于程序化操作）

        Args:
            tool_name: 工具名称 (schedule_tool / rag_retrieve_tool / task_plan_tool / file_manage_tool)
            action: 工具操作类型
            user_id: 用户ID
            role: 用户角色
            **kwargs: 工具特定参数

        Returns:
            工具执行结果字典
        """
        tool_map = {
            "schedule_tool": self.schedule_tool,
            "rag_retrieve_tool": self.rag_tool,
            "task_plan_tool": self.task_plan_tool,
            "file_manage_tool": self.file_manage_tool,
            "note_tool": self.note_tool,
            "stat_tool": self.stat_tool,
            "config_tool": self.config_tool,
        }
        tool = tool_map.get(tool_name)
        if not tool:
            return {"success": False, "error": f"Unknown tool: {tool_name}"}

        # 权限检查
        action_permission = f"{tool_name.replace('_tool', '')}:{action}_own"
        if not self.access_control.has_permission(Role(role), action_permission):
            return {"success": False, "error": f"Permission denied for action: {action_permission}"}

        try:
            result_str = tool._run(
                action=action,
                _role=role,
                _user_id=user_id,
                user_id=user_id,
                **kwargs,
            )
            result = json.loads(result_str)
            return {"success": True, "result": result}
        except Exception as e:
            logger.exception(f"Direct tool call failed: {e}")
            return {"success": False, "error": str(e)}

    def get_history(self, session_id: str, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """获取会话历史"""
        return self.memory_manager.get_history(session_id, user_id, limit)

    def list_sessions(self, user_id: str) -> List[Dict[str, Any]]:
        """列出用户所有会话"""
        return self.memory_manager.list_sessions(user_id)

    def clear_session(self, session_id: str, user_id: str):
        """清除会话"""
        self.memory_manager.clear_memory(session_id, user_id)

    def cleanup(self):
        """清理资源"""
        self.memory_manager.close()
        logger.info("CourseAgentCore resources cleaned up")

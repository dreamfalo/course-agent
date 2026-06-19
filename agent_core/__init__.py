# agent_core - 智能课程助手 Agent 内核
# 基于 LangChain + DeepSeek LLM + Chroma 向量库

from agent_core.config import Settings
from agent_core.agent.course_agent import CourseAgentCore

__version__ = "1.0.0"
__all__ = ["CourseAgentCore", "Settings"]

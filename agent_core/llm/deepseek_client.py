"""
DeepSeek 统一 LLM 客户端
封装 DeepSeek Chat / Code 模型，兼容 LangChain ChatOpenAI 接口
支持 temperature、上下文长度、top_p 参数配置
"""
import logging
from typing import Optional, List, Dict, Any, Iterator

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import BaseMessage, AIMessage, HumanMessage, SystemMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from langchain_core.callbacks import CallbackManagerForLLMRun
from openai import OpenAI

from agent_core.config import DeepSeekConfig

logger = logging.getLogger(__name__)


class DeepSeekClient(BaseChatModel):
    """DeepSeek LLM 统一客户端，兼容 LangChain BaseChatModel 接口"""

    config: DeepSeekConfig
    _client: OpenAI = None

    class Config:
        arbitrary_types_allowed = True

    def __init__(self, config: Optional[DeepSeekConfig] = None, **kwargs):
        cfg = config or DeepSeekConfig()
        super().__init__(config=cfg, **kwargs)
        self._init_client()
    def bind_tools(
        self,
        tools: List[Any],
        **kwargs,
    ) -> "DeepSeekClient":
        """Bind tools to the LLM for tool calling (OpenAI-compatible)."""
        # Convert LangChain tools to OpenAI format
        openai_tools = []
        for tool in tools:
            if hasattr(tool, "args_schema") and tool.args_schema:
                schema = tool.args_schema.model_json_schema()
                openai_tools.append({
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": (tool.description or "")[:1024],
                        "parameters": {
                            "type": "object",
                            "properties": schema.get("properties", {}),
                            "required": schema.get("required", []),
                        },
                    },
                })
        self._bound_tools = openai_tools
        return self


    def _init_client(self):
        """初始化 OpenAI 兼容客户端（容错：无 API key 时延后初始化）"""
        if not self.config.api_key:
            logger.warning("DeepSeek API key not set, client deferred")
            self._client = None
            return
        try:
            import httpx
            http_client = httpx.Client(
                timeout=httpx.Timeout(30.0, connect=10.0),
                limits=httpx.Limits(max_keepalive_connections=5),
            )
            self._client = OpenAI(
                api_key=self.config.api_key,
                base_url=self.config.api_base,
                timeout=self.config.request_timeout,
                http_client=http_client,
            )
        except Exception as e:
            logger.warning(f"DeepSeek client init failed: {e}")
            self._client = None

    @property
    def _llm_type(self) -> str:
        return "deepseek"

    @property
    def _identifying_params(self) -> Dict[str, Any]:
        return {
            "model": self.config.chat_model,
            "temperature": self.config.default_temperature,
            "max_tokens": self.config.default_max_tokens,
            "top_p": self.config.default_top_p,
        }

    def _convert_messages_to_openai_format(self, messages: List[BaseMessage]) -> List[Dict[str, Any]]:
        """将 LangChain 消息列表转为 OpenAI 格式（含 tool calls）"""
        role_map = {"human": "user", "ai": "assistant", "system": "system", "tool": "tool"}
        type_role_map = {"human": "user", "ai": "assistant", "system": "system", "tool": "tool"}
        converted = []
        for msg in messages:
            role = type_role_map.get(msg.type, "user")
            entry: Dict[str, Any] = {"role": role}

            # Handle content
            if isinstance(msg.content, str):
                entry["content"] = msg.content
            elif isinstance(msg.content, list):
                text_parts = [
                    part["text"] if isinstance(part, dict) and part.get("type") == "text"
                    else str(part) if isinstance(part, str) else ""
                    for part in msg.content
                ]
                entry["content"] = "\n".join(text_parts)

            # Handle tool calls in AI messages
            if msg.type == "ai" and hasattr(msg, "tool_calls") and msg.tool_calls:
                entry["tool_calls"] = [
                    {
                        "id": tc["id"],
                        "type": "function",
                        "function": {
                            "name": tc["name"],
                            "arguments": __import__("json").dumps(tc["args"], ensure_ascii=False),
                        },
                    }
                    for tc in msg.tool_calls
                ]

            # Handle tool messages
            if msg.type == "tool":
                entry["tool_call_id"] = getattr(msg, "tool_call_id", "")
                entry["content"] = str(msg.content)

            converted.append(entry)
        return converted

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs,
    ) -> ChatResult:
        if not self._client:
            raise RuntimeError("DeepSeek client not initialized. Set DEEPSEEK_API_KEY.")
        model = kwargs.get("model", self.config.chat_model)
        temperature = kwargs.get("temperature", self.config.default_temperature)
        max_tokens = kwargs.get("max_tokens", self.config.default_max_tokens)
        top_p = kwargs.get("top_p", self.config.default_top_p)

        openai_messages = self._convert_messages_to_openai_format(messages)

        # Build request params
        params = dict(
            model=model, messages=openai_messages,
            temperature=temperature, max_tokens=max_tokens,
            top_p=top_p, stop=stop,
        )

        # Support tool calling (from bind_tools or kwargs)
        bound_tools = kwargs.get("tools") or getattr(self, "_bound_tools", None)
        if bound_tools:
            params["tools"] = bound_tools
            params["tool_choice"] = kwargs.get("tool_choice", "auto")

        response = self._client.chat.completions.create(**params)
        choice = response.choices[0]
        msg = choice.message

        # Handle tool calls
        if msg.tool_calls:
            from langchain_core.messages import ToolMessage
            tool_calls = []
            for tc in msg.tool_calls:
                tool_calls.append({
                    "id": tc.id,
                    "name": tc.function.name,
                    "args": __import__("json").loads(tc.function.arguments),
                })
            ai_message = AIMessage(
                content=msg.content or "",
                tool_calls=tool_calls,
            )
        else:
            ai_message = AIMessage(content=msg.content or "")

        if choice.finish_reason:
            ai_message.response_metadata = {"finish_reason": choice.finish_reason}
        if response.usage:
            ai_message.usage_metadata = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
            }
        return ChatResult(generations=[ChatGeneration(message=ai_message)])

    def switch_to_code_model(self):
        """切换到 DeepSeek Coder 模型"""
        self.config.chat_model = self.config.code_model

    def switch_to_chat_model(self):
        """切换到 DeepSeek Chat 模型"""
        self.config.chat_model = "deepseek-chat"

    def chat(
        self, user_message: str, system_prompt: Optional[str] = None,
        temperature: Optional[float] = None, max_tokens: Optional[int] = None,
        top_p: Optional[float] = None, model: Optional[str] = None,
    ) -> str:
        """便捷对话接口"""
        messages: List[BaseMessage] = []
        if system_prompt:
            messages.append(SystemMessage(content=system_prompt))
        messages.append(HumanMessage(content=user_message))
        kwargs: Dict[str, Any] = {}
        if temperature is not None:
            kwargs["temperature"] = temperature
        if max_tokens is not None:
            kwargs["max_tokens"] = max_tokens
        if top_p is not None:
            kwargs["top_p"] = top_p
        if model is not None:
            kwargs["model"] = model
        result = self._generate(messages, **kwargs)
        return result.generations[0].message.content

    def stream_chat(
        self, user_message: str, system_prompt: Optional[str] = None,
        temperature: Optional[float] = None, max_tokens: Optional[int] = None,
        top_p: Optional[float] = None, model: Optional[str] = None,
    ) -> Iterator[str]:
        """流式对话接口"""
        messages: List[Dict[str, str]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": user_message})
        response = self._client.chat.completions.create(
            model=model or self.config.chat_model,
            messages=messages,
            temperature=temperature or self.config.default_temperature,
            max_tokens=max_tokens or self.config.default_max_tokens,
            top_p=top_p or self.config.default_top_p,
            stream=True,
        )
        for chunk in response:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

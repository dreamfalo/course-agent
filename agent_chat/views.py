"""
Agent 对话入口 —— 集成 LangChain DeepSeek Agent 内核
POST /api/agent/chat/
"""
import logging
import threading

from rest_framework import views, status
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view, permission_classes

from agent_chat.serializers import ChatRequestSerializer, ChatHistorySerializer
from agent_chat.models import ChatHistory

logger = logging.getLogger(__name__)

# 全局 Agent 实例（懒加载）
_agent_instance = None
_agent_lock = threading.Lock()


def get_agent():
    """获取全局 CourseAgentCore 单例"""
    global _agent_instance
    if _agent_instance is None:
        with _agent_lock:
            if _agent_instance is None:
                from agent_core.agent.course_agent import CourseAgentCore
                _agent_instance = CourseAgentCore()
                logger.info("CourseAgentCore initialized")
    return _agent_instance


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def agent_chat(request):
    """
    Agent 对话入口

    接收用户自然语言文本，调用 LangChain DeepSeek Agent 内核，
    自动识别意图并调用对应工具，返回对话结果和工具执行日志。

    POST /api/agent/chat/
    Body: {"message": "帮我查一下周三的课表", "session_id": "可选", "role": "student"}
    """
    ser = ChatRequestSerializer(data=request.data)
    ser.is_valid(raise_exception=True)

    message = ser.validated_data["message"]
    session_id = ser.validated_data.get("session_id", "")
    user_role = ser.validated_data.get("role", "student")
    user_id = request.user.username

    try:
        agent = get_agent()
        result = agent.chat(
            user_message=message,
            user_id=user_id,
            session_id=session_id or None,
            role=user_role,
        )

        # 持久化用户消息
        ChatHistory.objects.create(
            user_id=user_id,
            session_id=result.get("session_id", ""),
            role="user",
            content=message,
        )

        # 持久化助手回复
        ChatHistory.objects.create(
            user_id=user_id,
            session_id=result.get("session_id", ""),
            role="assistant",
            content=result.get("response", ""),
            tool_calls=result.get("tool_calls", []),
        )

        return Response({
            "code": 0,
            "msg": "success",
            "data": {
                "response": result.get("response", ""),
                "session_id": result.get("session_id", ""),
                "tool_calls": result.get("tool_calls", []),
            },
        })

    except Exception as e:
        logger.exception(f"Agent chat error: {e}")
        return Response({
            "code": 500,
            "msg": f"对话处理失败: {str(e)}",
            "data": None,
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def chat_history(request):
    """
    获取对话历史

    GET /api/agent/history/?session_id=xxx
    """
    session_id = request.query_params.get("session_id", "")
    qs = ChatHistory.objects.filter(
        user_id=request.user.username,
        session_id=session_id,
    ).order_by("created_at")
    data = ChatHistorySerializer(qs, many=True).data
    return Response({"code": 0, "msg": "ok", "data": data})


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def delete_session(request):
    """删除整个会话历史"""
    session_id = request.data.get("session_id", "") or request.query_params.get("session_id", "")
    if not session_id:
        return Response({"code": 400, "msg": "请提供 session_id", "data": None})
    deleted, _ = ChatHistory.objects.filter(
        user_id=request.user.username,
        session_id=session_id,
    ).delete()
    return Response({"code": 0, "msg": f"已删除 {deleted} 条对话", "data": {"deleted": deleted}})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def chat_sessions(request):
    """
    获取用户所有会话列表

    GET /api/agent/sessions/
    """
    from django.db.models import Max, Count
    sessions = (
        ChatHistory.objects
        .filter(user_id=request.user.username)
        .values("session_id")
        .annotate(last_active=Max("created_at"), msg_count=Count("id"))
        .order_by("-last_active")
    )
    return Response({"code": 0, "msg": "ok", "data": list(sessions)})

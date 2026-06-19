from rest_framework import serializers
from agent_chat.models import ChatHistory
from config.models import SystemUser


class ChatRequestSerializer(serializers.Serializer):
    """对话请求"""
    message = serializers.CharField(required=True)
    session_id = serializers.CharField(required=False, allow_blank=True)
    role = serializers.ChoiceField(choices=[("student", "学生"), ("admin", "管理员")], default="student")


class ChatHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatHistory
        fields = ["id", "user_id", "session_id", "role", "content", "tool_calls", "created_at"]

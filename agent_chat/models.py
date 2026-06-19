from django.db import models


class ChatHistory(models.Model):
    """Agent 对话历史表"""
    user_id = models.CharField("用户ID", max_length=64, db_index=True)
    session_id = models.CharField("会话ID", max_length=128, db_index=True)
    role = models.CharField("角色", max_length=16, choices=[
        ("user", "用户"), ("assistant", "助手")
    ])
    content = models.TextField("消息内容")
    tool_calls = models.JSONField("工具调用记录", default=list)
    created_at = models.DateTimeField("创建时间", auto_now_add=True)

    class Meta:
        db_table = "agent_chat_history"
        ordering = ["created_at"]
        indexes = [
            models.Index(fields=["user_id", "session_id"]),
        ]

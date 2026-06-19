from rest_framework import serializers
from task.models import UserTask


class UserTaskSerializer(serializers.ModelSerializer):
    weekday_cn = serializers.SerializerMethodField()

    class Meta:
        model = UserTask
        fields = [
            "id", "user_id", "plan_id", "task_id", "task_name", "subject",
            "date", "weekday", "weekday_cn", "start_time", "end_time",
            "duration_minutes", "progress", "dependencies", "status",
            "generated_at", "updated_at",
        ]
        read_only_fields = ["id", "task_id", "generated_at", "updated_at"]

    def get_weekday_cn(self, obj):
        mapping = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
        return mapping[obj.weekday] if 0 <= obj.weekday <= 6 else ""


class TaskGenerateSerializer(serializers.Serializer):
    """AI 一键生成任务"""
    daily_study_hours = serializers.IntegerField(default=3)
    subjects = serializers.ListField(child=serializers.CharField(), default=list)
    start_date = serializers.DateField(required=True)
    days = serializers.IntegerField(default=30)


class GanttSerializer(serializers.Serializer):
    """甘特图查询参数"""
    plan_id = serializers.CharField(required=False)
    start_date = serializers.DateField(required=False)
    end_date = serializers.DateField(required=False)

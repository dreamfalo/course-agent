from rest_framework import serializers
from schedule.models import UserSchedule


class ScheduleSerializer(serializers.ModelSerializer):
    weekday_cn = serializers.SerializerMethodField()

    class Meta:
        model = UserSchedule
        fields = [
            "id", "user_id", "course_id", "course_name", "teacher",
            "weekday", "weekday_cn", "start_time", "end_time",
            "location", "week_range", "semester", "status",
            "created_at", "updated_at",
        ]
        extra_kwargs = {"user_id": {"required": False}}
        read_only_fields = ["id", "course_id", "created_at", "updated_at"]

    def get_weekday_cn(self, obj):
        mapping = ["鍛ㄤ竴", "鍛ㄤ簩", "鍛ㄤ笁", "鍛ㄥ洓", "鍛ㄤ簲", "鍛ㄥ叚", "鍛ㄦ棩"]
        return mapping[obj.weekday] if 0 <= obj.weekday <= 6 else ""


class ScheduleImportSerializer(serializers.Serializer):
    """鎵归噺瀵煎叆搴忓垪鍖栧櫒"""
    courses = serializers.ListField(child=serializers.DictField())
    semester = serializers.CharField(default="2025-2026-2")


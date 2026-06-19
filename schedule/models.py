from django.db import models


class UserSchedule(models.Model):
    """课表表"""
    user_id = models.CharField("用户ID", max_length=64, db_index=True)
    course_id = models.CharField("课程编号", max_length=64, unique=True)
    course_name = models.CharField("课程名称", max_length=128)
    teacher = models.CharField("授课教师", max_length=64, default="待定")
    weekday = models.SmallIntegerField("星期(0=周一,6=周日)")
    start_time = models.TimeField("开始时间")
    end_time = models.TimeField("结束时间")
    location = models.CharField("上课地点", max_length=128, default="待定")
    week_range = models.CharField("周次范围", max_length=32, default="1-16")
    semester = models.CharField("学期", max_length=32, default="2025-2026-2")
    status = models.CharField("状态", max_length=16, default="active", choices=[
        ("active", "有效"), ("cancelled", "已取消"), ("finished", "已结课")
    ])
    created_at = models.DateTimeField("创建时间", auto_now_add=True)
    updated_at = models.DateTimeField("更新时间", auto_now=True)

    class Meta:
        db_table = "user_schedule"
        ordering = ["weekday", "start_time"]
        indexes = [
            models.Index(fields=["user_id", "semester"]),
            models.Index(fields=["user_id", "weekday"]),
        ]

    def __str__(self):
        return f"{self.course_name} ({self.user_id})"

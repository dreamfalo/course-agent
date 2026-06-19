from django.db import models


class UserTask(models.Model):
    """学习任务表"""
    user_id = models.CharField("用户ID", max_length=64, db_index=True)
    plan_id = models.CharField("计划ID", max_length=64, db_index=True)
    task_id = models.CharField("任务ID", max_length=64, unique=True)
    task_name = models.CharField("任务名称", max_length=256)
    subject = models.CharField("科目", max_length=64)
    date = models.DateField("日期")
    weekday = models.SmallIntegerField("星期(0=周一)", default=0)
    start_time = models.TimeField("开始时间")
    end_time = models.TimeField("结束时间")
    duration_minutes = models.IntegerField("时长(分钟)", default=0)
    progress = models.IntegerField("进度(%)", default=0)
    dependencies = models.JSONField("依赖任务ID列表", default=list)
    plan_config = models.JSONField("计划配置", default=dict)
    status = models.CharField("状态", max_length=16, default="pending", choices=[
        ("pending", "待开始"), ("in_progress", "进行中"), ("completed", "已完成"), ("cancelled", "已取消")
    ])
    generated_at = models.DateTimeField("生成时间", auto_now_add=True)
    updated_at = models.DateTimeField("更新时间", auto_now=True)

    class Meta:
        db_table = "user_task"
        ordering = ["date", "start_time"]
        indexes = [
            models.Index(fields=["user_id", "plan_id"]),
            models.Index(fields=["user_id", "date"]),
        ]

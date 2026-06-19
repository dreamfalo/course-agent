"""学习任务：增删改 + 甘特图 + AI 一键生成"""
import json
import uuid
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from datetime import date as dt_date

from task.models import UserTask
from task.serializers import UserTaskSerializer, TaskGenerateSerializer
from schedule.models import UserSchedule


class TaskViewSet(viewsets.ModelViewSet):
    serializer_class = UserTaskSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = UserTask.objects.filter(user_id=self.request.user.username)
        plan_id = self.request.query_params.get("plan_id")
        if plan_id:
            qs = qs.filter(plan_id=plan_id)
        start = self.request.query_params.get("start_date")
        if start:
            qs = qs.filter(date__gte=start)
        end = self.request.query_params.get("end_date")
        if end:
            qs = qs.filter(date__lte=end)
        return qs

    def perform_create(self, serializer):
        serializer.save(
            user_id=self.request.user.username,
            task_id=f"TASK_{UserTask.objects.count() + 1:04d}",
        )

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response({"code": 0, "msg": "更新成功", "data": serializer.data})

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return Response({"code": 0, "msg": "删除成功", "data": None})

    @action(detail=False, methods=["post"])
    def ai_generate(self, request):
        """AI 一键生成学习任务（调用 TaskPlanTool）"""
        ser = TaskGenerateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        data = ser.validated_data

        # 读取用户课表
        schedules = list(UserSchedule.objects.filter(
            user_id=request.user.username,
        ).values("course_name", "weekday", "start_time", "end_time", "week_range"))
        schedule_data = []
        for s in schedules:
            schedule_data.append({
                "course_name": s["course_name"],
                "weekday": s["weekday"],
                "start_time": str(s["start_time"])[:5],
                "end_time": str(s["end_time"])[:5],
                "week_range": s.get("week_range", "1-16"),
            })

        config = {
            "daily_study_hours": data["daily_study_hours"],
            "subjects": data.get("subjects") or ["数学", "英语", "专业课"],
            "start_date": str(data["start_date"]),
            "days": data["days"],
        }

        try:
            from agent_core.tools.task_plan_tool import TaskPlanTool
            tool = TaskPlanTool()
            result_raw = tool._run(
                action="generate",
                schedule_data=json.dumps(schedule_data),
                tasks_config=json.dumps(config),
                _user_id=request.user.username,
            )
            result = json.loads(result_raw)

            if not result.get("success"):
                return Response({"code": 500, "msg": result.get("error", "生成失败"), "data": None})

            plan_id = result["plan"]["plan_id"]
            # 从 tool 内部获取完整 tasks
            full_plan = tool._plans.get(plan_id, {})
            tasks = full_plan.get("tasks", [])
            created = 0
            for t in tasks:
                UserTask.objects.update_or_create(
                    task_id=t["task_id"],
                    defaults={
                        "user_id": request.user.username,
                        "plan_id": plan_id,
                        "task_name": f"{t['subject']}学习",
                        "subject": t["subject"],
                        "date": dt_date.fromisoformat(t["date"]),
                        "weekday": t["weekday"],
                        "start_time": t["start_time"],
                        "end_time": t["end_time"],
                        "duration_minutes": t["duration_minutes"],
                        "progress": t.get("progress", 0),
                        "dependencies": t.get("dependencies", []),
                        "status": "pending",
                    },
                )
                created += 1

            return Response({
                "code": 0, "msg": f"成功生成 {created} 个学习任务",
                "data": {"plan_id": plan_id, "total_tasks": created},
            })
        except Exception as e:
            import logging
            logging.getLogger(__name__).exception("AI generate failed")
            return Response({"code": 500, "msg": str(e), "data": None})

    @action(detail=False, methods=["get"])
    def gantt(self, request):
        """甘特图数据查询"""
        qs = self.get_queryset()
        plan_id = request.query_params.get("plan_id")
        if plan_id:
            qs = qs.filter(plan_id=plan_id)
        gantt_data = []
        for t in qs:
            gantt_data.append({
                "id": t.task_id,
                "name": t.task_name,
                "start": f"{t.date.isoformat()}T{t.start_time}",
                "end": f"{t.date.isoformat()}T{t.end_time}",
                "progress": t.progress,
                "dependencies": t.dependencies,
                "custom_class": f"subject-{t.subject}",
            })
        return Response({"code": 0, "msg": "ok", "data": gantt_data})

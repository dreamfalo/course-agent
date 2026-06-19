"""
TaskPlanTool - 学习任务规划工具
功能：读取用户课表自动生成学习任务、规避上课时段、输出甘特图结构化数据
"""
import json
import logging
from typing import Type, Optional, List, Dict, Any, Tuple
from datetime import datetime, time, timedelta
from copy import deepcopy

from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

from agent_core.utils.helpers import weekday_str_to_int

logger = logging.getLogger(__name__)


class TaskPlanInput(BaseModel):
    """任务规划工具输入 Schema"""
    action: str = Field(description="操作类型: generate(生成学习计划), list(列出已有计划), adjust(调整计划)")
    schedule_data: Optional[str] = Field(default=None, description="JSON格式的课表数据")
    tasks_config: Optional[str] = Field(default=None, description="JSON格式的任务配置，如每天学习时长、科目列表等")
    plan_id: Optional[str] = Field(default=None, description="计划ID（调整用）")
    adjustments: Optional[str] = Field(default=None, description="JSON格式的调整内容")
    user_id: Optional[str] = Field(default=None, description="用户ID")


class TaskPlanTool(BaseTool):
    """读取课表自动生成学习任务，规避上课时段，输出甘特图数据结构"""

    name: str = "task_plan_tool"
    description: str = (
        "学习任务规划工具。自动读取用户课表，智能生成学习任务计划，"
        "规避上课时段，输出可用于渲染甘特图的结构化数据。"
        "操作类型: generate(根据课表生成学习计划), list(列出已有计划), adjust(调整现有计划)。"
    )
    args_schema: Type[BaseModel] = TaskPlanInput

    _plans: Dict[str, Dict[str, Any]] = {}

    class Config:
        arbitrary_types_allowed = True

    def _run(
        self,
        action: str,
        schedule_data: Optional[str] = None,
        tasks_config: Optional[str] = None,
        plan_id: Optional[str] = None,
        adjustments: Optional[str] = None,
        user_id: Optional[str] = None,
        _role: str = "student",
        _user_id: str = "",
        **kwargs,
    ) -> str:
        """执行任务规划"""
        uid = user_id or _user_id
        if not uid:
            return json.dumps({"error": "user_id is required"}, ensure_ascii=False)

        try:
            if action == "generate":
                return self._generate_plan(uid, schedule_data, tasks_config)
            elif action == "list":
                return self._list_plans(uid)
            elif action == "adjust":
                return self._adjust_plan(uid, plan_id, adjustments)
            else:
                return json.dumps({"error": f"Unknown action: {action}"}, ensure_ascii=False)
        except Exception as e:
            logger.exception(f"TaskPlanTool error: {e}")
            return json.dumps({"error": str(e)}, ensure_ascii=False)

    def _generate_plan(
        self, uid: str, schedule_data: Optional[str], tasks_config: Optional[str]
    ) -> str:
        """根据课表自动生成学习任务"""
        if not schedule_data:
            # Auto-fetch from database
            try:
                from schedule.models import UserSchedule
                qs = UserSchedule.objects.filter(user_id=uid).order_by("weekday", "start_time")
                weekdays = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
                courses = []
                for c in qs[:20]:
                    courses.append({
                        "course_name": c.course_name,
                        "weekday": c.weekday,
                        "weekday_cn": weekdays[c.weekday] if 0 <= c.weekday <= 6 else "",
                        "start_time": str(c.start_time)[:5],
                        "end_time": str(c.end_time)[:5],
                    })
                if not courses:
                    return json.dumps({"error": "没有课表数据，请先导入课表或手动添加课程"}, ensure_ascii=False)
                schedule_data = json.dumps(courses, ensure_ascii=False)
            except Exception as e:
                return json.dumps({"error": f"读取课表失败: {e}"}, ensure_ascii=False)

        try:
            schedules = json.loads(schedule_data) if isinstance(schedule_data, str) else schedule_data
        except json.JSONDecodeError:
            return json.dumps({"error": "Invalid schedule_data JSON"}, ensure_ascii=False)

        # 默认任务配置
        config = {
            "daily_study_hours": 3,
            "subjects": ["数学", "英语", "专业课"],
            "start_date": datetime.now().strftime("%Y-%m-%d"),
            "days": 30,
            "break_minutes": 10,
        }
        if tasks_config:
            try:
                user_config = json.loads(tasks_config) if isinstance(tasks_config, str) else tasks_config
                config.update(user_config)
            except json.JSONDecodeError:
                pass

        # 构建上课时段表
        class_slots: Dict[int, List[Tuple[time, time]]] = {}
        for s in schedules:
            wd = s.get("weekday", 0)
            st = time.fromisoformat(s["start_time"]) if isinstance(s["start_time"], str) else s["start_time"]
            et = time.fromisoformat(s["end_time"]) if isinstance(s["end_time"], str) else s["end_time"]
            if wd not in class_slots:
                class_slots[wd] = []
            class_slots[wd].append((st, et))

        # 生成每日空闲时段
        plan_id = f"PLAN_{len(self._plans) + 1:04d}"
        tasks: List[Dict[str, Any]] = []
        start_date = datetime.strptime(config["start_date"], "%Y-%m-%d")

        task_id = 0
        for day_offset in range(config["days"]):
            current_date = start_date + timedelta(days=day_offset)
            wd = current_date.weekday()
            busy_slots = sorted(class_slots.get(wd, []), key=lambda x: x[0])

            # 找出空闲时段
            free_slots = self._find_free_slots(busy_slots)
            if not free_slots:
                continue

            study_minutes = config["daily_study_hours"] * 60
            subject_idx = 0

            for slot_start, slot_end in free_slots:
                slot_duration = (
                    datetime.combine(current_date, slot_end)
                    - datetime.combine(current_date, slot_start)
                ).total_seconds() / 60

                if slot_duration < 30:
                    continue

                actual_study = min(slot_duration, study_minutes)
                if actual_study <= 0:
                    continue

                task_id += 1
                task_end = (
                    datetime.combine(current_date, slot_start)
                    + timedelta(minutes=int(actual_study))
                ).time()

                subject = config["subjects"][subject_idx % len(config["subjects"])]

                tasks.append({
                    "task_id": f"TASK_{task_id:04d}",
                    "date": current_date.strftime("%Y-%m-%d"),
                    "weekday": wd,
                    "weekday_cn": ["周一", "周二", "周三", "周四", "周五", "周六", "周日"][wd],
                    "start_time": slot_start.strftime("%H:%M"),
                    "end_time": task_end.strftime("%H:%M"),
                    "duration_minutes": int(actual_study),
                    "subject": subject,
                    "type": "study",
                    "dependencies": [],
                    "progress": 0,
                })

                study_minutes -= int(actual_study)
                subject_idx += 1
                if study_minutes <= 0:
                    break

        plan = {
            "plan_id": plan_id,
            "user_id": uid,
            "config": config,
            "tasks": tasks,
            "total_tasks": len(tasks),
            "total_study_hours": round(sum(t["duration_minutes"] for t in tasks) / 60, 1),
            "generated_at": datetime.now().isoformat(),
            "gantt_data": self._build_gantt_data(tasks),
        }
        self._plans[plan_id] = plan

        logger.info(f"Plan generated: {plan_id} with {len(tasks)} tasks")
        return json.dumps({
            "success": True,
            "plan": {k: v for k, v in plan.items() if k != "tasks"},
            "sample_tasks": tasks[:5],
            "total_tasks": len(tasks),
        }, ensure_ascii=False)

    def _find_free_slots(
        self, busy_slots: List[Tuple[time, time]]
    ) -> List[Tuple[time, time]]:
        """根据上课时段计算空闲时段"""
        day_start = time(8, 0)
        day_end = time(22, 0)
        free: List[Tuple[time, time]] = []
        current = day_start
        for bs, be in busy_slots:
            if current < bs:
                free.append((current, bs))
            current = max(current, be)
        if current < day_end:
            free.append((current, day_end))
        return free

    def _build_gantt_data(self, tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """构建甘特图结构化数据"""
        gantt = []
        for t in tasks:
            gantt.append({
                "id": t["task_id"],
                "name": f"{t['subject']}学习",
                "start": f"{t['date']}T{t['start_time']}:00",
                "end": f"{t['date']}T{t['end_time']}:00",
                "progress": t["progress"],
                "dependencies": t.get("dependencies", []),
                "custom_class": f"subject-{t.get('subject', 'default')}",
            })
        return gantt

    def _list_plans(self, uid: str) -> str:
        """列出用户所有计划"""
        user_plans = [
            {
                "plan_id": p["plan_id"],
                "total_tasks": p["total_tasks"],
                "total_study_hours": p["total_study_hours"],
                "generated_at": p["generated_at"],
            }
            for p in self._plans.values()
            if p.get("user_id") == uid
        ]
        return json.dumps({
            "success": True,
            "total": len(user_plans),
            "plans": user_plans,
        }, ensure_ascii=False)

    def _adjust_plan(self, uid: str, plan_id: Optional[str], adjustments: Optional[str]) -> str:
        """调整现有计划"""
        if not plan_id or plan_id not in self._plans:
            return json.dumps({"error": f"Plan not found: {plan_id}"}, ensure_ascii=False)
        if not adjustments:
            return json.dumps({"error": "adjustments is required"}, ensure_ascii=False)

        try:
            adj = json.loads(adjustments) if isinstance(adjustments, str) else adjustments
        except json.JSONDecodeError:
            return json.dumps({"error": "Invalid adjustments JSON"}, ensure_ascii=False)

        plan = self._plans[plan_id]
        for task in plan["tasks"]:
            if task["task_id"] in adj:
                task.update(adj[task["task_id"]])

        plan["updated_at"] = datetime.now().isoformat()
        plan["gantt_data"] = self._build_gantt_data(plan["tasks"])
        logger.info(f"Plan adjusted: {plan_id}")
        return json.dumps({"success": True, "plan_id": plan_id, "adjusted_tasks": len(adj)}, ensure_ascii=False)

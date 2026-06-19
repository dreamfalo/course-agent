"""
ScheduleTool - 课表管理工具
功能：课表增删改查、时间冲突校验、文件导出
直接操作 MySQL 数据库，与前端 REST API 数据互通
"""
import json
import logging
from typing import Type, Optional, List, Dict, Any
from datetime import datetime, time

from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

from agent_core.auth.access_control import AccessControl, Role

logger = logging.getLogger(__name__)

# Weekday mapping
WEEKDAY_MAP = {"周一": 0, "周二": 1, "周三": 2, "周四": 3, "周五": 4, "周六": 5, "周日": 6}
WEEKDAY_REVERSE = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]


def weekday_str_to_int(w: str) -> int:
    return WEEKDAY_MAP.get(w, -1)


class ScheduleInput(BaseModel):
    action: str = Field(description="操作类型: add, update, delete, query, export")
    course_name: Optional[str] = Field(default=None, description="课程名称")
    course_id: Optional[str] = Field(default=None, description="课程编号")
    teacher: Optional[str] = Field(default=None, description="授课教师")
    weekday: Optional[str] = Field(default=None, description="星期几: 周一/周二/.../周日")
    start_time: Optional[str] = Field(default=None, description="开始时间 HH:MM")
    end_time: Optional[str] = Field(default=None, description="结束时间 HH:MM")
    location: Optional[str] = Field(default=None, description="上课地点")
    week_range: Optional[str] = Field(default=None, description="周次范围")
    export_format: Optional[str] = Field(default=None, description="导出格式: csv, excel")
    user_id: Optional[str] = Field(default=None, description="用户ID（用户名）")


class ScheduleTool(BaseTool):
    name: str = "schedule_tool"
    description: str = (
        "课表管理工具。支持增删改查、时间冲突校验、文件导出。"
        "action: add/update/delete/query/export"
    )
    args_schema: Type[BaseModel] = ScheduleInput

    class Config:
        arbitrary_types_allowed = True

    def _get_model(self):
        from schedule.models import UserSchedule
        return UserSchedule

    def _run(
        self,
        action: str,
        course_name: Optional[str] = None,
        course_id: Optional[str] = None,
        teacher: Optional[str] = None,
        weekday: Optional[str] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        location: Optional[str] = None,
        week_range: Optional[str] = None,
        export_format: Optional[str] = None,
        user_id: Optional[str] = None,
        **kwargs,
    ) -> str:
        uid = user_id or kwargs.get("_user_id", "")
        if not uid:
            return json.dumps({"error": "请提供 user_id（用户名）"}, ensure_ascii=False)

        try:
            if action == "add":
                return self._add(uid, course_name, teacher, weekday, start_time, end_time, location, week_range)
            elif action == "update":
                return self._update(uid, course_id, course_name, teacher, weekday, start_time, end_time, location, week_range)
            elif action == "delete":
                return self._delete(uid, course_id)
            elif action == "query":
                return self._query(uid, weekday)
            elif action == "export":
                return self._export(uid, export_format)
            else:
                return json.dumps({"error": f"未知操作: {action}，支持: add/update/delete/query/export"}, ensure_ascii=False)
        except Exception as e:
            logger.exception(f"ScheduleTool error: {e}")
            return json.dumps({"error": str(e)}, ensure_ascii=False)

    def _add(self, uid, name, teacher, weekday, start, end, location, week_range):
        if not all([name, weekday, start, end]):
            return json.dumps({"error": "缺少必填项: course_name, weekday, start_time, end_time"}, ensure_ascii=False)

        wd = weekday_str_to_int(weekday)
        if wd < 0:
            return json.dumps({"error": f"无效星期: {weekday}，请用 周一/周二/.../周日"}, ensure_ascii=False)

        import uuid
        Model = self._get_model()

        # Check time conflict
        conflicts = Model.objects.filter(
            user_id=uid, weekday=wd,
            start_time__lt=end, end_time__gt=start,
        )
        for c in conflicts:
            return json.dumps({
                "error": f"时间冲突：与「{c.course_name}」({c.start_time}-{c.end_time})冲突，请换个时间",
                "conflict_with": c.course_name,
            }, ensure_ascii=False)

        course = Model.objects.create(
            user_id=uid,
            course_id=f"C{uuid.uuid4().hex[:8].upper()}",
            course_name=name,
            teacher=teacher or "待定",
            weekday=wd,
            start_time=start,
            end_time=end,
            location=location or "待定",
            week_range=week_range or "1-16",
        )
        return json.dumps({
            "success": True,
            "msg": f"已添加课程「{name}」({WEEKDAY_REVERSE[wd]} {start}-{end})",
            "course_id": course.course_id,
        }, ensure_ascii=False)

    def _update(self, uid, course_id, name, teacher, weekday, start, end, location, week_range):
        if not course_id:
            return json.dumps({"error": "请提供 course_id"}, ensure_ascii=False)

        Model = self._get_model()
        try:
            course = Model.objects.get(user_id=uid, course_id=course_id)
        except Model.DoesNotExist:
            return json.dumps({"error": f"未找到课程: {course_id}"}, ensure_ascii=False)

        if name: course.course_name = name
        if teacher: course.teacher = teacher
        if weekday:
            wd = weekday_str_to_int(weekday)
            if wd >= 0: course.weekday = wd
        if start: course.start_time = start
        if end: course.end_time = end
        if location: course.location = location
        if week_range: course.week_range = week_range
        course.save()

        return json.dumps({
            "success": True,
            "msg": f"已更新课程「{course.course_name}」",
            "course_id": course.course_id,
        }, ensure_ascii=False)

    def _delete(self, uid, course_id):
        if not course_id:
            return json.dumps({"error": "请提供 course_id"}, ensure_ascii=False)

        Model = self._get_model()
        deleted, _ = Model.objects.filter(user_id=uid, course_id=course_id).delete()
        if deleted:
            return json.dumps({"success": True, "msg": f"已删除课程 {course_id}"}, ensure_ascii=False)
        return json.dumps({"error": f"未找到课程: {course_id}"}, ensure_ascii=False)

    def _query(self, uid, weekday=None):
        Model = self._get_model()
        qs = Model.objects.filter(user_id=uid)
        if weekday:
            wd = weekday_str_to_int(weekday)
            if wd >= 0: qs = qs.filter(weekday=wd)

        courses = []
        for c in qs.order_by("weekday", "start_time"):
            courses.append({
                "course_id": c.course_id,
                "course_name": c.course_name,
                "teacher": c.teacher,
                "weekday": c.weekday,
                "weekday_cn": WEEKDAY_REVERSE[c.weekday] if 0 <= c.weekday <= 6 else "",
                "start_time": str(c.start_time)[:5],
                "end_time": str(c.end_time)[:5],
                "location": c.location,
                "week_range": c.week_range,
                "semester": c.semester,
            })

        if not courses:
            return json.dumps({
                "success": True,
                "total": 0,
                "msg": "当前没有课程记录，你可以说「帮我添加课程」来创建",
                "schedules": [],
            }, ensure_ascii=False)

        return json.dumps({
            "success": True,
            "total": len(courses),
            "schedules": courses,
        }, ensure_ascii=False)

    def _export(self, uid, fmt):
        Model = self._get_model()
        courses = Model.objects.filter(user_id=uid).order_by("weekday", "start_time")
        if not courses.exists():
            return json.dumps({"error": "没有课程可导出"}, ensure_ascii=False)

        lines = ["课程名称,教师,星期,时间,地点,周次"]
        for c in courses:
            wd = WEEKDAY_REVERSE[c.weekday] if 0 <= c.weekday <= 6 else ""
            lines.append(f"{c.course_name},{c.teacher},{wd},{c.start_time}-{c.end_time},{c.location},{c.week_range}")

        return json.dumps({
            "success": True,
            "format": fmt or "csv",
            "total": courses.count(),
            "preview": "\n".join(lines[:5]),
        }, ensure_ascii=False)

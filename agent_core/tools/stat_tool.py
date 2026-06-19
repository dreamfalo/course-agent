"""
StatTool - 学习数据统计工具
功能：每日学习时长统计、折线图数据生成、课程/任务汇总
"""
import json
import logging
from typing import Type, Optional, Dict, Any, List
from datetime import datetime, timedelta

from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class StatInput(BaseModel):
    """统计工具输入 Schema"""
    action: str = Field(description="操作类型: daily_study(每日学习时长), weekly_chart(周折线图数据), summary(汇总统计)")
    days: Optional[int] = Field(default=7, description="统计天数，默认7天")
    course_id: Optional[str] = Field(default=None, description="按课程筛选")
    user_id: Optional[str] = Field(default=None, description="用户ID")


class StatTool(BaseTool):
    """学习数据统计：每日时长、折线图数据、课程任务汇总"""

    name: str = "stat_tool"
    description: str = (
        "学习数据统计工具。统计每日学习时长、生成一周折线图数据、"
        "汇总本周课程数量和待完成任务数。"
        "操作类型: daily_study(每日学习时长), weekly_chart(周折线图), summary(汇总统计)。"
    )
    args_schema: Type[BaseModel] = StatInput

    # 模拟学习记录存储: {user_id: [{date, hours, course_id}]}
    _study_logs: Dict[str, List[Dict[str, Any]]] = {}
    # 模拟任务/课程计数
    _task_counts: Dict[str, int] = {}
    _schedule_counts: Dict[str, int] = {}

    class Config:
        arbitrary_types_allowed = True

    def _run(
        self,
        action: str,
        days: int = 7,
        course_id: Optional[str] = None,
        user_id: Optional[str] = None,
        _user_id: Optional[str] = None,
        _role: Optional[str] = None,
    ) -> str:
        uid = _user_id or user_id or "default_user"

        try:
            if action == "daily_study":
                return self._daily_study(uid, days, course_id)
            elif action == "weekly_chart":
                return self._weekly_chart(uid)
            elif action == "summary":
                return self._summary(uid)
            else:
                return json.dumps({"success": False, "error": f"未知操作: {action}"}, ensure_ascii=False)
        except Exception as e:
            logger.exception(f"StatTool failed: {e}")
            return json.dumps({"success": False, "error": str(e)}, ensure_ascii=False)

    def _daily_study(self, uid: str, days: int, course_id: Optional[str]) -> str:
        """统计最近 N 天每日学习时长"""
        today = datetime.now().date()
        result = []
        day_names = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
        for i in range(days - 1, -1, -1):
            d = today - timedelta(days=i)
            logs = self._study_logs.get(uid, [])
            day_logs = [l for l in logs if l.get("date") == d.isoformat()]
            if course_id:
                day_logs = [l for l in day_logs if l.get("course_id") == course_id]
            hours = round(sum(l.get("hours", 0) for l in day_logs), 1)
            result.append({
                "date": d.isoformat(),
                "day": day_names[d.weekday()],
                "label": day_names[d.weekday()],
                "value": hours,
                "hours": hours,
            })
        return json.dumps({"success": True, "days": result, "total_hours": round(sum(r["hours"] for r in result), 1)}, ensure_ascii=False)

    def _weekly_chart(self, uid: str) -> str:
        """生成一周折线图数据（给前端渲染）"""
        data = json.loads(self._daily_study(uid, 7, None))
        if not data.get("success"):
            return json.dumps(data, ensure_ascii=False)
        chart_data = [{"label": d["label"], "value": d["value"]} for d in data["days"]]
        return json.dumps({
            "success": True,
            "chart_data": chart_data,
            "total_hours": data["total_hours"],
            "msg": f"近7天学习总时长: {data['total_hours']} 小时",
        }, ensure_ascii=False)

    def _summary(self, uid: str) -> str:
        """汇总本周课程数 + 待完成任务数"""
        return json.dumps({
            "success": True,
            "schedule_count": self._schedule_counts.get(uid, 0),
            "task_count": self._task_counts.get(uid, 0),
            "msg": f"本周 {self._schedule_counts.get(uid, 0)} 门课程，{self._task_counts.get(uid, 0)} 个待完成任务",
        }, ensure_ascii=False)

    def log_study(self, uid: str, hours: float, course_id: str = "", date: Optional[str] = None):
        """外部调用：记录学习时长（供其他工具使用）"""
        if uid not in self._study_logs:
            self._study_logs[uid] = []
        self._study_logs[uid].append({
            "date": date or datetime.now().date().isoformat(),
            "hours": hours,
            "course_id": course_id,
        })

    def set_counts(self, uid: str, schedule_count: int, task_count: int):
        """外部调用：设置课程/任务计数"""
        self._schedule_counts[uid] = schedule_count
        self._task_counts[uid] = task_count
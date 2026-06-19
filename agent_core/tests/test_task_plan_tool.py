"""
TaskPlanTool 单元测试
测试学习计划生成、空闲时段计算、甘特图数据输出
"""
import json
import unittest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent_core.tools.task_plan_tool import TaskPlanTool


class TestTaskPlanTool(unittest.TestCase):
    """TaskPlanTool 单元测试"""

    def setUp(self):
        self.tool = TaskPlanTool()
        self.uid = "user_task_001"
        self.schedule_data = [
            {
                "course_name": "高等数学",
                "weekday": 0,
                "start_time": "08:00",
                "end_time": "10:00",
                "week_range": "1-16",
            },
            {
                "course_name": "大学英语",
                "weekday": 0,
                "start_time": "14:00",
                "end_time": "16:00",
                "week_range": "1-16",
            },
            {
                "course_name": "计算机基础",
                "weekday": 2,
                "start_time": "10:00",
                "end_time": "12:00",
                "week_range": "1-16",
            },
        ]

    def test_generate_plan_success(self):
        """测试生成学习计划"""
        result_str = self.tool._run(
            action="generate",
            schedule_data=json.dumps(self.schedule_data),
            _user_id=self.uid,
        )
        result = json.loads(result_str)
        self.assertTrue(result.get("success"))
        self.assertIn("plan", result)
        self.assertGreater(result["total_tasks"], 0)
        self.assertIn("sample_tasks", result)

    def test_generate_avoids_class_times(self):
        """测试学习任务规避上课时段"""
        result_str = self.tool._run(
            action="generate",
            schedule_data=json.dumps(self.schedule_data),
            _user_id=self.uid,
        )
        result = json.loads(result_str)

        # 解析完整计划
        plan_key = list(self.tool._plans.keys())[0]
        full_plan = self.tool._plans[plan_key]
        tasks = full_plan["tasks"]

        # 检查没有任务与上课时间重叠
        for task in tasks:
            wd = task["weekday"]
            task_start = task["start_time"]
            task_end = task["end_time"]
            for course in self.schedule_data:
                if course["weekday"] == wd:
                    cs = course["start_time"]
                    ce = course["end_time"]
                    self.assertFalse(
                        task_start < ce and task_end > cs,
                        f"Task {task['task_id']} overlaps with {course['course_name']}"
                    )

    def test_generate_with_custom_config(self):
        """测试自定义任务配置"""
        config = {
            "daily_study_hours": 2,
            "subjects": ["算法", "数据结构"],
            "start_date": "2026-01-01",
            "days": 7,
        }
        result_str = self.tool._run(
            action="generate",
            schedule_data=json.dumps(self.schedule_data),
            tasks_config=json.dumps(config),
            _user_id=self.uid,
        )
        result = json.loads(result_str)
        self.assertTrue(result.get("success"))

    def test_generate_empty_schedule(self):
        """测试空课表"""
        result_str = self.tool._run(
            action="generate",
            schedule_data="[]",
            _user_id=self.uid,
        )
        result = json.loads(result_str)
        self.assertTrue(result.get("success"))

    def test_generate_no_schedule_data(self):
        """测试缺少课表数据"""
        result_str = self.tool._run(
            action="generate",
            _user_id=self.uid,
        )
        result = json.loads(result_str)
        self.assertIn("error", result)

    def test_list_plans(self):
        """测试列出计划"""
        self.tool._run(
            action="generate",
            schedule_data=json.dumps(self.schedule_data),
            _user_id=self.uid,
        )
        result_str = self.tool._run(action="list", _user_id=self.uid)
        result = json.loads(result_str)
        self.assertTrue(result.get("success"))
        self.assertGreaterEqual(result["total"], 1)

    def test_adjust_plan(self):
        """测试调整计划"""
        self.tool._run(
            action="generate",
            schedule_data=json.dumps(self.schedule_data),
            _user_id=self.uid,
        )
        plan_ids = list(self.tool._plans.keys())
        adjustments = json.dumps({
            "TASK_0001": {"progress": 50, "subject": "高等数学复习"},
        })
        result_str = self.tool._run(
            action="adjust",
            plan_id=plan_ids[0],
            adjustments=adjustments,
            _user_id=self.uid,
        )
        result = json.loads(result_str)
        self.assertTrue(result.get("success"))

    def test_gantt_data_structure(self):
        """测试甘特图数据结构"""
        self.tool._run(
            action="generate",
            schedule_data=json.dumps(self.schedule_data),
            _user_id=self.uid,
        )
        plan_key = list(self.tool._plans.keys())[0]
        gantt = self.tool._plans[plan_key]["gantt_data"]
        self.assertIsInstance(gantt, list)
        if gantt:
            item = gantt[0]
            self.assertIn("id", item)
            self.assertIn("name", item)
            self.assertIn("start", item)
            self.assertIn("end", item)
            self.assertIn("progress", item)


if __name__ == "__main__":
    unittest.main()


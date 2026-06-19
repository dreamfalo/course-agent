"""
ScheduleTool 单元测试
测试课表增删改查、时间冲突校验、文件导出
"""
import json
import unittest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent_core.tools.schedule_tool import ScheduleTool


class TestScheduleTool(unittest.TestCase):
    """ScheduleTool 单元测试"""

    def setUp(self):
        self.tool = ScheduleTool()
        self.uid = "user_test_001"

    def test_add_course_success(self):
        """测试正常添加课程"""
        result_str = self.tool._run(
            action="add",
            course_name="高等数学",
            teacher="张教授",
            weekday="周一",
            start_time="08:00",
            end_time="09:30",
            location="教学楼A101",
            week_range="1-16",
            _user_id=self.uid,
        )
        result = json.loads(result_str)
        self.assertTrue(result.get("success"))
        self.assertEqual(result["course"]["course_name"], "高等数学")

    def test_add_course_time_conflict(self):
        """测试时间冲突检测"""
        # 先添加一门课
        self.tool._run(
            action="add",
            course_name="线性代数",
            weekday="周一",
            start_time="08:00",
            end_time="10:00",
            _user_id=self.uid,
        )
        # 再添加时间冲突的课
        result_str = self.tool._run(
            action="add",
            course_name="概率论",
            weekday="周一",
            start_time="09:00",
            end_time="11:00",
            _user_id=self.uid,
        )
        result = json.loads(result_str)
        self.assertIn("error", result)
        self.assertIn("冲突", result["error"])

    def test_add_course_missing_fields(self):
        """测试缺少必填字段"""
        result_str = self.tool._run(
            action="add",
            course_name="高等数学",
            _user_id=self.uid,
        )
        result = json.loads(result_str)
        self.assertIn("error", result)

    def test_invalid_weekday(self):
        """测试无效星期"""
        result_str = self.tool._run(
            action="add",
            course_name="测试",
            weekday="周八",
            start_time="08:00",
            end_time="09:00",
            _user_id=self.uid,
        )
        result = json.loads(result_str)
        self.assertIn("error", result)

    def test_invalid_time_range(self):
        """测试结束时间早于开始时间"""
        result_str = self.tool._run(
            action="add",
            course_name="测试",
            weekday="周一",
            start_time="10:00",
            end_time="08:00",
            _user_id=self.uid,
        )
        result = json.loads(result_str)
        self.assertIn("error", result)

    def test_query_schedule(self):
        """测试查询课表"""
        self.tool._run(
            action="add", course_name="数学", weekday="周一",
            start_time="08:00", end_time="09:00", _user_id=self.uid,
        )
        self.tool._run(
            action="add", course_name="英语", weekday="周二",
            start_time="10:00", end_time="11:00", _user_id=self.uid,
        )
        result_str = self.tool._run(action="query", _user_id=self.uid)
        result = json.loads(result_str)
        self.assertTrue(result.get("success"))
        self.assertEqual(result["total"], 2)

    def test_query_by_weekday(self):
        """测试按星期筛选"""
        self.tool._run(
            action="add", course_name="数学", weekday="周一",
            start_time="08:00", end_time="09:00", _user_id=self.uid,
        )
        self.tool._run(
            action="add", course_name="英语", weekday="周二",
            start_time="10:00", end_time="11:00", _user_id=self.uid,
        )
        result_str = self.tool._run(action="query", weekday="周一", _user_id=self.uid)
        result = json.loads(result_str)
        self.assertEqual(result["total"], 1)
        self.assertEqual(result["schedules"][0]["course_name"], "数学")

    def test_update_course(self):
        """测试更新课程"""
        self.tool._run(
            action="add", course_name="数学", weekday="周一",
            start_time="08:00", end_time="09:00", _user_id=self.uid,
        )
        result_str = self.tool._run(
            action="update", course_id="COURSE_0001",
            teacher="李教授", _user_id=self.uid,
        )
        result = json.loads(result_str)
        self.assertTrue(result.get("success"))
        self.assertEqual(result["course"]["teacher"], "李教授")

    def test_delete_course(self):
        """测试删除课程"""
        self.tool._run(
            action="add", course_name="数学", weekday="周一",
            start_time="08:00", end_time="09:00", _user_id=self.uid,
        )
        result_str = self.tool._run(action="delete", course_id="COURSE_0001", _user_id=self.uid)
        result = json.loads(result_str)
        self.assertTrue(result.get("success"))

    def test_export_excel(self):
        """测试导出 Excel 格式"""
        self.tool._run(
            action="add", course_name="数学", weekday="周一",
            start_time="08:00", end_time="09:00", _user_id=self.uid,
        )
        result_str = self.tool._run(action="export", export_format="excel", _user_id=self.uid)
        result = json.loads(result_str)
        self.assertTrue(result.get("success"))
        self.assertEqual(result["format"], "excel")

    def test_export_ics(self):
        """测试导出 ICS 格式"""
        self.tool._run(
            action="add", course_name="数学", weekday="周一",
            start_time="08:00", end_time="09:00", _user_id=self.uid,
        )
        result_str = self.tool._run(action="export", export_format="ics", _user_id=self.uid)
        result = json.loads(result_str)
        self.assertTrue(result.get("success"))
        self.assertIn("BEGIN:VCALENDAR", result["content_preview"])

    def test_user_isolation(self):
        """测试用户数据隔离"""
        self.tool._run(
            action="add", course_name="用户A课程", weekday="周一",
            start_time="08:00", end_time="09:00", _user_id="user_a",
        )
        result_str = self.tool._run(action="query", _user_id="user_b")
        result = json.loads(result_str)
        self.assertEqual(result["total"], 0)


if __name__ == "__main__":
    unittest.main()

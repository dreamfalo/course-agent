"""
FileManageTool 单元测试
测试文件上传、下载、列表、删除、过期清理
"""
import json
import os
import tempfile
import unittest
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent_core.tools.file_manage_tool import FileManageTool


class TestFileManageTool(unittest.TestCase):
    """FileManageTool 单元测试"""

    def setUp(self):
        self.tool = FileManageTool()
        self.uid = "user_file_001"
        self.course_id = "COURSE_CS101"

    def _create_test_file(self, content: str = "test content") -> str:
        """创建临时测试文件"""
        fd, path = tempfile.mkstemp(suffix=".txt", prefix="test_file_")
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(content)
        return path

    def test_upload_file_success(self):
        """测试上传文件（本地回退模式）"""
        path = self._create_test_file()
        try:
            result_str = self.tool._run(
                action="upload",
                file_path=path,
                course_id=self.course_id,
                _user_id=self.uid,
            )
            result = json.loads(result_str)
            self.assertTrue(result.get("success"))
            self.assertEqual(result["file"]["file_name"], os.path.basename(path))
            self.assertEqual(result["file"]["course_id"], self.course_id)
        finally:
            os.unlink(path)

    def test_upload_temp_file_with_ttl(self):
        """测试上传临时文件并设置过期时间"""
        path = self._create_test_file()
        try:
            result_str = self.tool._run(
                action="upload",
                file_path=path,
                course_id=self.course_id,
                is_temp=True,
                ttl_hours=1,
                _user_id=self.uid,
            )
            result = json.loads(result_str)
            self.assertTrue(result.get("success"))
            self.assertTrue(result["file"]["is_temp"])
            self.assertIsNotNone(result["file"]["expires_at"])
        finally:
            os.unlink(path)

    def test_upload_file_not_found(self):
        """测试上传不存在的文件"""
        result_str = self.tool._run(
            action="upload",
            file_path="/nonexistent/file.pdf",
            _user_id=self.uid,
        )
        result = json.loads(result_str)
        self.assertIn("error", result)

    def test_list_files(self):
        """测试列出文件"""
        path = self._create_test_file()
        try:
            self.tool._run(
                action="upload", file_path=path,
                course_id=self.course_id, _user_id=self.uid,
            )
            result_str = self.tool._run(action="list", _user_id=self.uid)
            result = json.loads(result_str)
            self.assertTrue(result.get("success"))
            self.assertGreaterEqual(result["total"], 1)
        finally:
            os.unlink(path)

    def test_list_files_by_course(self):
        """测试按课程筛选文件"""
        path = self._create_test_file()
        try:
            self.tool._run(
                action="upload", file_path=path,
                course_id="COURSE_A", _user_id=self.uid,
            )
            result_str = self.tool._run(
                action="list", course_id="COURSE_B", _user_id=self.uid,
            )
            result = json.loads(result_str)
            self.assertEqual(result["total"], 0)
        finally:
            os.unlink(path)

    def test_delete_file(self):
        """测试删除文件"""
        path = self._create_test_file()
        try:
            upload_result = json.loads(
                self.tool._run(
                    action="upload", file_path=path,
                    course_id=self.course_id, _user_id=self.uid,
                )
            )
            obj_name = upload_result["file"]["object_name"]

            delete_result = json.loads(
                self.tool._run(
                    action="delete",
                    object_name=obj_name,
                    _user_id=self.uid,
                )
            )
            self.assertTrue(delete_result.get("success"))
        finally:
            os.unlink(path)

    def test_delete_other_user_file_blocked(self):
        """测试学生不能删除他人文件"""
        path = self._create_test_file()
        try:
            upload_result = json.loads(
                self.tool._run(
                    action="upload", file_path=path,
                    course_id=self.course_id, _user_id="user_a",
                )
            )
            obj_name = upload_result["file"]["object_name"]

            delete_result = json.loads(
                self.tool._run(
                    action="delete",
                    object_name=obj_name,
                    _user_id="user_b",
                    _role="student",
                )
            )
            self.assertIn("error", delete_result)
        finally:
            os.unlink(path)

    def test_cleanup_only_admin(self):
        """测试只有管理员能清理"""
        result_str = self.tool._run(
            action="cleanup",
            _user_id=self.uid,
            _role="student",
        )
        result = json.loads(result_str)
        self.assertIn("error", result)

    def test_admin_cleanup(self):
        """测试管理员清理过期文件"""
        result_str = self.tool._run(
            action="cleanup",
            _user_id=self.uid,
            _role="admin",
        )
        result = json.loads(result_str)
        self.assertTrue(result.get("success"))

    def test_download_file_not_found(self):
        """测试下载不存在的文件"""
        result_str = self.tool._run(
            action="download",
            object_name="nonexistent_file",
            _user_id=self.uid,
        )
        result = json.loads(result_str)
        self.assertIn("error", result)


if __name__ == "__main__":
    unittest.main()

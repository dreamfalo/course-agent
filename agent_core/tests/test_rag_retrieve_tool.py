"""
RAGRetrieveTool 单元测试
测试文档解析、文本分块、向量检索
"""
import json
import os
import tempfile
import unittest
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent_core.config import ChromaConfig
from agent_core.tools.rag_retrieve_tool import RAGRetrieveTool


class TestRAGRetrieveTool(unittest.TestCase):
    """RAGRetrieveTool 单元测试"""

    def setUp(self):
        chroma_config = ChromaConfig(
            persist_directory=os.path.join(tempfile.gettempdir(), "test_chroma"),
            collection_name="test_courses",
            chunk_size=200,
            chunk_overlap=20,
        )
        self.tool = RAGRetrieveTool(chroma_config=chroma_config)
        self.uid = "user_rag_001"
        self.course_id = "COURSE_MATH"

    def _create_test_txt(self, content: str) -> str:
        """创建临时TXT测试文件"""
        fd, path = tempfile.mkstemp(suffix=".txt", prefix="test_rag_")
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(content)
        return path

    def test_ingest_txt_success(self):
        """测试 TXT 文档入库"""
        path = self._create_test_txt(
            "第一章 微积分基础\n\n极限是微积分的基本概念。\n"
            "第二章 导数\n\n导数是函数变化率的度量。\n" * 10
        )
        try:
            result_str = self.tool._run(
                action="ingest",
                file_path=path,
                course_id=self.course_id,
                _user_id=self.uid,
            )
            result = json.loads(result_str)
            self.assertTrue(result.get("success"))
            self.assertEqual(result["course_id"], self.course_id)
            self.assertGreater(result["chunks"], 0)
        finally:
            os.unlink(path)

    def test_ingest_file_not_found(self):
        """测试文件不存在"""
        result_str = self.tool._run(
            action="ingest",
            file_path="/nonexistent/file.pdf",
            course_id=self.course_id,
            _user_id=self.uid,
        )
        result = json.loads(result_str)
        self.assertIn("error", result)

    def test_ingest_no_course_id(self):
        """测试缺 course_id"""
        path = self._create_test_txt("测试内容")
        try:
            result_str = self.tool._run(
                action="ingest",
                file_path=path,
                _user_id=self.uid,
            )
            result = json.loads(result_str)
            self.assertIn("error", result)
        finally:
            os.unlink(path)

    def test_list_documents(self):
        """测试列出文档"""
        path = self._create_test_txt("测试文档内容" * 20)
        try:
            self.tool._run(
                action="ingest", file_path=path,
                course_id=self.course_id, _user_id=self.uid,
            )
            result_str = self.tool._run(
                action="list", _user_id=self.uid,
            )
            result = json.loads(result_str)
            self.assertTrue(result.get("success"))
            self.assertGreaterEqual(result["total"], 1)
        finally:
            os.unlink(path)

    def test_list_by_course(self):
        """测试按课程筛选文档"""
        result_str = self.tool._run(
            action="list", course_id="COURSE_NONEXIST", _user_id=self.uid,
        )
        result = json.loads(result_str)
        self.assertTrue(result.get("success"))

    def test_delete_document(self):
        """测试删除文档"""
        path = self._create_test_txt("待删除内容" * 10)
        try:
            ingest_result = json.loads(
                self.tool._run(
                    action="ingest", file_path=path,
                    course_id=self.course_id, _user_id=self.uid,
                )
            )
            doc_id = ingest_result.get("doc_id")
            self.assertIsNotNone(doc_id)

            delete_result = json.loads(
                self.tool._run(action="delete", doc_id=doc_id, _user_id=self.uid)
            )
            self.assertTrue(delete_result.get("success"))
        finally:
            os.unlink(path)

    def test_unknown_action(self):
        """测试未知操作"""
        result_str = self.tool._run(action="unknown_action", _user_id=self.uid)
        result = json.loads(result_str)
        self.assertIn("error", result)


if __name__ == "__main__":
    unittest.main()

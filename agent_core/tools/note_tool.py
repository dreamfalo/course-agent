"""
NoteTool - 学习笔记管理工具
功能：笔记增删改查、按课程/关键词检索、笔记导出
"""
import json
import logging
from typing import Type, Optional, Dict, Any, List
from datetime import datetime
from uuid import uuid4

from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class NoteInput(BaseModel):
    """笔记工具输入 Schema"""
    action: str = Field(description="操作类型: create(新建), update(修改), delete(删除), query(检索), export(导出)")
    note_id: Optional[str] = Field(default=None, description="笔记ID")
    title: Optional[str] = Field(default=None, description="笔记标题")
    content: Optional[str] = Field(default=None, description="笔记正文内容")
    course_id: Optional[str] = Field(default=None, description="绑定课程ID")
    course_name: Optional[str] = Field(default=None, description="绑定课程名称")
    keyword: Optional[str] = Field(default=None, description="检索关键词")
    color: Optional[str] = Field(default=None, description="笔记颜色标记，如 #2981fd")
    user_id: Optional[str] = Field(default=None, description="用户ID")


class NoteTool(BaseTool):
    """学习笔记增删改查 + 检索 + 导出"""

    name: str = "note_tool"
    description: str = (
        "学习笔记管理工具。支持创建、修改、删除、检索笔记，按课程或关键词搜索，"
        "以及导出单篇笔记为文本文件。"
        "操作类型: create(新建笔记), update(修改笔记), delete(删除笔记), "
        "query(检索笔记), export(导出笔记)。"
    )
    args_schema: Type[BaseModel] = NoteInput

    _notes: Dict[str, List[Dict[str, Any]]] = {}

    class Config:
        arbitrary_types_allowed = True

    def _run(
        self,
        action: str,
        note_id: Optional[str] = None,
        title: Optional[str] = None,
        content: Optional[str] = None,
        course_id: Optional[str] = None,
        course_name: Optional[str] = None,
        keyword: Optional[str] = None,
        color: Optional[str] = None,
        user_id: Optional[str] = None,
        _user_id: Optional[str] = None,
        _role: Optional[str] = None,
    ) -> str:
        uid = _user_id or user_id or "default_user"

        if uid not in self._notes:
            self._notes[uid] = []

        try:
            if action == "create":
                return self._create_note(uid, title, content, course_id, course_name, color)
            elif action == "update":
                return self._update_note(uid, note_id, title, content, color)
            elif action == "delete":
                return self._delete_note(uid, note_id)
            elif action == "query":
                return self._query_notes(uid, course_id, keyword)
            elif action == "export":
                return self._export_note(uid, note_id)
            else:
                return json.dumps({"success": False, "error": f"未知操作: {action}"}, ensure_ascii=False)
        except Exception as e:
            logger.exception(f"NoteTool failed: {e}")
            return json.dumps({"success": False, "error": str(e)}, ensure_ascii=False)

    def _create_note(self, uid: str, title: Optional[str], content: Optional[str],
                     course_id: Optional[str], course_name: Optional[str], color: Optional[str]) -> str:
        if not title:
            return json.dumps({"success": False, "error": "笔记标题不能为空"}, ensure_ascii=False)
        note = {
            "id": str(uuid4())[:12],
            "title": title,
            "content": content or "",
            "course_id": course_id or "",
            "course_name": course_name or "",
            "color": color or "#2981fd",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        }
        self._notes[uid].append(note)
        logger.info(f"Note created: {note['id']} by {uid}")
        return json.dumps({"success": True, "note": note}, ensure_ascii=False)

    def _update_note(self, uid: str, note_id: Optional[str], title: Optional[str],
                     content: Optional[str], color: Optional[str]) -> str:
        if not note_id:
            return json.dumps({"success": False, "error": "请指定笔记ID"}, ensure_ascii=False)
        for note in self._notes[uid]:
            if note["id"] == note_id:
                if title:
                    note["title"] = title
                if content is not None:
                    note["content"] = content
                if color:
                    note["color"] = color
                note["updated_at"] = datetime.now().isoformat()
                return json.dumps({"success": True, "note": note}, ensure_ascii=False)
        return json.dumps({"success": False, "error": f"笔记 {note_id} 不存在"}, ensure_ascii=False)

    def _delete_note(self, uid: str, note_id: Optional[str]) -> str:
        if not note_id:
            return json.dumps({"success": False, "error": "请指定笔记ID"}, ensure_ascii=False)
        for i, note in enumerate(self._notes[uid]):
            if note["id"] == note_id:
                self._notes[uid].pop(i)
                return json.dumps({"success": True, "msg": f"笔记 {note_id} 已删除"}, ensure_ascii=False)
        return json.dumps({"success": False, "error": f"笔记 {note_id} 不存在"}, ensure_ascii=False)

    def _query_notes(self, uid: str, course_id: Optional[str], keyword: Optional[str]) -> str:
        results = self._notes[uid]
        if course_id:
            results = [n for n in results if n.get("course_id") == course_id]
        if keyword:
            kw = keyword.lower()
            results = [n for n in results if kw in n.get("title", "").lower() or kw in n.get("content", "").lower()]
        return json.dumps({
            "success": True,
            "count": len(results),
            "notes": sorted(results, key=lambda x: x.get("updated_at", ""), reverse=True),
        }, ensure_ascii=False)

    def _export_note(self, uid: str, note_id: Optional[str]) -> str:
        if not note_id:
            return json.dumps({"success": False, "error": "请指定要导出的笔记ID"}, ensure_ascii=False)
        for note in self._notes[uid]:
            if note["id"] == note_id:
                text = f"# {note['title']}\n\n{note['content']}\n\n---\n课程: {note.get('course_name','')}\n时间: {note['updated_at']}"
                filename = f"note_{note_id}.txt"
                return json.dumps({
                    "success": True,
                    "filename": filename,
                    "content": text,
                    "msg": f"笔记已导出为 {filename}"
                }, ensure_ascii=False)
        return json.dumps({"success": False, "error": f"笔记 {note_id} 不存在"}, ensure_ascii=False)
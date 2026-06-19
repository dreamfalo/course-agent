from django.db import models


class KnowledgeFile(models.Model):
    """RAG 知识库文档表"""
    user_id = models.CharField("用户ID", max_length=64, db_index=True)
    course_id = models.CharField("关联课程ID", max_length=64, db_index=True)
    doc_id = models.CharField("文档唯一ID", max_length=256, unique=True)
    file_name = models.CharField("文件名", max_length=256)
    file_path = models.CharField("文件路径", max_length=512)
    file_type = models.CharField("文件类型", max_length=16, choices=[
        ("pdf", "PDF"), ("docx", "Word"), ("txt", "TXT"), ("md", "Markdown")
    ])
    file_size = models.BigIntegerField("文件大小(字节)", default=0)
    chunks_count = models.IntegerField("分块数量", default=0)
    course_name = models.CharField("关联课程名", max_length=128, blank=True)
    status = models.CharField("状态", max_length=16, default="uploaded", choices=[
        ("uploaded", "已上传"), ("vectorized", "已向量化"), ("failed", "失败")
    ])
    uploaded_at = models.DateTimeField("上传时间", auto_now_add=True)

    class Meta:
        db_table = "user_knowledge_file"
        ordering = ["-uploaded_at"]
        indexes = [
            models.Index(fields=["user_id", "course_id"]),
        ]

"""知识库：文件上传、向量化、检索、预览"""
import os
import uuid
import threading
from django.conf import settings
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from knowledge.models import KnowledgeFile
from knowledge.serializers import (
    KnowledgeFileSerializer, KnowledgeSearchSerializer, FileUploadSerializer,
)
from course_agent_backend.minio_utils import MinIOClient


class KnowledgeViewSet(viewsets.ModelViewSet):
    serializer_class = KnowledgeFileSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = KnowledgeFile.objects.filter(user_id=self.request.user.username)
        course_id = self.request.query_params.get("course_id")
        if course_id:
            qs = qs.filter(course_id=course_id)
        return qs

    def create(self, request, *args, **kwargs):
        """上传文件 — 本地存储，异步向量化"""
        ser = FileUploadSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        f = ser.validated_data["file"]
        course_id = ser.validated_data["course_id"]
        course_name = ser.validated_data.get("course_name", "")
        doc_id = str(uuid.uuid4())[:12]
        ext = os.path.splitext(f.name)[1].lower()
        file_type_map = {".pdf": "pdf", ".docx": "docx", ".doc": "docx", ".txt": "txt", ".md": "md"}
        file_type = file_type_map.get(ext, "txt")

        # 本地存储
        local_dir = os.path.join(settings.MEDIA_ROOT, "knowledge", request.user.username, doc_id)
        os.makedirs(local_dir, exist_ok=True)
        local_path = os.path.join(local_dir, f.name)
        with open(local_path, "wb+") as dest:
            for chunk in f.chunks():
                dest.write(chunk)
        file_size = os.path.getsize(local_path)

        obj = KnowledgeFile.objects.create(
            user_id=request.user.username,
            course_id=course_id,
            course_name=course_name,
            doc_id=doc_id,
            file_name=f.name,
            file_path=local_path,
            file_type=file_type,
            file_size=file_size,
            chunks_count=0,
            status="uploaded",
        )

        # Async vectorize
        def _vectorize():
            try:
                from agent_core.tools.rag_retrieve_tool import RAGRetrieveTool
                rag = RAGRetrieveTool()
                result_raw = rag._run(
                    action="ingest", file_path=local_path,
                    course_id=course_id, _user_id=request.user.username,
                )
                import json
                result = json.loads(result_raw)
                if result.get("success"):
                    obj.status = "vectorized"
                    obj.chunks_count = result.get("chunks", 0)
                    obj.save(update_fields=["status", "chunks_count"])
            except Exception as e:
                import logging
                logging.getLogger(__name__).warning(f"Vectorize failed: {e}")

        threading.Thread(target=_vectorize, daemon=True).start()

        return Response({
            "code": 0, "msg": "上传成功",
            "data": KnowledgeFileSerializer(obj).data,
        }, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["post"])
    def search(self, request):
        """知识库语义检索"""
        ser = KnowledgeSearchSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        query = ser.validated_data["query"]
        course_id = ser.validated_data.get("course_id")
        top_k = ser.validated_data["top_k"]
        try:
            from agent_core.tools.rag_retrieve_tool import RAGRetrieveTool
            rag = RAGRetrieveTool()
            result_raw = rag._run(
                action="search", query=query, course_id=course_id,
                top_k=top_k, _user_id=request.user.username,
            )
            import json
            result = json.loads(result_raw)
            return Response({"code": 0, "msg": "检索成功", "data": result})
        except Exception as e:
            return Response({"code": 500, "msg": str(e), "data": None})

    @action(detail=True, methods=["get"])
    def preview(self, request, pk=None):
        """文档预览（返回下载URL）"""
        obj = self.get_object()
        url = MinIOClient.get_presigned_url(obj.file_path)
        return Response({"code": 0, "msg": "ok", "data": {"url": url, "file_name": obj.file_name}})

    def destroy(self, request, *args, **kwargs):
        obj = self.get_object()
        MinIOClient.delete_file(obj.file_path)
        obj.delete()
        return Response({"code": 0, "msg": "删除成功", "data": None})

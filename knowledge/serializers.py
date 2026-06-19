from rest_framework import serializers
from knowledge.models import KnowledgeFile


class KnowledgeFileSerializer(serializers.ModelSerializer):
    download_url = serializers.SerializerMethodField()

    class Meta:
        model = KnowledgeFile
        fields = [
            "id", "user_id", "course_id", "course_name", "doc_id",
            "file_name", "file_path", "file_type", "file_size",
            "chunks_count", "status", "download_url", "uploaded_at",
        ]
        read_only_fields = ["id", "doc_id", "file_size", "chunks_count", "status", "uploaded_at"]

    def get_download_url(self, obj):
        from course_agent_backend.minio_utils import MinIOClient
        return MinIOClient.get_presigned_url(f"knowledge/{obj.doc_id}/{obj.file_name}")


class KnowledgeSearchSerializer(serializers.Serializer):
    """知识库检索"""
    query = serializers.CharField(required=True)
    course_id = serializers.CharField(required=False, allow_blank=True)
    top_k = serializers.IntegerField(default=5, min_value=1, max_value=20)


class FileUploadSerializer(serializers.Serializer):
    """文件上传"""
    file = serializers.FileField(required=True)
    course_id = serializers.CharField(required=True)
    course_name = serializers.CharField(required=False, allow_blank=True)

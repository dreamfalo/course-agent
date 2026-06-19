"""
RAGRetrieveTool - RAG 检索增强生成工具
功能：PDF/Word/TXT 文档解析、文本分块、Chroma 向量入库、课程绑定检索
"""
import json
import logging
import os
import tempfile
from typing import Type, Optional, List, Dict, Any

from langchain_core.tools import BaseTool
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import (
    PyPDFLoader,
    Docx2txtLoader,
    TextLoader,
)
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from pydantic import BaseModel, Field

from agent_core.config import ChromaConfig

logger = logging.getLogger(__name__)


class RAGRetrieveInput(BaseModel):
    """RAG 检索工具输入 Schema"""
    action: str = Field(description="操作类型: ingest, search, list, delete")
    file_path: Optional[str] = Field(default=None, description="入库文档路径")
    course_id: Optional[str] = Field(default=None, description="绑定课程ID")
    query: Optional[str] = Field(default=None, description="检索查询文本")
    top_k: int = Field(default=5, description="返回结果数量")
    doc_id: Optional[str] = Field(default=None, description="文档ID")
    user_id: Optional[str] = Field(default=None, description="用户ID")


class RAGRetrieveTool(BaseTool):
    """RAG检索增强生成工具：文档解析 -> 分块 -> Chroma 入库 -> 课程绑定检索"""

    name: str = "rag_retrieve_tool"
    description: str = (
        "RAG检索增强生成工具。支持PDF/Word/TXT文档解析入Chroma向量库，"
        "基于课程绑定的语义检索。"
        "操作类型: ingest(文档入库), search(向量检索), list(列出文档), delete(删除文档)。"
    )
    args_schema: Type[BaseModel] = RAGRetrieveInput

    _chroma_config: ChromaConfig = ChromaConfig()
    _vectorstore: Optional[Chroma] = None
    _embeddings: Optional[OpenAIEmbeddings] = None
    _doc_index: Dict[str, Dict[str, Any]] = {}

    class Config:
        arbitrary_types_allowed = True

    def __init__(self, chroma_config: Optional[ChromaConfig] = None, **kwargs):
        super().__init__(**kwargs)
        if chroma_config:
            self._chroma_config = chroma_config
        self._embeddings = self._create_embeddings()
        if self._embeddings:
            self._init_vectorstore()

    def _create_embeddings(self) -> Optional[OpenAIEmbeddings]:
        """懒加载 Embeddings，容错处理"""
        try:
            api_key = os.environ.get("OPENAI_API_KEY", "test-dummy-key")
            return OpenAIEmbeddings(
                model=self._chroma_config.embedding_model,
                api_key=api_key,
            )
        except Exception as e:
            logger.warning(f"Failed to create embeddings: {e}")
            return None

    def _init_vectorstore(self):
        """初始化 Chroma 向量库"""
        try:
            persist_dir = self._chroma_config.persist_directory
            os.makedirs(persist_dir, exist_ok=True)
            self._vectorstore = Chroma(
                collection_name=self._chroma_config.collection_name,
                embedding_function=self._embeddings,
                persist_directory=persist_dir,
            )
            logger.info(f"Chroma vectorstore initialized at {persist_dir}")
        except Exception as e:
            logger.error(f"Failed to init vectorstore: {e}")
            self._vectorstore = None

    def _run(
        self,
        action: str,
        file_path: Optional[str] = None,
        course_id: Optional[str] = None,
        query: Optional[str] = None,
        top_k: int = 5,
        doc_id: Optional[str] = None,
        user_id: Optional[str] = None,
        _role: str = "student",
        _user_id: str = "",
        **kwargs,
    ) -> str:
        uid = user_id or _user_id
        try:
            if action == "ingest":
                return self._ingest_document(file_path, course_id, uid)
            elif action == "search":
                return self._search(query, course_id, top_k, uid)
            elif action == "list":
                return self._list_documents(uid, course_id)
            elif action == "delete":
                return self._delete_document(doc_id, uid)
            else:
                return json.dumps({"error": f"Unknown action: {action}"}, ensure_ascii=False)
        except Exception as e:
            logger.exception(f"RAGRetrieveTool error: {e}")
            return json.dumps({"error": str(e)}, ensure_ascii=False)

    def _ingest_document(
        self, file_path: Optional[str], course_id: Optional[str], uid: str
    ) -> str:
        if not file_path or not os.path.exists(file_path):
            return json.dumps({"error": f"File not found: {file_path}"}, ensure_ascii=False)
        if not course_id:
            return json.dumps({"error": "course_id is required for ingest"}, ensure_ascii=False)
        if not self._embeddings:
            return json.dumps({"error": "Embeddings not available"}, ensure_ascii=False)

        ext = os.path.splitext(file_path)[1].lower()
        if ext == ".pdf":
            loader = PyPDFLoader(file_path)
        elif ext in (".docx", ".doc"):
            loader = Docx2txtLoader(file_path)
        elif ext == ".txt":
            loader = TextLoader(file_path, encoding="utf-8")
        else:
            return json.dumps({"error": f"Unsupported format: {ext}"}, ensure_ascii=False)

        docs = loader.load()
        if not docs:
            return json.dumps({"error": "No content extracted"}, ensure_ascii=False)

        full_text = "\n".join([d.page_content for d in docs])
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self._chroma_config.chunk_size,
            chunk_overlap=self._chroma_config.chunk_overlap,
            separators=["\n\n", "\n", "。", ".", " ", ""],
        )
        chunks = text_splitter.split_text(full_text)
        if not chunks:
            return json.dumps({"error": "No chunks produced"}, ensure_ascii=False)

        metadatas = [
            {
                "course_id": course_id, "user_id": uid,
                "source": os.path.basename(file_path),
                "chunk_index": i, "total_chunks": len(chunks),
            }
            for i in range(len(chunks))
        ]

        doc_id_prefix = f"{uid}_{course_id}_{os.path.basename(file_path)}"
        ids = [f"{doc_id_prefix}_chunk_{i}" for i in range(len(chunks))]

        if self._vectorstore:
            self._vectorstore.add_texts(texts=chunks, metadatas=metadatas, ids=ids)

        self._doc_index[doc_id_prefix] = {
            "doc_id": doc_id_prefix,
            "file_name": os.path.basename(file_path),
            "course_id": course_id, "user_id": uid,
            "chunks": len(chunks),
        }

        logger.info(f"Document ingested: {file_path} -> {len(chunks)} chunks")
        return json.dumps({
            "success": True, "doc_id": doc_id_prefix,
            "file_name": os.path.basename(file_path),
            "course_id": course_id, "chunks": len(chunks),
        }, ensure_ascii=False)

    def _search(
        self, query: Optional[str], course_id: Optional[str], top_k: int, uid: str
    ) -> str:
        if not query:
            return json.dumps({"error": "query is required"}, ensure_ascii=False)
        if not self._vectorstore:
            return json.dumps({"error": "Vectorstore not initialized"}, ensure_ascii=False)

        filter_dict: Dict[str, Any] = {"user_id": uid}
        if course_id:
            filter_dict["course_id"] = course_id

        try:
            results = self._vectorstore.similarity_search(query, k=top_k, filter=filter_dict)
        except Exception:
            results = self._vectorstore.similarity_search(query, k=top_k)

        formatted = [
            {"content": doc.page_content[:300], "metadata": doc.metadata}
            for doc in results
        ]
        return json.dumps({
            "success": True, "query": query,
            "results_count": len(formatted), "results": formatted,
        }, ensure_ascii=False)

    def _list_documents(self, uid: str, course_id: Optional[str] = None) -> str:
        docs = list(self._doc_index.values())
        docs = [d for d in docs if d.get("user_id") == uid]
        if course_id:
            docs = [d for d in docs if d.get("course_id") == course_id]
        return json.dumps({
            "success": True, "total": len(docs), "documents": docs,
        }, ensure_ascii=False)

    def _delete_document(self, doc_id: Optional[str], uid: str) -> str:
        if not doc_id:
            return json.dumps({"error": "doc_id is required"}, ensure_ascii=False)
        if doc_id in self._doc_index:
            del self._doc_index[doc_id]
            return json.dumps({"success": True, "deleted": doc_id}, ensure_ascii=False)
        return json.dumps({"error": f"Document not found: {doc_id}"}, ensure_ascii=False)

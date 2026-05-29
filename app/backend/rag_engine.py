"""
RAG 知识库引擎
本地文档向量化 + 检索增强生成
"""
import os
from pathlib import Path
from typing import List, Optional
import json


class Document:
    """文档块"""
    def __init__(self, content: str, metadata: dict = None):
        self.content = content
        self.metadata = metadata or {}

    def __repr__(self):
        return f"<Doc: {self.content[:50]}...>"


class RAGConfig:
    """RAG配置"""
    def __init__(
        self,
        chunk_size: int = 512,
        chunk_overlap: int = 64,
        top_k: int = 5,
        similarity_threshold: float = 0.5,
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.top_k = top_k
        self.similarity_threshold = similarity_threshold


class RAGEngine:
    """本地RAG引擎"""
    def __init__(self, kb_dir: str = "knowledge_base", config: RAGConfig = None):
        self.kb_dir = Path(kb_dir)
        self.kb_dir.mkdir(exist_ok=True)
        self.config = config or RAGConfig()
        self._embedding_model = None
        self._vector_store = None
        self._texts = []
        self._metadatas = []
        self._indexed = False

    def _get_embedding_model(self):
        """延迟加载embedding模型"""
        if self._embedding_model is None:
            from sentence_transformers import SentenceTransformer
            # 使用轻量中文embedding模型
            self._embedding_model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
        return self._embedding_model

    def _chunk_text(self, text: str) -> List[str]:
        """文本分块"""
        chunk_size = self.config.chunk_size
        overlap = self.config.chunk_overlap
        chunks = []
        start = 0
        text_len = len(text)
        while start < text_len:
            end = start + chunk_size
            chunks.append(text[start:end])
            start += chunk_size - overlap
        return chunks

    def _load_pdf(self, pdf_path: Path) -> str:
        """读取PDF文本"""
        try:
            from pypdf import PdfReader
            reader = PdfReader(str(pdf_path))
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            return text
        except Exception as e:
            return f"[PDF读取失败: {e}]"

    def add_document(self, file_path: str, doc_name: str = None) -> int:
        """添加文档到知识库"""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")

        name = doc_name or path.stem
        ext = path.suffix.lower()

        # 读取文本
        if ext == ".pdf":
            text = self._load_pdf(path)
        elif ext in [".txt", ".md"]:
            text = path.read_text(encoding="utf-8")
        else:
            raise ValueError(f"不支持的文件格式: {ext}")

        # 分块
        chunks = self._chunk_text(text)
        for chunk in chunks:
            self._texts.append(chunk)
            self._metadatas.append({"source": name, "file": str(path)})

        self._indexed = False
        return len(chunks)

    def build_index(self):
        """构建向量索引"""
        if not self._texts:
            return

        import faiss
        model = self._get_embedding_model()

        # 向量化
        embeddings = model.encode(self._texts, show_progress_bar=True)
        dim = embeddings.shape[1]

        # 构建FAISS索引
        self._vector_store = faiss.IndexFlatL2(dim)
        self._vector_store.add(embeddings.astype("float32"))
        self._indexed = True

    def search(self, query: str, top_k: int = None) -> List[Document]:
        """检索相关文档"""
        if not self._indexed:
            self.build_index()

        top_k = top_k or self.config.top_k
        model = self._get_embedding_model()

        # 查询向量化
        q_emb = model.encode([query]).astype("float32")

        # 检索
        distances, indices = self._vector_store.search(q_emb, top_k * 2)

        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx < len(self._texts):
                # L2距离转相似度（简单近似）
                score = max(0, 1 - dist / 100)
                if score >= self.config.similarity_threshold:
                    results.append(Document(
                        content=self._texts[idx],
                        metadata={**self._metadatas[idx], "score": float(score)}
                    ))

        return results[:top_k]

    def query_with_context(self, question: str, top_k: int = None) -> tuple[str, List[Document]]:
        """带上下文检索"""
        docs = self.search(question, top_k)
        if not docs:
            return "", []
        context = "\n\n".join(d.content for d in docs)
        return context, docs

    def get_stats(self) -> dict:
        """获取知识库统计"""
        return {
            "total_chunks": len(self._texts),
            "indexed": self._indexed,
            "kb_files": [f.name for f in self.kb_dir.iterdir() if f.is_file()],
        }
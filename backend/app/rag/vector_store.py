import os
import asyncio
import re
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document
from typing import List, Dict, Any, Optional

try:
    import torch
except Exception:
    torch = None

from app.core.config import settings

class VectorStoreManager:
    def __init__(self):
        device = "cpu"
        if torch is not None and torch.cuda.is_available():
            device = "cuda"

        model_kwargs = {"device": device}
        encode_kwargs = {"normalize_embeddings": True}
        
        self.embeddings = HuggingFaceEmbeddings(
            model_name=settings.EMBEDDING_MODEL,
            model_kwargs=model_kwargs,
            encode_kwargs=encode_kwargs
        )
        
        self.persist_directory = settings.CHROMA_PERSIST_DIR
        os.makedirs(self.persist_directory, exist_ok=True)

        self.chunk_size = settings.CHUNK_SIZE
        self.chunk_overlap = settings.CHUNK_OVERLAP

    def _split_documents(self, documents: List[Document]) -> List[Document]:
        chunks: List[Document] = []
        step = max(1, self.chunk_size - self.chunk_overlap)

        for doc in documents:
            text = doc.page_content or ""
            if len(text) <= self.chunk_size:
                chunks.append(doc)
                continue

            for start in range(0, len(text), step):
                end = start + self.chunk_size
                chunk_text = text[start:end].strip()
                if not chunk_text:
                    continue
                chunks.append(Document(page_content=chunk_text, metadata=doc.metadata))
                if end >= len(text):
                    break

        return chunks

    def _is_noise_chunk(self, text: str) -> bool:
        cleaned = (text or "").strip()
        if not cleaned:
            return True

        words = re.findall(r"[A-Za-z]{2,}", cleaned)
        if len(words) < 25:
            return True

        alpha_chars = sum(1 for c in cleaned if c.isalpha())
        alpha_ratio = alpha_chars / max(1, len(cleaned))
        if alpha_ratio < 0.45:
            return True

        low_value_terms = [
            "all rights reserved",
            "author contributions",
            "conflicts of interest",
            "references",
            "copyright",
        ]
        lowered = cleaned.lower()
        if any(term in lowered for term in low_value_terms):
            return True

        return False

    def _get_collection(self, chat_id: str):
        """Retourne une instance Chroma spécifique pour un chat_id."""
        return Chroma(
            collection_name=f"chat_{chat_id}",
            embedding_function=self.embeddings,
            persist_directory=self.persist_directory
        )

    async def add_documents_batched(
        self,
        parsed_docs: List[Dict[str, Any]],
        chat_id: str,
        batch_size: int,
        sleep_seconds: float,
    ) -> Dict[str, int]:
        """Add chunks in smaller batches to reduce CPU spikes during indexing."""
        langchain_docs = [
            Document(page_content=d["page_content"], metadata=d["metadata"])
            for d in parsed_docs
        ]
        chunks = self._split_documents(langchain_docs)

        filtered_chunks = [chunk for chunk in chunks if not self._is_noise_chunk(chunk.page_content)]
        dropped = max(0, len(chunks) - len(filtered_chunks))

        if not filtered_chunks:
            return {"chunks_added": 0, "chunks_dropped": dropped}

        vector_store = self._get_collection(chat_id)
        for i in range(0, len(filtered_chunks), max(1, batch_size)):
            batch = filtered_chunks[i : i + max(1, batch_size)]
            await asyncio.to_thread(vector_store.add_documents, batch)
            await asyncio.sleep(max(0.0, sleep_seconds))

        return {"chunks_added": len(filtered_chunks), "chunks_dropped": dropped}

    def add_documents(self, parsed_docs: List[Dict[str, Any]], chat_id: str):
        """Découpe les documents en chunks et les ajoute dans une collection isolée."""
        langchain_docs = [
            Document(page_content=d["page_content"], metadata=d["metadata"])
            for d in parsed_docs
        ]
        
        chunks = [c for c in self._split_documents(langchain_docs) if not self._is_noise_chunk(c.page_content)]
        
        if chunks:
            vector_store = self._get_collection(chat_id)
            vector_store.add_documents(documents=chunks)

    def search_documents(self, query: str, chat_id: str, top_k: int = None) -> List[Document]:
        """Recherche sémantique restreinte à un chat_id."""
        k = top_k or settings.TOP_K_RETRIEVAL
        vector_store = self._get_collection(chat_id)
        return vector_store.similarity_search(query, k=k)

    def delete_collection_data(self, chat_id: str):
        """Supprime les données associées à un chat."""
        # Supprimer physiquement la collection (version safe)
        try:
            vector_store = self._get_collection(chat_id)
            vector_store.delete_collection()
        except Exception:
            pass

_vector_mgr: Optional[VectorStoreManager] = None


def get_vector_manager() -> VectorStoreManager:
    global _vector_mgr
    if _vector_mgr is None:
        _vector_mgr = VectorStoreManager()
    return _vector_mgr

from typing import List, Tuple

from langchain_core.documents import Document

from app.core.config import settings


def estimate_text_tokens(text: str) -> int:
    if not text:
        return 0
    ratio = max(1, settings.TOKEN_ESTIMATE_CHARS_PER_TOKEN)
    return max(1, len(text) // ratio)


def estimate_documents_tokens(documents: List[Document]) -> int:
    return sum(estimate_text_tokens(doc.page_content) for doc in documents)


def pack_documents_by_budget(documents: List[Document], max_tokens: int) -> Tuple[List[Document], int]:
    """Pack documents greedily while respecting a token budget estimate."""
    selected: List[Document] = []
    used = 0

    for doc in documents:
        doc_tokens = estimate_text_tokens(doc.page_content)
        if used + doc_tokens > max_tokens:
            continue
        selected.append(doc)
        used += doc_tokens

    return selected, used

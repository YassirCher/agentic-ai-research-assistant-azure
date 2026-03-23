from typing import Any, Dict


def extract_total_tokens(response: Any) -> int:
    """Best-effort token extraction from LangChain/Groq responses."""
    if response is None:
        return 0

    metadata: Dict[str, Any] = getattr(response, "response_metadata", {}) or {}
    usage = metadata.get("token_usage") or metadata.get("usage") or {}

    for key in ("total_tokens", "total", "prompt_tokens"):
        value = usage.get(key)
        if isinstance(value, int):
            return value

    usage_metadata: Dict[str, Any] = getattr(response, "usage_metadata", {}) or {}
    value = usage_metadata.get("total_tokens")
    if isinstance(value, int):
        return value

    return 0

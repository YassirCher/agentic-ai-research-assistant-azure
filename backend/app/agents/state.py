from typing import Annotated, List, TypedDict
import operator
from langchain_core.documents import Document

class AgentState(TypedDict):
    """
    État global du graphe LangGraph.
    """
    question: str
    chat_id: str # ID de la session pour l'isolation ChromaDB
    documents: List[Document]
    generation: str
    loop_count: int
    needs_rag: bool
    is_valid: bool
    # Utilisation de reducers pour l'accumulation automatique
    agent_steps: Annotated[list, operator.add]
    total_tokens: Annotated[int, operator.add]

from app.agents.state import AgentState
from app.rag.vector_store import get_vector_manager

def retriever_node(state: AgentState):
    """
    Interroge la base de données vectorielle ChromaDB
    pour récupérer le contexte pertinent.
    """
    question = state["question"]
    chat_id = state["chat_id"]
    docs = get_vector_manager().search_documents(question, chat_id=chat_id)
    
    step = {
        "agent": "Retriever",
        "icon": "🔍",
        "action": "Recherche de contexte",
        "detail": f"{len(docs)} documents récupérés.",
        "response": "\n\n".join([f"Source: {d.metadata.get('source')}\n{d.page_content}" for d in docs]) if docs else "Aucun document trouvé."
    }
    # Avec le reducer operator.add, on retourne juste le nouveau step dans une liste
    return {"documents": docs, "question": question, "agent_steps": [step]}

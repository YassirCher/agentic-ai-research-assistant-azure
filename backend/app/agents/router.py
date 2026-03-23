from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from app.api.dependencies import get_fast_llm
from app.agents.state import AgentState

class RouteQuery(BaseModel):
    """Router un prompt vers RAG ou standard chat."""
    datasource: str = Field(
        ...,
        description="Given a user question choose to route it to 'vectorstore' or 'direct_chat'."
    )

def router_node(state: AgentState):
    """
    Analyse la question pour décider s'il faut chercher dans la base ChromaDB
    ou si on peut répondre directement (salutations, questions générales).
    """
    question = state["question"]
    llm = get_fast_llm()
    structured_llm_router = llm.with_structured_output(RouteQuery)

    system = """You are an expert at routing a user question to a vectorstore or direct_chat.
    The vectorstore contains documents related to scientific research and articles provided by the user.
    Use the vectorstore for questions on these topics. Otherwise, use direct_chat.
    For simple greetings (Hello, hi) -> direct_chat.
    """
    route_prompt = ChatPromptTemplate.from_messages([
        ("system", system),
        ("human", "{question}"),
    ])
    
    question_router = route_prompt | structured_llm_router
    try:
        source = question_router.invoke({"question": question})
        needs_rag = source.datasource == "vectorstore"
        tokens = 0
        if hasattr(source, "response_metadata"):
             tokens = source.datasource.response_metadata.get("token_usage", {}).get("total_tokens", 0)
    except Exception as e:
        needs_rag = True
        tokens = 0
        
    step = {
        "agent": "Router",
        "icon": "🚦",
        "action": "Analyse de l'intention",
        "detail": "Redirection vers la base documentaire (RAG)." if needs_rag else "Réponse directe par l'assistant.",
        "response": f"Source choisie : {'VectorStore' if needs_rag else 'Direct Chat'}",
        "tokens": tokens
    }
        
    return {"needs_rag": needs_rag, "agent_steps": [step], "total_tokens": tokens}

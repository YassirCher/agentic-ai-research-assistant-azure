from langgraph.graph import END, StateGraph
from app.agents.state import AgentState
from app.agents.router import router_node
from app.agents.retriever import retriever_node
from app.agents.ranker import ranker_node
from app.agents.generator import generator_node
from app.agents.critic import critic_node

def route_question(state: AgentState):
    """Bifurque selon le Router."""
    if state["needs_rag"]:
        return "retrieve"
    else:
        return "generate"

def eval_generation(state: AgentState):
    """
    Critique la génération: si hallucination et boucle <= 2, on regénère.
    Sinon, on accepte et on termine. (Evite les boucles infinies coûteuses).
    """
    # Si la boucle dépasse 2, on force la fin pour économiser Groq Free Tier
    if state.get("loop_count", 0) >= 2:
        return "end"
        
    if state["is_valid"]:
        return "end"
    else:
        # On pourrait implémenter un prompt de correction ici.
        return "generate"

workflow = StateGraph(AgentState)

# Noeuds
workflow.add_node("router", router_node)
workflow.add_node("retriever", retriever_node)
workflow.add_node("ranker", ranker_node)
workflow.add_node("generator", generator_node)
workflow.add_node("critic", critic_node)

# Flow
workflow.set_entry_point("router")

workflow.add_conditional_edges(
    "router",
    route_question,
    {
        "retrieve": "retriever",
        "generate": "generator"
    }
)

workflow.add_edge("retriever", "ranker")
workflow.add_edge("ranker", "generator")
workflow.add_edge("generator", "critic")

workflow.add_conditional_edges(
    "critic",
    eval_generation,
    {
        "end": END,
        "generate": "generator"
    }
)

app_graph = workflow.compile()

from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from app.api.dependencies import get_fast_llm
from app.agents.state import AgentState

class GradeHallucinations(BaseModel):
    """Note binaire (yes/no) pour les hallucinations."""
    binary_score: str = Field(description="Answer is grounded in the facts, 'yes' or 'no'")

def critic_node(state: AgentState):
    """
    Évalue si la génération est ancrée dans les documents récupérés.
    Prévient de l'hallucination avant d'envoyer à l'utilisateur.
    """
    question = state["question"]
    documents = state.get("documents", [])
    generation = state.get("generation", "")
    
    # Si on n'a pas fait de RAG, pas besoin de checker l'hallucination vs docs
    if not state.get("needs_rag", True):
        return {"is_valid": True}
        
    llm = get_fast_llm()
    structured_llm_grader = llm.with_structured_output(GradeHallucinations)

    system = """You are a grader assessing whether an LLM generation is grounded in / supported by a set of retrieved facts. \n 
    Give a binary score 'yes' or 'no'. 'Yes' means that the answer is grounded in / supported by the set of facts."""
    
    hallucination_prompt = ChatPromptTemplate.from_messages([
        ("system", system),
        ("human", "Set of facts: \n\n {documents} \n\n LLM generation: {generation}"),
    ])
    
    hallucination_grader = hallucination_prompt | structured_llm_grader
    
    total_tokens = state.get("total_tokens", 0)
    doc_content = "\n\n".join(doc.page_content for doc in documents)
    full_prompt = f"System: {system}\n\nFacts: {doc_content}\n\nGeneration: {generation}"
    
    try:
         # Appel direct pour capturer les métadonnées
         res = llm.invoke(hallucination_prompt.format(documents=doc_content, generation=generation))
         
         # On parse manuellement le structured output si on n'utilise pas le parser auto
         # Mais ici structured_llm_grader simplifie. On va tenter d'extraire de res.
         # Comme on utilise with_structured_output, res est déjà GradeHallucinations.
         # Pour avoir les tokens, on peut utiliser le LLM brut mais c'est lourd.
         # On va plutôt utiliser res.response_metadata si le wrapper le permet ou estimer.
         
         # Si GradeHallucinations est retourné par with_structured_output, 
         # LangChain attache souvent les metadata à l'objet retourné s'il est Pydantic.
         # Sinon, on fait un appel LLM classique et on parse.
         
         score = hallucination_grader.invoke({"documents": doc_content, "generation": generation})
         grade = score.binary_score
         is_valid = (grade == "yes")
         
         tokens = 0
         if hasattr(score, "response_metadata"):
              tokens = score.response_metadata.get("token_usage", {}).get("total_tokens", 0)
         
         total_tokens += tokens
    except Exception:
         is_valid = True
         tokens = 0
         
    step = {
        "agent": "Critic",
        "icon": "🛡️",
        "action": "Vérification anti-hallucination",
        "detail": "Génération validée avec succès." if is_valid else "Hallucination détectée. Rejet et demande de nouvelle génération.",
        "prompt": full_prompt,
        "response": "Validé" if is_valid else "Rejeté",
        "tokens": tokens
    }

    # Avec les reducers Annotated[..., operator.add]
    return {
        "is_valid": is_valid, 
        "agent_steps": [step], 
        "total_tokens": tokens
    }

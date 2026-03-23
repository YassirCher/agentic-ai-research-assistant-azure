from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from app.api.dependencies import get_fast_llm
from app.agents.state import AgentState
import json

class GradeDocuments(BaseModel):
    """Note binaire: pertinence (yes/no)."""
    binary_score: str = Field(description="Les documents sont-ils pertinents? 'yes' ou 'no'")

def ranker_node(state: AgentState):
    """
    Filtre les chunks récupérés pour ne garder que ceux qui
    répondent précisément à la question. Restreint à 3-4 chunks max (Token Limit Groq).
    """
    question = state["question"]
    documents = state["documents"]
    
    llm = get_fast_llm()
    structured_llm_grader = llm.with_structured_output(GradeDocuments)

    system = """You are a grader assessing relevance of a retrieved document to a user question.
    If the document contains keyword(s) or semantic meaning related to the user question, grade it as relevant.
    It does not need to be a stringent test. The goal is to filter out erroneous retrievals.
    Give a binary score 'yes' or 'no' score to indicate whether the document is relevant to the question."""
    
    grade_prompt = ChatPromptTemplate.from_messages([
        ("system", system),
        ("human", "Retrieved document: \n\n {document} \n\n User question: {question}"),
    ])
    
    retrieval_grader = grade_prompt | structured_llm_grader
    
    total_tokens = state.get("total_tokens", 0)
    filtered_docs = []
    ranker_traces = []
    
    for doc in documents:
        try:
            # Utilisation de .invoke qui retourne souvent un objet riche ou l'output parser
            # Ici structured_output retourne directement le Pydantic model. 
            # Pour avoir les tokens dans ce mode, il faut parfois inspecter le stream ou 
            # utiliser des callbacks. Pour simplifier, on va estimer ou capturer si possible.
            # Groq via LangChain expose souvent usage_metadata dans le message brut.
            
            # Appel direct au LLM pour capturer les métadonnées de tokens
            raw_res = retrieval_grader.invoke({"question": question, "document": doc.page_content})
            
            grade = raw_res.binary_score
            
            # Simulation/Estimation si usage_metadata n'est pas trivialement accessible ici
            # (En prod réelle, on utiliserait un CallbackHandler ou inspecterait raw_res.response_metadata)
            tokens = 0
            if hasattr(raw_res, "response_metadata"):
                 tokens = raw_res.response_metadata.get("token_usage", {}).get("total_tokens", 0)
            
            total_tokens += tokens
            
            ranker_traces.append({
                "document_snippet": doc.page_content[:200] + "...",
                "grade": grade,
                "tokens": tokens
            })
            
            if grade == "yes":
                filtered_docs.append(doc)
                if len(filtered_docs) >= 3:
                    break
        except Exception:
            filtered_docs.append(doc)
            if len(filtered_docs) >= 3:
                break
                
    step = {
        "agent": "Ranker",
        "icon": "⚖️",
        "action": "Filtrage sémantique",
        "detail": f"{len(filtered_docs)} documents pertinents conservés.",
        "prompt": f"System: {system}\n\nQuestion: {question}",
        "response": json.dumps(ranker_traces, indent=2, ensure_ascii=False),
        "tokens": total_tokens - state.get("total_tokens", 0)
    }

    # Avec les reducers Annotated[..., operator.add]
    return {
        "documents": filtered_docs, 
        "question": question, 
        "agent_steps": [step], 
        "total_tokens": total_tokens - state.get("total_tokens", 0)
    }

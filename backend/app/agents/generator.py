from langchain_core.prompts import ChatPromptTemplate
import logging
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type

from app.api.dependencies import get_fast_llm, get_smart_llm
from app.agents.state import AgentState
from app.core.config import settings
from app.core.token_budget import estimate_text_tokens, pack_documents_by_budget
from app.core.token_usage import extract_total_tokens

logger = logging.getLogger("uvicorn.error")

def format_docs(docs):
    """Formate les chunks en texte avec leurs métadonnées pour le générateur."""
    return "\n\n".join(
        f"--- Source: {doc.metadata.get('source', 'Inconnu')} (Page: {doc.metadata.get('page', 'Inconnue')}) ---\n{doc.page_content}"
        for doc in docs
    )


@retry(
    reraise=True,
    wait=wait_exponential(multiplier=1, min=1, max=8),
    stop=stop_after_attempt(3),
    retry=retry_if_exception_type(Exception),
)
def _invoke_with_retry(llm, prompt_value):
    return llm.invoke(prompt_value)


def _invoke_with_fallback(primary_llm, fallback_llm, prompt_value):
    try:
        return _invoke_with_retry(primary_llm, prompt_value), "smart"
    except Exception as primary_err:
        logger.warning("Generator primary model failed, fallback engaged: %s", str(primary_err))
        return _invoke_with_retry(fallback_llm, prompt_value), "fast"

def generator_node(state: AgentState):
    """
    Utilise le LLM puissant (Llama-3-70b/Mixtral) pour rédiger la réponse
    basée UNIQUEMENT sur les chunks vérifiés (Anti-hallucination + Grounding).
    """
    question = state["question"]
    documents = state.get("documents", [])
    
    smart_llm = get_smart_llm()
    fast_llm = get_fast_llm()
    
    # Prompting structuré
    system = """You are an expert academic research assistant.
    Use ONLY the context below to answer the user's question.
    If the answer is not in the context, say "Je ne peux pas répondre basé sur les documents fournis."
    
    CRITICAL: For every claim you make, you MUST cite the exact source and page number precisely as they appear in the Context.
    Format your citation like this: [DocumentName.pdf, Page X].
    Respond in the same language as the user's query (default to French).
    
    Context:
    {context}
    """
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system),
        ("human", "Question: {question}"),
    ])
    
    consumed_before_generator = state.get("total_tokens", 0)
    available_total = (
        settings.TOKEN_BUDGET_TOTAL
        - consumed_before_generator
        - settings.TOKEN_BUDGET_SAFETY_MARGIN
    )
    generator_budget = max(0, min(settings.TOKEN_BUDGET_GENERATOR, available_total))

    total_tokens = 0
    context_text = format_docs(documents)
    
    # Construction du prompt final pour la trace
    full_prompt = f"System: {system}\n\nContext: {context_text}\n\nQuestion: {question}"

    if generator_budget <= 0:
        generation = (
            "Quota de tokens proche de la limite. J'active le mode condense. "
            "Veuillez reformuler une question plus precise ou reduire le contexte."
        )
        step = {
            "agent": "Generator",
            "icon": "✍️",
            "action": "Génération de la réponse",
            "detail": "Budget token insuffisant, generation bloquee proprement.",
            "model": "budget_guard",
            "prompt": full_prompt,
            "response": generation,
            "tokens": 0,
            "budget": {
                "total_budget": settings.TOKEN_BUDGET_TOTAL,
                "consumed_before": consumed_before_generator,
                "generator_budget": generator_budget,
                "fallback": "blocked",
            },
        }
        return {
            "generation": generation,
            "question": question,
            "loop_count": state.get("loop_count", 0) + 1,
            "agent_steps": [step],
            "total_tokens": 0,
        }
    
    try:
        if not documents and state.get("needs_rag", True):
            generation = "Aucun document pertinent n'a été trouvé pour répondre à cette question."
            tokens = 0
            used_model = "no_context"
            fallback_mode = "none"
        elif not state.get("needs_rag", True):
            direct_prompt = ChatPromptTemplate.from_messages([
                ("system", "You are a helpful AI assistant. Answer directly to the user greeting or general statement."),
                ("human", "{question}"),
            ])
            res, used_model = _invoke_with_fallback(
                smart_llm,
                fast_llm,
                direct_prompt.format(question=question),
            )
            generation = res.content
            tokens = extract_total_tokens(res)
            fallback_mode = "none"
        else:
            prompt_overhead = estimate_text_tokens(system + question)
            max_context_tokens = max(0, generator_budget - prompt_overhead)

            selected_docs, used_context_tokens = pack_documents_by_budget(documents, max_context_tokens)
            if not selected_docs and documents and max_context_tokens > 0:
                selected_docs = documents[:1]

            context_text = format_docs(selected_docs)
            full_prompt = f"System: {system}\n\nContext: {context_text}\n\nQuestion: {question}"

            projected_total = prompt_overhead + used_context_tokens
            overflow = projected_total > generator_budget
            fallback_mode = "condensed" if overflow or len(selected_docs) < len(documents) else "none"

            primary_model = fast_llm if overflow else smart_llm
            secondary_model = fast_llm

            res, used_model = _invoke_with_fallback(
                primary_model,
                secondary_model,
                prompt.format(context=context_text, question=question),
            )
            generation = res.content
            tokens = extract_total_tokens(res)

    except Exception as e:
        import traceback
        logger.error("Erreur critique dans Generator Node:")
        logger.error(traceback.format_exc())
        generation = "Je rencontre une difficulté temporaire avec le modèle. Veuillez réessayer dans quelques secondes."
        tokens = 0
        used_model = "none"
        fallback_mode = "error"
        
    step = {
        "agent": "Generator",
        "icon": "✍️",
        "action": "Génération de la réponse",
        "detail": "Rédaction terminée." if used_model != "none" else "Échec de génération.",
        "model": used_model,
        "prompt": full_prompt,
        "response": generation,
        "tokens": tokens,
        "budget": {
            "total_budget": settings.TOKEN_BUDGET_TOTAL,
            "consumed_before": consumed_before_generator,
            "generator_budget": generator_budget,
            "fallback": fallback_mode,
        },
    }

    # Avec les reducers Annotated[..., operator.add]
    return {
        "generation": generation, 
        "question": question, 
        "loop_count": state.get("loop_count", 0) + 1, 
        "agent_steps": [step],
        "total_tokens": tokens
    }

import os
from langchain_groq import ChatGroq
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type
from app.core.config import settings
from groq import RateLimitError # or whatever langchain-groq throws

# Retries asynchrones pour gérer le Free Tier de Groq (HTTP 429)
def get_groq_llm(model_name: str, temperature: float = 0.0):
    """
    Initialise le client LangChain pour Groq avec gestion des limites de requêtes.
    """
    if not settings.GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY is not configured")

    return ChatGroq(
        groq_api_key=settings.GROQ_API_KEY,
        model_name=model_name,
        temperature=temperature,
        max_tokens=settings.TOKEN_BUDGET_GENERATOR,
        max_retries=3,  # LangChain gère nativement quelques retries pour les 429
        request_timeout=45,
    )

def get_fast_llm():
    """Modèle rapide pour le Router, Ranker, Critic"""
    return get_groq_llm(model_name=settings.GROQ_FAST_MODEL, temperature=0.0)

def get_smart_llm():
    """Modèle puissant (Generator) pour la rédaction finale"""
    return get_groq_llm(model_name=settings.GROQ_SMART_MODEL, temperature=0.2)

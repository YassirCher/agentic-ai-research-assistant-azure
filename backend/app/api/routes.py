from fastapi import APIRouter, File, UploadFile, HTTPException, Depends, Request, BackgroundTasks
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel
from typing import AsyncGenerator, Dict, List
import json
import uuid
import asyncio
from sqlmodel import Session, select

from app.rag.document_parser import parse_pdf_from_bytes
from app.rag.vector_store import get_vector_manager
from app.agents.graph import app_graph
from app.db.database import get_session, Chat, Message
from app.core.config import settings
from app.core.rate_limit import rate_limiter
from app.core.upload_jobs import upload_job_store

router = APIRouter()

class QueryRequest(BaseModel):
    question: str
    chat_id: str


def _client_identifier(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client and request.client.host:
        return request.client.host
    return "unknown"


def _enforce_rate_limit(request: Request, scope: str):
    if scope == "upload":
        limit = settings.RATE_LIMIT_UPLOAD
    else:
        limit = settings.RATE_LIMIT_QUERY

    allowed = rate_limiter.check(
        key=f"{scope}:{_client_identifier(request)}",
        limit=limit,
        window_seconds=settings.RATE_LIMIT_WINDOW_SECONDS,
    )
    if not allowed:
        raise HTTPException(
            status_code=429,
            detail={
                "message": "Trop de requetes. Reessayez dans quelques instants.",
                "error_code": "RATE_LIMIT_EXCEEDED",
            },
        )


def _safe_server_error(code: str = "INTERNAL_SERVER_ERROR") -> HTTPException:
    return HTTPException(
        status_code=500,
        detail={
            "message": "Une erreur interne est survenue. Veuillez reessayer.",
            "error_code": code,
        },
    )


async def _process_upload_background(chat_id: str, valid_files: List[Dict[str, bytes]]):
    """Parse and index files in background to keep upload response fast and UI fluid."""
    for file_item in valid_files:
        filename = file_item["filename"]
        content = file_item["content"]

        try:
            upload_job_store.mark_file_processing(chat_id, filename)
            parsed_docs = parse_pdf_from_bytes(content, filename)
            if not parsed_docs:
                upload_job_store.mark_file_error(
                    chat_id,
                    filename,
                    "Aucun texte exploitable detecte dans le PDF",
                )
                continue

            result = await get_vector_manager().add_documents_batched(
                parsed_docs,
                chat_id=chat_id,
                batch_size=settings.EMBEDDING_BATCH_SIZE,
                sleep_seconds=settings.EMBEDDING_BATCH_SLEEP_SECONDS,
            )
            upload_job_store.mark_file_done(
                chat_id,
                filename,
                pages_extracted=len(parsed_docs),
                chunks_added=result["chunks_added"],
                chunks_dropped=result["chunks_dropped"],
            )
        except Exception:
            logger.exception("Background indexing failed for %s", filename)
            upload_job_store.mark_file_error(
                chat_id,
                filename,
                "Echec pendant l'indexation en arriere-plan",
            )

        await asyncio.sleep(settings.EMBEDDING_BATCH_SLEEP_SECONDS)

    upload_job_store.finalize(chat_id)

@router.post("/upload")
async def upload_pdfs(
    request: Request,
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...), 
    db: Session = Depends(get_session)
):
    """
    Crée un nouveau Chat et indexe plusieurs PDF dans une collection dédiée.
    Le titre est basé sur le nom du premier fichier.
    """
    _enforce_rate_limit(request, "upload")

    if not files:
        raise HTTPException(status_code=400, detail="Aucun fichier fourni")
    if len(files) > settings.MAX_UPLOAD_FILES:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Nombre maximal de fichiers depasse: {settings.MAX_UPLOAD_FILES}"
            ),
        )
        
    chat_id = str(uuid.uuid4())
    
    # Titre intelligent basé sur les noms de fichiers
    first_filename = files[0].filename.replace(".pdf", "").replace(".PDF", "")
    if len(files) > 1:
        chat_title = f"{first_filename} + {len(files)-1} autres"
    else:
        chat_title = first_filename

    new_chat = Chat(id=chat_id, title=chat_title)
    db.add(new_chat)
    db.commit()
    db.refresh(new_chat)
    
    file_results = []
    valid_files: List[Dict[str, bytes]] = []
    
    try:
        for file in files:
            result = {
                "filename": file.filename,
                "status": "skipped",
                "pages_extracted": 0,
                "chunks_added": 0,
                "message": "",
            }

            if not file.filename.lower().endswith(".pdf"):
                result["status"] = "error"
                result["message"] = "Format invalide: seuls les PDF sont acceptes"
                file_results.append(result)
                continue

            content = await file.read()
            file_size_mb = len(content) / (1024 * 1024)
            if file_size_mb > settings.MAX_UPLOAD_FILE_MB:
                result["status"] = "error"
                result["message"] = (
                    f"Fichier trop volumineux (>{settings.MAX_UPLOAD_FILE_MB} MB)"
                )
                file_results.append(result)
                continue

            result["status"] = "queued"
            result["message"] = "En attente de traitement"
            file_results.append(result)
            valid_files.append({"filename": file.filename, "content": content})

        if not valid_files:
            db.delete(new_chat)
            db.commit()
            raise HTTPException(
                status_code=400,
                detail={
                    "message": "Aucun PDF valide n'a pu etre indexe",
                    "error_code": "UPLOAD_VALIDATION_FAILED",
                    "files": file_results,
                },
            )

        upload_job_store.create_job(chat_id=chat_id, title=chat_title, files=file_results)
        background_tasks.add_task(_process_upload_background, chat_id, valid_files)
            
        return JSONResponse(status_code=202, content={
            "status": "processing",
            "chat_id": chat_id,
            "title": chat_title,
            "message": "Upload recu. Indexation en arriere-plan demarree.",
            "files": file_results,
            "status_url": f"/api/uploads/{chat_id}/status",
        })
    except Exception as e:
        logger.exception("Upload failed")
        db.delete(new_chat)
        db.commit()
        if isinstance(e, HTTPException):
            raise
        raise _safe_server_error("UPLOAD_INTERNAL_ERROR")


@router.get("/uploads/{chat_id}/status")
async def get_upload_status(chat_id: str):
    job = upload_job_store.get_job(chat_id)
    if not job:
        raise HTTPException(
            status_code=404,
            detail={
                "message": "Statut d'upload introuvable",
                "error_code": "UPLOAD_STATUS_NOT_FOUND",
            },
        )
    return job

@router.get("/chats")
async def list_chats(db: Session = Depends(get_session)):
    """Liste tous les chats par ordre chronologique décroissant."""
    statement = select(Chat).order_by(Chat.created_at.desc())
    results = db.exec(statement).all()
    return results

@router.get("/chats/{chat_id}/messages")
async def get_chat_messages(chat_id: str, db: Session = Depends(get_session)):
    """Récupère l'historique des messages d'un chat."""
    statement = select(Message).where(Message.chat_id == chat_id).order_by(Message.created_at.asc())
    results = db.exec(statement).all()
    return results

@router.delete("/chats/{chat_id}")
async def delete_chat(chat_id: str, db: Session = Depends(get_session)):
    """Supprime un chat de SQLite et sa collection de ChromaDB."""
    chat = db.get(Chat, chat_id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat non trouvé")
    
    try:
        # Suppression SQL (cascade_delete gère les messages)
        db.delete(chat)
        db.commit()
        
        # Suppression Chroma
        get_vector_manager().delete_collection_data(chat_id)
        
        return {"status": "success", "message": f"Chat {chat_id} supprimé avec succès."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la suppression: {str(e)}")


import logging
logger = logging.getLogger("uvicorn.error")


def _build_graph_inputs(req: QueryRequest) -> Dict:
    return {
        "question": req.question,
        "chat_id": req.chat_id,
        "needs_rag": True,
        "is_valid": False,
        "loop_count": 0,
        "agent_steps": [],
        "total_tokens": 0,
        "documents": [],
        "generation": "",
    }


def _ensure_chat_exists(db: Session, chat_id: str):
    chat = db.get(Chat, chat_id)
    if not chat:
        chat = Chat(id=chat_id, title="Chat Direct")
        db.add(chat)
        db.commit()
    return chat


def _save_user_message(db: Session, chat_id: str, question: str):
    user_msg = Message(chat_id=chat_id, role="user", content=question)
    db.add(user_msg)
    db.commit()


def _save_ai_message(db: Session, chat_id: str, answer: str):
    ai_msg = Message(chat_id=chat_id, role="ai", content=answer)
    db.add(ai_msg)
    db.commit()


def _accumulate_state(state: Dict, delta: Dict):
    for key, value in delta.items():
        if key == "agent_steps":
            state.setdefault("agent_steps", []).extend(value)
        elif key == "total_tokens":
            state["total_tokens"] = state.get("total_tokens", 0) + value
        else:
            state[key] = value


def _to_sse(payload: Dict) -> str:
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"

@router.post("/query")
async def query_assistant(req: QueryRequest, request: Request, db: Session = Depends(get_session)):
    """Session-aware query."""
    _enforce_rate_limit(request, "query")
    _ensure_chat_exists(db, req.chat_id)
    _save_user_message(db, req.chat_id, req.question)
    inputs = _build_graph_inputs(req)
    config = {"recursion_limit": 15}
    
    try:
        result = app_graph.invoke(inputs, config=config)
        _save_ai_message(db, req.chat_id, result["generation"])

        quota_info = None
        for step in reversed(result.get("agent_steps", [])):
            budget = step.get("budget") if isinstance(step, dict) else None
            if budget:
                quota_info = budget
                break

        return {
            "answer": result["generation"], 
            "metadata": {
                "loop_count": result.get("loop_count", 0),
                "total_tokens": result.get("total_tokens", 0),
                "quota": quota_info,
            },
            "trace": result.get("agent_steps", [])
        }
    except Exception as e:
        logger.exception("Query failed")
        raise _safe_server_error("QUERY_INTERNAL_ERROR")


@router.post("/query/stream")
async def query_assistant_stream(req: QueryRequest, request: Request, db: Session = Depends(get_session)):
    """SSE stream that emits each agent step in real-time, then final answer."""
    _enforce_rate_limit(request, "query")
    _ensure_chat_exists(db, req.chat_id)
    _save_user_message(db, req.chat_id, req.question)

    inputs = _build_graph_inputs(req)
    config = {"recursion_limit": 15}

    async def event_stream() -> AsyncGenerator[str, None]:
        try:
            running_state: Dict = {
                "agent_steps": [],
                "total_tokens": 0,
                "generation": "",
                "loop_count": 0,
            }

            yield _to_sse({"type": "start", "message": "Generation started"})

            for output in app_graph.stream(inputs, config=config):
                for node_name, delta in output.items():
                    _accumulate_state(running_state, delta)

                    step = None
                    if isinstance(delta, dict) and delta.get("agent_steps"):
                        step = delta["agent_steps"][-1]

                    yield _to_sse(
                        {
                            "type": "agent_step",
                            "node": node_name,
                            "step": step,
                            "metadata": {
                                "loop_count": running_state.get("loop_count", 0),
                                "total_tokens": running_state.get("total_tokens", 0),
                            },
                        }
                    )

            answer = running_state.get("generation", "")
            _save_ai_message(db, req.chat_id, answer)

            yield _to_sse(
                {
                    "type": "done",
                    "answer": answer,
                    "trace": running_state.get("agent_steps", []),
                    "metadata": {
                        "loop_count": running_state.get("loop_count", 0),
                        "total_tokens": running_state.get("total_tokens", 0),
                    },
                }
            )
        except Exception as e:
            logger.exception("Streaming query failed")
            yield _to_sse(
                {
                    "type": "error",
                    "message": "Une erreur interne est survenue. Veuillez reessayer.",
                    "error_code": "QUERY_STREAM_INTERNAL_ERROR",
                }
            )

    return StreamingResponse(event_stream(), media_type="text/event-stream")

import json
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.infra.embeddings.sentence_transformer_provider import SentenceTransformerEmbeddingProvider
from app.infra.llm.ollama_provider import OllamaProvider
from app.infra.vectorstore.chroma_store import ChromaVectorStore
from app.models.document import DocumentStatus
from app.models.message import MessageRole
from app.models.user import User
from app.repositories.chat_repository import ChatRepository
from app.repositories.document_repository import DocumentRepository
from app.repositories.message_repository import MessageRepository
from app.repositories.subject_repository import SubjectRepository
from app.schemas.chat import ChatCreate, ChatOut, MessageCreate, MessageOut
from app.services.rag_service import RAGService

router = APIRouter()


def _get_owned_document_or_404(db: Session, document_id: uuid.UUID, user: User):
    document = DocumentRepository(db).get(document_id)
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    subject = SubjectRepository(db).get_owned(document.subject_id, user.id)
    if not subject:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    return document


@router.post("/", response_model=ChatOut, status_code=status.HTTP_201_CREATED)
def create_chat(
    payload: ChatCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    document = _get_owned_document_or_404(db, payload.document_id, current_user)
    if document.status != DocumentStatus.READY:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Document is not ready yet (status: {document.status.value}). Wait for processing to finish.",
        )
    return ChatRepository(db).create(owner_id=current_user.id, document_id=payload.document_id, title=payload.title)


@router.get("/", response_model=list[ChatOut])
def list_chats(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return ChatRepository(db).list_for_user(current_user.id)


@router.get("/{chat_id}/messages", response_model=list[MessageOut])
def get_messages(
    chat_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    chat = ChatRepository(db).get_owned(uuid.UUID(chat_id), current_user.id)
    if not chat:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat not found")
    return MessageRepository(db).list_for_chat(chat.id)


@router.post("/{chat_id}/messages")
async def send_message(
    chat_id: str,
    payload: MessageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Streams the AI's answer back as Server-Sent Events (SSE):
      - one `citations` event, sent immediately (retrieval happens before generation)
      - repeated `token` events, one per generated token
      - one final `done` event

    Frontend consumes this with a standard `fetch` + `ReadableStream` reader
    (SSE via `EventSource` doesn't support POST bodies, so plain fetch-based
    SSE parsing is what Module 3's chat UI will use).
    """
    chat = ChatRepository(db).get_owned(uuid.UUID(chat_id), current_user.id)
    if not chat:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat not found")

    # Captured now, while `db` is still open -- `chat` itself must not be touched
    # inside event_generator() below, since by the time it runs (after the
    # response starts streaming) the request-scoped session will be closed and
    # any lazy attribute access on `chat` would raise DetachedInstanceError.
    chat_id_value = chat.id
    document_id_value = chat.document_id

    message_repo = MessageRepository(db)
    message_repo.create(chat_id=chat_id_value, role=MessageRole.USER, content=payload.content)

    rag_service = RAGService(
        embedding_provider=SentenceTransformerEmbeddingProvider(),
        vector_store=ChromaVectorStore(),
        llm_provider=OllamaProvider(),
    )

    async def event_generator():
        token_stream, citations = await rag_service.answer_stream(payload.content, document_id_value)

        yield f"data: {json.dumps({'type': 'citations', 'citations': citations})}\n\n"

        full_answer = ""
        async for token in token_stream:
            full_answer += token
            yield f"data: {json.dumps({'type': 'token', 'content': token})}\n\n"

        # Save the complete assistant message only after streaming finishes,
        # using a fresh session since the request-scoped `db` may be stale by now.
        from app.db.session import SessionLocal

        save_db = SessionLocal()
        try:
            MessageRepository(save_db).create(
                chat_id=chat_id_value,
                role=MessageRole.ASSISTANT,
                content=full_answer,
                citations=citations,
            )
        finally:
            save_db.close()

        yield f"data: {json.dumps({'type': 'done'})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")

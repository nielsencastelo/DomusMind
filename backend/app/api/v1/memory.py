import uuid

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.schemas import DocumentIn, DocumentOut, MemoryOut, OkResponse
from app.repositories.memory_repo import MemoryRepository
from app.services.rag_service import RAGService

router = APIRouter(prefix="/memory", tags=["memory"])

_rag = RAGService()


@router.get("/memories", response_model=list[MemoryOut])
async def list_memories(limit: int = 50, db: AsyncSession = Depends(get_db)):
    repo = MemoryRepository(db)
    return await repo.get_all(limit)


@router.delete("/memories/{memory_id}", response_model=OkResponse)
async def delete_memory(memory_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    repo = MemoryRepository(db)
    ok = await repo.delete(memory_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Memória não encontrada.")
    return OkResponse(ok=True, message="Memória removida.")


@router.post("/search")
async def search_memories(query: str, limit: int = 5, db: AsyncSession = Depends(get_db)):
    """Semantic search across memories and documents."""
    embedding = await _rag.embed(query)
    if not embedding:
        raise HTTPException(status_code=503, detail="Embedding service unavailable.")
    repo = MemoryRepository(db)
    chunks = await repo.combined_search(embedding, limit=limit)
    return {"query": query, "results": chunks}


@router.get("/documents", response_model=list[DocumentOut])
async def list_documents(db: AsyncSession = Depends(get_db)):
    repo = MemoryRepository(db)
    return await repo.get_all_documents()


@router.post("/documents", response_model=DocumentOut, status_code=201)
async def upload_document(payload: DocumentIn, db: AsyncSession = Depends(get_db)):
    """Index a text document for RAG retrieval."""
    embedding = await _rag.embed(payload.content)
    repo = MemoryRepository(db)
    doc = await repo.save_document(
        filename=payload.filename,
        content=payload.content,
        embedding=embedding,
    )
    return doc


@router.post("/documents/upload", response_model=DocumentOut, status_code=201)
async def upload_file(file: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    """Upload a text file and index it for RAG."""
    raw = await file.read()
    try:
        content = raw.decode("utf-8")
    except UnicodeDecodeError:
        content = raw.decode("latin-1")

    embedding = await _rag.embed(content)
    repo = MemoryRepository(db)
    doc = await repo.save_document(
        filename=file.filename or "uploaded_file",
        content=content,
        embedding=embedding,
    )
    return doc

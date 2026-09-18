import hashlib
import logging
from pathlib import Path

from sqlalchemy.orm import Session

from core.models import CareerChunk, CareerDocument
from rag.chunking import chunk_text
from rag.embeddings import embed_texts
from rag.vectorstore import get_collection

logger = logging.getLogger(__name__)

CORPUS_DIR = Path("rag/corpus")

SOURCE_TYPE_MAP = {
    "career": "경력기술서",
    "project": "프로젝트설명",
    "letter": "기존자소서",
}


def _guess_source_type(filename: str) -> str:
    prefix = filename.split("_", 1)[0].lower()
    return SOURCE_TYPE_MAP.get(prefix, "기타")


def _hash_content(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def ingest_file(session: Session, path: Path) -> bool:
    """파일 하나를 ingest. 변경 없으면 스킵하고 False, 새로 처리했으면 True를 반환."""
    content = path.read_text(encoding="utf-8").strip()
    if not content:
        logger.warning("빈 파일 스킵: %s", path)
        return False

    content_hash = _hash_content(content)
    existing = session.query(CareerDocument).filter_by(file_path=str(path)).one_or_none()

    if existing and existing.content_hash == content_hash:
        return False

    # 임베딩(외부 API 호출)을 먼저 계산해서, 실패하면 DB/벡터스토어 어느 쪽도 건드리지 않는다.
    chunks = chunk_text(content)
    embeddings = embed_texts(chunks) if chunks else []

    collection = get_collection()

    if existing:
        old_chunk_ids = [c.chroma_embedding_id for c in existing.chunks]
        if old_chunk_ids:
            collection.delete(ids=old_chunk_ids)
        for chunk_row in list(existing.chunks):
            session.delete(chunk_row)
        document = existing
        document.content = content
        document.content_hash = content_hash
        document.title = path.stem
        document.source_type = _guess_source_type(path.name)
    else:
        document = CareerDocument(
            source_type=_guess_source_type(path.name),
            title=path.stem,
            content=content,
            file_path=str(path),
            content_hash=content_hash,
        )
        session.add(document)

    session.flush()

    if chunks:
        chroma_ids = [f"doc{document.id}-chunk{i}" for i in range(len(chunks))]
        collection.add(
            ids=chroma_ids,
            embeddings=embeddings,
            documents=chunks,
            metadatas=[
                {"document_id": document.id, "title": document.title, "source_type": document.source_type}
                for _ in chunks
            ],
        )
        for i, (chunk_value, chroma_id) in enumerate(zip(chunks, chroma_ids)):
            session.add(
                CareerChunk(
                    career_document_id=document.id,
                    chunk_text=chunk_value,
                    chroma_embedding_id=chroma_id,
                    chunk_index=i,
                )
            )

    logger.info("ingest 완료: %s (%d개 청크)", path.name, len(chunks))
    return True

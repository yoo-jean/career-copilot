from unittest.mock import patch

import chromadb

from core.db import session_scope
from core.models import CareerDocument
from rag.ingest import ingest_file, prune_orphaned_documents


def _fake_embed_texts(texts: list[str]) -> list[list[float]]:
    return [[float(len(t) % 7), 0.1, 0.2] for t in texts]


def _cleanup(file_path: str) -> None:
    with session_scope() as session:
        doc = session.query(CareerDocument).filter_by(file_path=file_path).one_or_none()
        if doc:
            for chunk in list(doc.chunks):
                session.delete(chunk)
            session.delete(doc)


def test_ingest_file_creates_document_and_chunks(tmp_path):
    corpus_file = tmp_path / "career_test.md"
    corpus_file.write_text("첫 번째 문단입니다.\n\n두 번째 문단입니다.", encoding="utf-8")
    file_path = str(corpus_file)
    fake_collection = chromadb.Client().create_collection("test_ingest_create")

    _cleanup(file_path)
    try:
        with patch("rag.ingest.embed_texts", side_effect=_fake_embed_texts), patch(
            "rag.ingest.get_collection", return_value=fake_collection
        ):
            with session_scope() as session:
                created = ingest_file(session, corpus_file)
            assert created is True

        with session_scope() as session:
            doc = session.query(CareerDocument).filter_by(file_path=file_path).one()
            assert doc.content_hash is not None
            assert len(doc.chunks) == 1

        assert fake_collection.count() == 1
    finally:
        _cleanup(file_path)


def test_ingest_file_skips_unchanged_content(tmp_path):
    corpus_file = tmp_path / "career_test2.md"
    corpus_file.write_text("동일한 내용입니다.", encoding="utf-8")
    file_path = str(corpus_file)
    fake_collection = chromadb.Client().create_collection("test_ingest_skip")

    _cleanup(file_path)
    try:
        with patch("rag.ingest.embed_texts", side_effect=_fake_embed_texts), patch(
            "rag.ingest.get_collection", return_value=fake_collection
        ):
            with session_scope() as session:
                first = ingest_file(session, corpus_file)
            with session_scope() as session:
                second = ingest_file(session, corpus_file)

        assert first is True
        assert second is False
    finally:
        _cleanup(file_path)


def test_ingest_file_reingests_on_content_change(tmp_path):
    corpus_file = tmp_path / "career_test3.md"
    corpus_file.write_text("원래 내용.", encoding="utf-8")
    file_path = str(corpus_file)
    fake_collection = chromadb.Client().create_collection("test_ingest_change")

    _cleanup(file_path)
    try:
        with patch("rag.ingest.embed_texts", side_effect=_fake_embed_texts), patch(
            "rag.ingest.get_collection", return_value=fake_collection
        ):
            with session_scope() as session:
                ingest_file(session, corpus_file)

            corpus_file.write_text("변경된 내용입니다.", encoding="utf-8")
            with session_scope() as session:
                changed = ingest_file(session, corpus_file)

        assert changed is True
        with session_scope() as session:
            doc = session.query(CareerDocument).filter_by(file_path=file_path).one()
            assert "변경된" in doc.content
            assert len(doc.chunks) == 1
    finally:
        _cleanup(file_path)


def test_prune_orphaned_documents_removes_deleted_file_entries(tmp_path):
    """코퍼스 파일을 삭제해도 DB/Chroma에 예전 내용이 고아로 남아있던
    실제 버그의 회귀 테스트 (더미 fixture 정리 중 발견됨)."""
    corpus_file = tmp_path / "career_orphan_test.md"
    corpus_file.write_text("곧 삭제될 내용입니다.", encoding="utf-8")
    file_path = str(corpus_file)
    fake_collection = chromadb.Client().create_collection("test_ingest_prune")

    _cleanup(file_path)
    try:
        with patch("rag.ingest.embed_texts", side_effect=_fake_embed_texts), patch(
            "rag.ingest.get_collection", return_value=fake_collection
        ):
            with session_scope() as session:
                ingest_file(session, corpus_file)

            assert fake_collection.count() == 1

            corpus_file.unlink()  # 파일 삭제 -> 이제 고아 문서가 됨

            with session_scope() as session:
                removed = prune_orphaned_documents(session)

        # prune_orphaned_documents는 테이블 전체를 훑으므로, 공유 dev DB에 다른
        # 고아 문서가 있어도 통과해야 한다 — 이 테스트 문서가 지워졌는지만 확인.
        assert removed >= 1
        with session_scope() as session:
            assert session.query(CareerDocument).filter_by(file_path=file_path).one_or_none() is None
    finally:
        _cleanup(file_path)


def test_prune_orphaned_documents_keeps_existing_files(tmp_path):
    corpus_file = tmp_path / "career_keep_test.md"
    corpus_file.write_text("계속 존재하는 내용입니다.", encoding="utf-8")
    file_path = str(corpus_file)
    fake_collection = chromadb.Client().create_collection("test_ingest_keep")

    _cleanup(file_path)
    try:
        with patch("rag.ingest.embed_texts", side_effect=_fake_embed_texts), patch(
            "rag.ingest.get_collection", return_value=fake_collection
        ):
            with session_scope() as session:
                ingest_file(session, corpus_file)

            with session_scope() as session:
                removed = prune_orphaned_documents(session)

        assert removed == 0
        with session_scope() as session:
            assert session.query(CareerDocument).filter_by(file_path=file_path).one_or_none() is not None
    finally:
        _cleanup(file_path)

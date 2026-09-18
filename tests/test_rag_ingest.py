from unittest.mock import patch

import chromadb

from core.db import session_scope
from core.models import CareerDocument
from rag.ingest import ingest_file


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

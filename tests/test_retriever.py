from unittest.mock import patch

import chromadb

from rag.retriever import retrieve_relevant_chunks


def test_retrieve_relevant_chunks_returns_top_match():
    collection = chromadb.Client().create_collection("test_retriever_basic")
    collection.add(
        ids=["c1", "c2"],
        embeddings=[[1.0, 0.0], [0.0, 1.0]],
        documents=["파이썬 백엔드 경험", "그래픽 디자인 경험"],
        metadatas=[
            {"title": "doc1", "source_type": "경력기술서"},
            {"title": "doc2", "source_type": "프로젝트설명"},
        ],
    )

    with (
        patch("rag.retriever.get_collection", return_value=collection),
        patch("rag.retriever.embed_texts", return_value=[[1.0, 0.0]]),
    ):
        results = retrieve_relevant_chunks("백엔드 개발자 채용", top_k=1)

    assert len(results) == 1
    assert results[0].text == "파이썬 백엔드 경험"
    assert results[0].title == "doc1"
    assert results[0].source_type == "경력기술서"


def test_retrieve_relevant_chunks_empty_collection_returns_empty_list():
    collection = chromadb.Client().create_collection("test_retriever_empty")

    with patch("rag.retriever.get_collection", return_value=collection):
        results = retrieve_relevant_chunks("아무 질문")

    assert results == []

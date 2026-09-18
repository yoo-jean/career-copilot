from dataclasses import dataclass

from rag.embeddings import embed_texts
from rag.vectorstore import get_collection


@dataclass
class RetrievedChunk:
    text: str
    title: str
    source_type: str
    distance: float


def retrieve_relevant_chunks(query: str, top_k: int = 5) -> list[RetrievedChunk]:
    collection = get_collection()
    count = collection.count()
    if count == 0:
        return []

    query_embedding = embed_texts([query])[0]
    result = collection.query(query_embeddings=[query_embedding], n_results=min(top_k, count))

    documents = result["documents"][0]
    metadatas = result["metadatas"][0]
    distances = result["distances"][0]

    return [
        RetrievedChunk(
            text=doc,
            title=meta.get("title", ""),
            source_type=meta.get("source_type", ""),
            distance=dist,
        )
        for doc, meta, dist in zip(documents, metadatas, distances)
    ]

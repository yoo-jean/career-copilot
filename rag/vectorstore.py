import chromadb
from chromadb.api.models.Collection import Collection

from config.settings import get_settings

COLLECTION_NAME = "career_chunks"

_collection: Collection | None = None


def get_collection() -> Collection:
    global _collection
    if _collection is None:
        settings = get_settings()
        client = chromadb.PersistentClient(path=str(settings.chroma_persist_dir))
        _collection = client.get_or_create_collection(COLLECTION_NAME)
    return _collection

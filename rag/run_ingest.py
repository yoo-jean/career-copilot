import logging

from core.db import init_db, session_scope
from rag.ingest import CORPUS_DIR, ingest_file, prune_orphaned_documents

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def main() -> None:
    init_db()

    paths = sorted([*CORPUS_DIR.glob("*.md"), *CORPUS_DIR.glob("*.txt")]) if CORPUS_DIR.exists() else []
    if not paths:
        logger.warning("%s에 ingest할 파일이 없습니다.", CORPUS_DIR)

    updated = 0
    skipped = 0
    errors = 0
    for path in paths:
        try:
            with session_scope() as session:
                if ingest_file(session, path):
                    updated += 1
                else:
                    skipped += 1
        except Exception:
            errors += 1
            logger.exception("ingest 실패: %s", path)

    try:
        with session_scope() as session:
            pruned = prune_orphaned_documents(session)
    except Exception:
        pruned = 0
        logger.exception("고아 문서 정리 실패")

    logger.info(
        "총 %d개 파일 — 갱신 %d, 변경없음(스킵) %d, 실패 %d, 정리(삭제) %d",
        len(paths),
        updated,
        skipped,
        errors,
        pruned,
    )


if __name__ == "__main__":
    main()

import logging

from core.db import init_db, session_scope
from rag.ingest import CORPUS_DIR, ingest_file

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def main() -> None:
    init_db()

    if not CORPUS_DIR.exists():
        logger.error("%s 디렉토리가 없습니다. 경력 문서를 .md/.txt 파일로 넣어주세요.", CORPUS_DIR)
        return

    paths = sorted([*CORPUS_DIR.glob("*.md"), *CORPUS_DIR.glob("*.txt")])
    if not paths:
        logger.warning("%s에 ingest할 파일이 없습니다.", CORPUS_DIR)
        return

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

    logger.info("총 %d개 파일 — 갱신 %d, 변경없음(스킵) %d, 실패 %d", len(paths), updated, skipped, errors)


if __name__ == "__main__":
    main()

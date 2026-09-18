import json
import logging
import sys

from config.settings import get_settings
from core.db import init_db, session_scope
from crawler.service import save_job_posting
from crawler.sites.saramin import SaraminAdapter
from crawler.sites.wanted import WantedAdapter

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

ADAPTERS = [SaraminAdapter, WantedAdapter]


def load_watchlist() -> list[str]:
    settings = get_settings()
    path = settings.data_dir / "watchlist.json"
    if not path.exists():
        logger.error(
            "%s가 없습니다. fixtures/watchlist.example.json을 참고해 만들어주세요 (관심 직무 키워드 목록).",
            path,
        )
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    return data.get("keywords", [])


def main() -> None:
    init_db()
    keywords = load_watchlist()
    if not keywords:
        sys.exit(1)

    created_count = 0
    skipped_count = 0
    error_count = 0

    for adapter_cls in ADAPTERS:
        adapter = adapter_cls()
        for keyword in keywords:
            logger.info("[%s] 검색 중: %s", adapter.name, keyword)
            try:
                postings = adapter.search(keyword, max_results=10)
            except Exception:
                error_count += 1
                logger.exception("[%s] 검색 실패: %s", adapter.name, keyword)
                continue

            for posting in postings:
                try:
                    with session_scope() as session:
                        _, created = save_job_posting(session, posting)
                    if created:
                        created_count += 1
                        logger.info("저장: [%s] %s", posting.company_name, posting.title)
                    else:
                        skipped_count += 1
                except Exception:
                    error_count += 1
                    logger.exception("저장 실패: %s", posting.url)

    logger.info("완료 — 신규 %d건, 중복 스킵 %d건, 실패 %d건", created_count, skipped_count, error_count)


if __name__ == "__main__":
    main()

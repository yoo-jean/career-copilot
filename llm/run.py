import logging

from core.db import init_db, session_scope
from core.models import JobPosting, JobPostingStatus
from llm.service import summarize_and_save

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def main() -> None:
    init_db()

    with session_scope() as session:
        posting_ids = [
            pid for (pid,) in session.query(JobPosting.id).filter(JobPosting.status == JobPostingStatus.NEW).all()
        ]

    logger.info("요약 대상: %d건", len(posting_ids))

    success_count = 0
    error_count = 0
    for posting_id in posting_ids:
        try:
            with session_scope() as session:
                posting = session.get(JobPosting, posting_id)
                summary = summarize_and_save(session, posting)
                outcome = "메타 정보만 (본문 없음)" if summary.model_used == "meta_only" else "요약 완료"
                logger.info("[%s] %s -> %s", posting.company.name, posting.title[:30], outcome)
            success_count += 1
        except Exception:
            error_count += 1
            logger.exception("요약 실패: posting_id=%s", posting_id)

    logger.info("완료 — 성공 %d건, 실패 %d건", success_count, error_count)


if __name__ == "__main__":
    main()

import argparse
import logging

from core.db import init_db, session_scope
from core.models import JobPosting
from rag.service import create_cover_letter_draft, create_interview_answer_draft

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def main() -> None:
    parser = argparse.ArgumentParser(description="채용공고에 대한 자소서/면접답변 초안 생성")
    parser.add_argument("job_id", type=int)
    parser.add_argument("--question", type=str, default=None, help="지정하면 면접답변 초안, 없으면 자소서 초안 생성")
    args = parser.parse_args()

    init_db()
    with session_scope() as session:
        posting = session.get(JobPosting, args.job_id)
        if posting is None:
            logger.error("job_id=%s 공고를 찾을 수 없습니다.", args.job_id)
            return

        if args.question:
            draft = create_interview_answer_draft(session, posting, args.question)
        else:
            draft = create_cover_letter_draft(session, posting)

        print("\n" + "=" * 60)
        print(draft.content)
        print("=" * 60)


if __name__ == "__main__":
    main()

import pytest

from core.db import init_db


@pytest.fixture(scope="session", autouse=True)
def _init_test_db():
    """모든 테스트가 시작되기 전에 스키마를 보장한다.

    로컬 dev DB(data/career_copilot.db)가 이미 존재하면 우연히 통과하지만,
    CI처럼 data/ 디렉토리가 아예 없는 환경에서는 테이블이 없어 실패했다.
    """
    init_db()

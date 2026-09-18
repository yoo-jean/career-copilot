from config.settings import get_settings
from core.db import init_db, session_scope
from core.models import Company


def test_settings_resolve_database_url():
    settings = get_settings()
    assert settings.resolved_database_url.startswith("sqlite:///")
    assert settings.resolved_database_url.endswith("career_copilot.db")


def test_db_roundtrip():
    init_db()

    with session_scope() as session:
        session.query(Company).filter_by(name="__test_company__").delete()

    with session_scope() as session:
        session.add(Company(name="__test_company__", careers_url="https://example.com"))

    with session_scope() as session:
        company = session.query(Company).filter_by(name="__test_company__").one()
        assert company.careers_url == "https://example.com"
        session.delete(company)

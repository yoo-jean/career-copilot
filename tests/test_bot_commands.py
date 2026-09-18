from datetime import datetime

import discord

from bot.commands.jobs import _fetch_recent_jobs_embed, build_jobs_embed
from bot.commands.summarize import _fetch_or_build_summary_embed, build_summary_embed
from core.db import session_scope
from core.models import Company, JobPosting, JobPostingStatus, JobSummary


def test_build_jobs_embed_empty():
    embed = build_jobs_embed([])
    assert "없습니다" in embed.description


def test_build_jobs_embed_with_posting():
    posting = JobPosting(
        id=1,
        title="백엔드 개발자",
        url="https://example.com/1",
        raw_text="",
        status=JobPostingStatus.NEW,
        deadline_at=datetime(2026, 10, 14),
    )
    posting.company = Company(name="테스트회사")

    embed = build_jobs_embed([posting])
    assert "#1" in embed.description
    assert "테스트회사" in embed.description
    assert "10/14" in embed.description
    assert "신규" in embed.description


def test_build_summary_embed():
    posting = JobPosting(id=1, title="백엔드 개발자", url="https://example.com/1", raw_text="", status=JobPostingStatus.SUMMARIZED)
    posting.company = Company(name="테스트회사")
    summary = JobSummary(
        requirements_json=["Python 3년"],
        preferred_json=[],
        tech_stack_json=["Python", "FastAPI"],
        salary_info=None,
        summary_text="백엔드 개발자 채용 공고입니다.",
        model_used="claude-sonnet-5",
    )

    embed = build_summary_embed(posting, summary)
    assert "테스트회사" in embed.title
    assert embed.description == "백엔드 개발자 채용 공고입니다."
    assert any(f.name == "자격요건" and "Python 3년" in f.value for f in embed.fields)
    assert any(f.name == "우대사항" and "정보 없음" in f.value for f in embed.fields)


def test_fetch_recent_jobs_embed_smoke():
    embed = _fetch_recent_jobs_embed(3)
    assert isinstance(embed, discord.Embed)


def test_fetch_or_build_summary_embed_missing_job():
    result = _fetch_or_build_summary_embed(-1)
    assert isinstance(result, str)
    assert "찾을 수 없습니다" in result


def _cleanup_test_row():
    with session_scope() as session:
        session.query(JobSummary).filter(
            JobSummary.job_posting_id.in_(
                session.query(JobPosting.id).filter_by(url="https://example.com/__test_bot__")
            )
        ).delete(synchronize_session=False)
        session.query(JobPosting).filter_by(url="https://example.com/__test_bot__").delete()
        session.query(Company).filter_by(name="__test_bot_company__").delete()


def test_fetch_or_build_summary_embed_existing_summary():
    _cleanup_test_row()

    with session_scope() as session:
        company = Company(name="__test_bot_company__")
        session.add(company)
        session.flush()
        posting = JobPosting(
            company_id=company.id,
            title="테스트 공고",
            url="https://example.com/__test_bot__",
            raw_text="테스트용 원문",
            status=JobPostingStatus.NEW,
        )
        session.add(posting)
        session.flush()
        session.add(
            JobSummary(
                job_posting_id=posting.id,
                requirements_json=["요건1"],
                preferred_json=[],
                tech_stack_json=["Python"],
                salary_info=None,
                summary_text="테스트 요약",
                model_used="meta_only",
            )
        )
        posting_id = posting.id

    try:
        result = _fetch_or_build_summary_embed(posting_id)
        assert not isinstance(result, str)
        assert "__test_bot_company__" in result.title
    finally:
        _cleanup_test_row()

from unittest.mock import patch

from bot.commands.draft import (
    _generate_cover_letter_embed,
    _generate_interview_answer_embed,
    build_draft_embed,
)
from core.db import session_scope
from core.models import Company, Draft, DraftType, JobPosting, JobPostingStatus

TEST_URL = "https://example.com/__test_draft__"


def test_build_draft_embed_cover_letter():
    posting = JobPosting(id=1, title="백엔드 개발자", url="https://example.com/1", raw_text="", status=JobPostingStatus.SUMMARIZED)
    posting.company = Company(name="테스트회사")
    draft = Draft(draft_type=DraftType.COVER_LETTER, content="자소서 내용입니다.")

    embed = build_draft_embed(posting, draft)
    assert "자소서 초안" in embed.title
    assert embed.description == "자소서 내용입니다."
    assert embed.fields == []


def test_build_draft_embed_interview_answer_shows_question():
    posting = JobPosting(id=1, title="백엔드 개발자", url="https://example.com/1", raw_text="", status=JobPostingStatus.SUMMARIZED)
    posting.company = Company(name="테스트회사")
    draft = Draft(draft_type=DraftType.INTERVIEW_ANSWER, question="가장 어려웠던 경험은?", content="답변 내용입니다.")

    embed = build_draft_embed(posting, draft)
    assert "면접 답변 초안" in embed.title
    assert any(f.name == "질문" and "가장 어려웠던" in f.value for f in embed.fields)


def _cleanup() -> None:
    with session_scope() as session:
        posting = session.query(JobPosting).filter_by(url=TEST_URL).one_or_none()
        if posting:
            session.query(Draft).filter_by(job_posting_id=posting.id).delete()
            session.delete(posting)
        session.query(Company).filter_by(name="__test_draft_company__").delete()


def _create_test_posting() -> int:
    with session_scope() as session:
        company = Company(name="__test_draft_company__")
        session.add(company)
        session.flush()
        posting = JobPosting(
            company_id=company.id,
            title="테스트 공고",
            url=TEST_URL,
            raw_text="테스트 원문",
            status=JobPostingStatus.NEW,
        )
        session.add(posting)
        session.flush()
        return posting.id


def test_generate_cover_letter_embed_missing_job():
    result = _generate_cover_letter_embed(-1)
    assert isinstance(result, str)
    assert "찾을 수 없습니다" in result


def test_generate_interview_answer_embed_missing_job():
    result = _generate_interview_answer_embed(-1, "질문입니다")
    assert isinstance(result, str)
    assert "찾을 수 없습니다" in result


def test_generate_cover_letter_embed_with_existing_job():
    _cleanup()
    try:
        posting_id = _create_test_posting()
        fake_draft = Draft(id=1, draft_type=DraftType.COVER_LETTER, content="가짜 자소서 내용")

        with patch("bot.commands.draft.create_cover_letter_draft", return_value=fake_draft) as mock_create:
            result = _generate_cover_letter_embed(posting_id)

        mock_create.assert_called_once()
        assert not isinstance(result, str)
        assert "__test_draft_company__" in result.title
        assert result.description == "가짜 자소서 내용"
    finally:
        _cleanup()


def test_generate_interview_answer_embed_with_existing_job():
    _cleanup()
    try:
        posting_id = _create_test_posting()
        fake_draft = Draft(
            id=2, draft_type=DraftType.INTERVIEW_ANSWER, question="가장 어려웠던 경험은?", content="가짜 답변 내용"
        )

        with patch("bot.commands.draft.create_interview_answer_draft", return_value=fake_draft) as mock_create:
            result = _generate_interview_answer_embed(posting_id, "가장 어려웠던 경험은?")

        mock_create.assert_called_once_with(mock_create.call_args.args[0], mock_create.call_args.args[1], "가장 어려웠던 경험은?")
        assert not isinstance(result, str)
        assert any(f.name == "질문" for f in result.fields)
    finally:
        _cleanup()

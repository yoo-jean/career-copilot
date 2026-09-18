from types import SimpleNamespace
from unittest.mock import patch

from rag.generator import generate_cover_letter_draft, generate_interview_answer_draft
from rag.retriever import RetrievedChunk


def _fake_text_message(text: str, stop_reason: str = "end_turn") -> SimpleNamespace:
    block = SimpleNamespace(type="text", text=text)
    return SimpleNamespace(content=[block], stop_reason=stop_reason)


@patch("rag.generator.get_client")
@patch("rag.generator.get_settings")
def test_generate_cover_letter_draft_returns_text(mock_get_settings, mock_get_client):
    mock_get_settings.return_value = SimpleNamespace(anthropic_model="claude-sonnet-5")
    fake_client = mock_get_client.return_value
    fake_client.messages.create.return_value = _fake_text_message("자기소개서 초안 내용입니다.")

    chunks = [RetrievedChunk(text="백엔드 3년 경험", title="경력기술서", source_type="경력기술서", distance=0.1)]
    result = generate_cover_letter_draft(
        job_title="백엔드 개발자",
        company_name="테스트회사",
        job_summary_text="백엔드 채용",
        career_chunks=chunks,
    )

    assert result == "자기소개서 초안 내용입니다."
    fake_client.messages.create.assert_called_once()
    assert fake_client.messages.create.call_args.kwargs["thinking"] == {"type": "disabled"}


@patch("rag.generator.get_client")
@patch("rag.generator.get_settings")
def test_generate_interview_answer_draft_returns_text(mock_get_settings, mock_get_client):
    mock_get_settings.return_value = SimpleNamespace(anthropic_model="claude-sonnet-5")
    fake_client = mock_get_client.return_value
    fake_client.messages.create.return_value = _fake_text_message("면접 답변 초안입니다.")

    result = generate_interview_answer_draft(
        question="가장 어려웠던 프로젝트는?",
        job_title="백엔드 개발자",
        company_name="테스트회사",
        job_summary_text="백엔드 채용",
        career_chunks=[],
    )

    assert result == "면접 답변 초안입니다."
    call_kwargs = fake_client.messages.create.call_args.kwargs
    assert "참고할 개인 경력 데이터가 없습니다" in call_kwargs["messages"][0]["content"]
    assert call_kwargs["thinking"] == {"type": "disabled"}


@patch("rag.generator.get_client")
@patch("rag.generator.get_settings")
def test_truncated_generation_logs_warning(mock_get_settings, mock_get_client, caplog):
    """실제로 겪은 버그의 회귀 테스트: thinking이 기본 활성화된 상태로 두면
    max_tokens 예산을 사고 과정이 먼저 소진해 본문이 중간에 잘렸다.
    thinking을 명시적으로 꺼뒀는지와 별개로, 혹시 잘리는 경우 경고 로그를 남기는지 확인한다."""
    mock_get_settings.return_value = SimpleNamespace(anthropic_model="claude-sonnet-5")
    fake_client = mock_get_client.return_value
    fake_client.messages.create.return_value = _fake_text_message("끊긴 문장인데", stop_reason="max_tokens")

    with caplog.at_level("WARNING"):
        result = generate_cover_letter_draft(
            job_title="백엔드 개발자",
            company_name="테스트회사",
            job_summary_text="백엔드 채용",
            career_chunks=[],
        )

    assert result == "끊긴 문장인데"
    assert any("잘렸습니다" in record.message for record in caplog.records)

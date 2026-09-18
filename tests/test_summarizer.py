from types import SimpleNamespace
from unittest.mock import patch

from llm.summarizer import summarize_job_posting


def test_thin_raw_text_skips_llm_call():
    result = summarize_job_posting(title="t", company_name="c", raw_text="짧은 메타 정보만 있음")

    assert result.model_used == "meta_only"
    assert result.requirements_json == []
    assert "이미지" in result.summary_text


def _fake_message(payload: dict, stop_reason: str = "tool_use") -> SimpleNamespace:
    tool_block = SimpleNamespace(type="tool_use", input=payload)
    return SimpleNamespace(content=[tool_block], stop_reason=stop_reason)


@patch("llm.summarizer.get_client")
@patch("llm.summarizer.get_settings")
def test_llm_call_parses_tool_use_response(mock_get_settings, mock_get_client):
    mock_get_settings.return_value = SimpleNamespace(anthropic_model="claude-sonnet-5")
    fake_client = mock_get_client.return_value
    fake_client.messages.create.return_value = _fake_message(
        {
            "requirements": ["Python 3년 이상"],
            "preferred": ["AWS 경험"],
            "tech_stack": ["Python", "FastAPI"],
            "salary_info": None,
            "summary_text": "백엔드 개발자 채용 공고입니다.",
        }
    )

    raw_text = "회사: 테스트\n공고명: 백엔드 개발자\n" + ("상세 설명 " * 50)
    result = summarize_job_posting(title="백엔드 개발자", company_name="테스트", raw_text=raw_text)

    assert result.requirements_json == ["Python 3년 이상"]
    assert result.preferred_json == ["AWS 경험"]
    assert result.tech_stack_json == ["Python", "FastAPI"]
    assert result.salary_info is None
    assert result.model_used == "claude-sonnet-5"
    fake_client.messages.create.assert_called_once()


@patch("llm.summarizer.get_client")
@patch("llm.summarizer.get_settings")
def test_truncated_response_does_not_raise(mock_get_settings, mock_get_client):
    """summary_text가 스키마상 먼저 채워지므로, max_tokens에 걸려 목록 필드가
    잘려도 KeyError 없이 결과를 반환해야 한다 (회귀 테스트: 필드 순서를 뒤집으면
    summary_text가 누락돼 KeyError가 났던 실제 버그)."""
    mock_get_settings.return_value = SimpleNamespace(anthropic_model="claude-sonnet-5")
    fake_client = mock_get_client.return_value
    fake_client.messages.create.return_value = _fake_message(
        {
            "summary_text": "백엔드 개발자 채용 공고입니다.",
            "requirements": ["Java", "Spring"],
        },
        stop_reason="max_tokens",
    )

    raw_text = "회사: 테스트\n공고명: 백엔드 개발자\n" + ("상세 설명 " * 50)
    result = summarize_job_posting(title="백엔드 개발자", company_name="테스트", raw_text=raw_text)

    assert result.summary_text == "백엔드 개발자 채용 공고입니다."
    assert result.preferred_json == []
    assert result.tech_stack_json == []

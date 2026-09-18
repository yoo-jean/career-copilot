import logging
from pathlib import Path

from config.settings import get_settings
from llm.client import get_client
from rag.retriever import RetrievedChunk

logger = logging.getLogger(__name__)

_PROMPTS_DIR = Path(__file__).parent / "prompts"
COVER_LETTER_PROMPT = (_PROMPTS_DIR / "cover_letter.md").read_text(encoding="utf-8").strip()
INTERVIEW_ANSWER_PROMPT = (_PROMPTS_DIR / "interview_answer.md").read_text(encoding="utf-8").strip()

# 확장 사고(thinking)가 기본 활성화돼 있으면 max_tokens 예산을 사고 과정에 먼저 써버려
# 정작 본문이 잘리는 문제가 있었다 (자소서/면접답변은 깊은 추론이 필요 없는 작업이라 꺼둔다).
THINKING_DISABLED = {"type": "disabled"}


def _format_context(chunks: list[RetrievedChunk]) -> str:
    if not chunks:
        return "(참고할 개인 경력 데이터가 없습니다)"
    return "\n\n".join(f"[{c.source_type} - {c.title}]\n{c.text}" for c in chunks)


def _extract_text(message) -> str:
    if message.stop_reason == "max_tokens":
        logger.warning("생성 응답이 max_tokens에서 잘렸습니다. 내용이 중간에 끊겼을 수 있습니다.")
    return "".join(block.text for block in message.content if block.type == "text").strip()


def generate_cover_letter_draft(
    job_title: str,
    company_name: str,
    job_summary_text: str,
    career_chunks: list[RetrievedChunk],
) -> str:
    settings = get_settings()
    client = get_client()

    user_content = (
        f"지원 회사: {company_name}\n"
        f"공고 제목: {job_title}\n"
        f"공고 요약: {job_summary_text}\n\n"
        f"--- 내 경력 데이터 ---\n{_format_context(career_chunks)}"
    )

    message = client.messages.create(
        model=settings.anthropic_model,
        max_tokens=1500,
        thinking=THINKING_DISABLED,
        system=COVER_LETTER_PROMPT,
        messages=[{"role": "user", "content": user_content}],
    )
    return _extract_text(message)


def generate_interview_answer_draft(
    question: str,
    job_title: str,
    company_name: str,
    job_summary_text: str,
    career_chunks: list[RetrievedChunk],
) -> str:
    settings = get_settings()
    client = get_client()

    user_content = (
        f"지원 회사: {company_name}\n"
        f"공고 제목: {job_title}\n"
        f"공고 요약: {job_summary_text}\n"
        f"면접 질문: {question}\n\n"
        f"--- 내 경력 데이터 ---\n{_format_context(career_chunks)}"
    )

    message = client.messages.create(
        model=settings.anthropic_model,
        max_tokens=1200,
        thinking=THINKING_DISABLED,
        system=INTERVIEW_ANSWER_PROMPT,
        messages=[{"role": "user", "content": user_content}],
    )
    return _extract_text(message)

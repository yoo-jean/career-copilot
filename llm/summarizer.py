import logging
from dataclasses import dataclass
from pathlib import Path

from config.settings import get_settings
from llm.client import get_client

logger = logging.getLogger(__name__)

MIN_RAW_TEXT_LENGTH_FOR_LLM = 300

SYSTEM_PROMPT = (Path(__file__).parent / "prompts" / "summarize_job.md").read_text(encoding="utf-8").strip()

EXTRACT_TOOL = {
    "name": "record_job_summary",
    "description": "채용공고에서 추출한 핵심 요건, 우대사항, 기술스택, 급여 정보를 구조화하여 기록한다.",
    "input_schema": {
        "type": "object",
        "properties": {
            # summary_text를 가장 먼저 채우도록 배치 — 뒤의 목록 필드들이 길어서
            # max_tokens에 걸려 잘리더라도 핵심 요약만은 항상 확보되도록 함.
            "summary_text": {
                "type": "string",
                "description": "채용공고 핵심을 3~4문장으로 요약",
            },
            "requirements": {
                "type": "array",
                "items": {"type": "string"},
                "description": "필수 자격요건 목록 (최대 8개)",
            },
            "preferred": {
                "type": "array",
                "items": {"type": "string"},
                "description": "우대사항 목록 (최대 8개)",
            },
            "tech_stack": {
                "type": "array",
                "items": {"type": "string"},
                "description": "언급된 기술 스택/툴 목록 (최대 8개)",
            },
            "salary_info": {
                "type": ["string", "null"],
                "description": "급여 관련 언급 (없으면 null)",
            },
        },
        "required": ["summary_text", "requirements", "preferred", "tech_stack"],
    },
}


@dataclass
class JobSummaryResult:
    requirements_json: list[str]
    preferred_json: list[str]
    tech_stack_json: list[str]
    salary_info: str | None
    summary_text: str
    model_used: str


def summarize_job_posting(title: str, company_name: str, raw_text: str) -> JobSummaryResult:
    if len(raw_text.strip()) < MIN_RAW_TEXT_LENGTH_FOR_LLM:
        return JobSummaryResult(
            requirements_json=[],
            preferred_json=[],
            tech_stack_json=[],
            salary_info=None,
            summary_text="상세 설명 본문이 없는 공고입니다 (이미지 형태 공고로 추정). 목록 정보만 확인 가능합니다.",
            model_used="meta_only",
        )

    settings = get_settings()
    client = get_client()

    message = client.messages.create(
        model=settings.anthropic_model,
        max_tokens=2048,
        system=SYSTEM_PROMPT,
        tools=[EXTRACT_TOOL],
        tool_choice={"type": "tool", "name": "record_job_summary"},
        messages=[
            {
                "role": "user",
                "content": f"회사: {company_name}\n공고 제목: {title}\n\n원문:\n{raw_text}",
            }
        ],
    )

    if message.stop_reason == "max_tokens":
        logger.warning("응답이 max_tokens에서 잘렸습니다 (title=%r). 목록 필드가 누락됐을 수 있습니다.", title)

    tool_use = next(block for block in message.content if block.type == "tool_use")
    result = tool_use.input

    return JobSummaryResult(
        requirements_json=result.get("requirements", []),
        preferred_json=result.get("preferred", []),
        tech_stack_json=result.get("tech_stack", []),
        salary_info=result.get("salary_info"),
        summary_text=result.get("summary_text", ""),
        model_used=settings.anthropic_model,
    )

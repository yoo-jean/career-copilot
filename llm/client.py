from anthropic import Anthropic

from config.settings import get_settings

_client: Anthropic | None = None


def get_client() -> Anthropic:
    global _client
    if _client is None:
        settings = get_settings()
        if not settings.anthropic_api_key:
            raise RuntimeError("ANTHROPIC_API_KEY가 설정되지 않았습니다 (.env를 확인하세요).")
        _client = Anthropic(api_key=settings.anthropic_api_key)
    return _client

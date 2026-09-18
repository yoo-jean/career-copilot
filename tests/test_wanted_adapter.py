import json
from pathlib import Path

from crawler.sites.wanted import build_raw_text, parse_due_time, parse_search_results

FIXTURES = Path(__file__).parent / "fixtures"


def _load(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def test_parse_search_results():
    search_json = _load("wanted_search_sample.json")
    results = parse_search_results(search_json, max_results=10)

    assert len(results) == 2
    first = results[0]
    assert first["external_id"] == "380594"
    assert first["title"] == "백엔드 개발자"
    assert "아타드" in first["company_name"]
    assert first["url"] == "https://www.wanted.co.kr/wd/380594"


def test_parse_search_results_respects_max_results():
    search_json = _load("wanted_search_sample.json")
    results = parse_search_results(search_json, max_results=1)
    assert len(results) == 1


def test_build_raw_text_includes_structured_sections():
    search_json = _load("wanted_search_sample.json")
    detail_json = _load("wanted_detail_sample.json")
    listing = parse_search_results(search_json, max_results=1)[0]

    raw_text = build_raw_text(listing, detail_json)

    assert "회사: 아타드" in raw_text
    assert "[주요업무]" in raw_text
    assert "[자격요건]" in raw_text
    assert "[우대사항]" in raw_text
    assert "기술태그:" in raw_text
    assert "Kotlin" in raw_text or "Java" in raw_text


def test_build_raw_text_handles_missing_detail_gracefully():
    listing = {"company_name": "테스트회사", "title": "테스트 공고"}
    raw_text = build_raw_text(listing, {"data": {"job": {}}})
    assert "회사: 테스트회사" in raw_text


def test_parse_due_time_returns_none_when_missing():
    detail_json = _load("wanted_detail_sample.json")
    assert parse_due_time(detail_json) is None


def test_parse_due_time_parses_iso_string():
    detail_json = {"data": {"job": {"due_time": "2026-10-31T23:59:59+09:00"}}}
    result = parse_due_time(detail_json)
    assert result is not None
    assert result.year == 2026
    assert result.month == 10
    assert result.day == 31


def test_parse_due_time_handles_malformed_value():
    detail_json = {"data": {"job": {"due_time": "not-a-date"}}}
    assert parse_due_time(detail_json) is None

from pathlib import Path

from crawler.sites.saramin import parse_detail_html, parse_search_results

FIXTURES = Path(__file__).parent / "fixtures"


def test_parse_search_results():
    html = (FIXTURES / "saramin_search_sample.html").read_text(encoding="utf-8")
    results = parse_search_results(html, max_results=10)

    assert len(results) == 2
    first = results[0]
    assert first["external_id"] == "53930400"
    assert "수산" in first["company_name"]
    assert first["url"] == "https://www.saramin.co.kr/zf_user/jobs/relay/view?rec_idx=53930400"
    assert first["company_url"].startswith("https://www.saramin.co.kr/zf_user/company-info/view")
    assert "회사:" in first["meta_text"]
    assert "공고명:" in first["meta_text"]


def test_parse_search_results_respects_max_results():
    html = (FIXTURES / "saramin_search_sample.html").read_text(encoding="utf-8")
    results = parse_search_results(html, max_results=1)
    assert len(results) == 1


def test_parse_detail_html_extracts_description():
    html = (FIXTURES / "saramin_detail_sample.html").read_text(encoding="utf-8")
    text = parse_detail_html(html)

    assert "모집부문" in text
    assert "자격요건" in text
    assert len(text) > 100


def test_parse_detail_html_missing_content_returns_empty():
    assert parse_detail_html("<html><body>no content here</body></html>") == ""

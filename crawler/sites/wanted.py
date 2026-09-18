import logging
import time
from datetime import datetime

import requests

from crawler.base import RawJobPosting, SiteAdapter

logger = logging.getLogger(__name__)

BASE_URL = "https://www.wanted.co.kr"
SEARCH_PATH = "/api/chaos/search/v1/position"
DETAIL_PATH_TEMPLATE = "/api/chaos/jobs/v5/{job_id}/details"

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
)

DETAIL_SECTIONS = [
    ("회사소개", "intro"),
    ("주요업무", "main_tasks"),
    ("자격요건", "requirements"),
    ("우대사항", "preferred_points"),
    ("복지", "benefits"),
]


class WantedAdapter(SiteAdapter):
    name = "wanted"

    def __init__(self, request_delay: float = 0.5, timeout: float = 10.0):
        self.request_delay = request_delay
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": USER_AGENT, "Accept": "application/json"})

    def search(self, keyword: str, max_results: int = 10) -> list[RawJobPosting]:
        search_json = self._fetch_search_json(keyword, max_results)
        listings = parse_search_results(search_json, max_results)

        postings = []
        for listing in listings:
            time.sleep(self.request_delay)
            detail_json = self._fetch_detail_json(listing["external_id"])
            postings.append(
                RawJobPosting(
                    external_id=listing["external_id"],
                    title=listing["title"],
                    url=listing["url"],
                    company_name=listing["company_name"],
                    raw_text=build_raw_text(listing, detail_json),
                    deadline_at=parse_due_time(detail_json),
                )
            )
        return postings

    def _fetch_search_json(self, keyword: str, max_results: int) -> dict:
        params = {
            "query": keyword,
            "country": "all",
            "years": -1,
            "sort": "job.recommend_order",
            "limit": max_results,
            "offset": 0,
        }
        resp = self.session.get(BASE_URL + SEARCH_PATH, params=params, timeout=self.timeout)
        resp.raise_for_status()
        return resp.json()

    def _fetch_detail_json(self, job_id: str) -> dict:
        resp = self.session.get(BASE_URL + DETAIL_PATH_TEMPLATE.format(job_id=job_id), timeout=self.timeout)
        resp.raise_for_status()
        return resp.json()


def parse_search_results(search_json: dict, max_results: int) -> list[dict]:
    results = []
    for item in search_json.get("data", [])[:max_results]:
        job_id = item.get("id")
        company = item.get("company") or {}
        if job_id is None or not company.get("name"):
            continue
        results.append(
            {
                "external_id": str(job_id),
                "title": item.get("position", ""),
                "company_name": company["name"],
                "url": f"{BASE_URL}/wd/{job_id}",
            }
        )
    return results


def build_raw_text(listing: dict, detail_json: dict) -> str:
    job = detail_json.get("data", {}).get("job", {}) or {}
    detail = job.get("detail", {}) or {}
    address = job.get("address") or {}
    skill_tags = [t.get("text", "") for t in job.get("skill_tags", []) if t.get("text")]

    annual_from = job.get("annual_from")
    annual_to = job.get("annual_to")

    meta_lines = [
        f"회사: {listing['company_name']}",
        f"공고명: {listing['title']}",
        f"경력: {annual_from}~{annual_to}년" if annual_from is not None else "",
        f"고용형태: {job.get('employment_type', '')}",
        f"지역: {address.get('full_location', '')}",
        f"기술태그: {', '.join(skill_tags)}" if skill_tags else "",
    ]

    body_parts = [f"[{label}]\n{detail[key]}" for label, key in DETAIL_SECTIONS if detail.get(key)]

    meta_text = "\n".join(line for line in meta_lines if line)
    body_text = "\n\n".join(body_parts)
    return f"{meta_text}\n\n{body_text}" if body_text else meta_text


def parse_due_time(detail_json: dict) -> datetime | None:
    due_time = (detail_json.get("data", {}).get("job", {}) or {}).get("due_time")
    if not due_time:
        return None
    try:
        return datetime.fromisoformat(due_time.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        logger.warning("due_time 파싱 실패: %r", due_time)
        return None

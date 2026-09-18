import logging
import re
import time
from datetime import date, datetime, timedelta

import requests
from bs4 import BeautifulSoup

from crawler.base import RawJobPosting, SiteAdapter

logger = logging.getLogger(__name__)

BASE_URL = "https://www.saramin.co.kr"
SEARCH_PATH = "/zf_user/search/recruit"
DETAIL_PATH = "/zf_user/jobs/relay/view-detail"

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
)


class SaraminAdapter(SiteAdapter):
    name = "saramin"

    def __init__(self, request_delay: float = 0.8, timeout: float = 10.0):
        self.request_delay = request_delay
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": USER_AGENT})

    def search(self, keyword: str, max_results: int = 10) -> list[RawJobPosting]:
        html = self._fetch_search_html(keyword, max_results)
        listings = parse_search_results(html, max_results)

        postings = []
        for listing in listings:
            time.sleep(self.request_delay)
            detail_html = self._fetch_detail_html(listing["external_id"])
            description = parse_detail_html(detail_html)
            raw_text = listing["meta_text"] + "\n\n" + description
            postings.append(
                RawJobPosting(
                    external_id=listing["external_id"],
                    title=listing["title"],
                    url=listing["url"],
                    company_name=listing["company_name"],
                    company_url=listing["company_url"],
                    posted_at=listing["posted_at"],
                    deadline_at=listing["deadline_at"],
                    raw_text=raw_text,
                )
            )
        return postings

    def _fetch_search_html(self, keyword: str, max_results: int) -> str:
        params = {
            "searchword": keyword,
            "recruitPage": 1,
            "recruitPageCount": max_results,
            "recruitSort": "relation",
        }
        resp = self.session.get(BASE_URL + SEARCH_PATH, params=params, timeout=self.timeout)
        resp.raise_for_status()
        return resp.text

    def _fetch_detail_html(self, external_id: str) -> str:
        params = {"rec_idx": external_id, "rec_seq": 0}
        resp = self.session.get(BASE_URL + DETAIL_PATH, params=params, timeout=self.timeout)
        resp.raise_for_status()
        return resp.text


def parse_search_results(html: str, max_results: int) -> list[dict]:
    soup = BeautifulSoup(html, "lxml")

    results = []
    for item in soup.select(".item_recruit")[:max_results]:
        external_id = item.get("value")
        title_el = item.select_one(".job_tit a")
        company_el = item.select_one(".corp_name a")
        if not external_id or not title_el or not company_el:
            continue

        condition_spans = [s.get_text(strip=True) for s in item.select(".job_condition span")]
        sector_tags = [a.get_text(strip=True) for a in item.select(".job_sector a")]
        deadline_el = item.select_one(".job_date .date")
        modified_el = item.select_one(".job_day")

        title = title_el.get("title") or title_el.get_text(strip=True)
        deadline_text = deadline_el.get_text(strip=True) if deadline_el else ""
        modified_text = modified_el.get_text(strip=True) if modified_el else ""

        meta_lines = [
            f"회사: {company_el.get_text(strip=True)}",
            f"공고명: {title}",
            f"조건: {' / '.join(condition_spans)}" if condition_spans else "",
            f"직무 태그: {', '.join(sector_tags)}" if sector_tags else "",
            f"마감: {deadline_text}" if deadline_text else "",
        ]

        company_href = company_el.get("href")
        results.append(
            {
                "external_id": external_id,
                "title": title,
                "url": f"{BASE_URL}/zf_user/jobs/relay/view?rec_idx={external_id}",
                "company_name": company_el.get_text(strip=True),
                "company_url": BASE_URL + company_href if company_href else None,
                "posted_at": _parse_modified_date(modified_text),
                "deadline_at": _parse_deadline(deadline_text),
                "meta_text": "\n".join(line for line in meta_lines if line),
            }
        )
    return results


def parse_detail_html(html: str) -> str:
    soup = BeautifulSoup(html, "lxml")
    content = soup.select_one(".user_content")
    if not content:
        logger.warning("상세 설명(.user_content)을 찾지 못했습니다.")
        return ""
    return content.get_text("\n", strip=True)


def _parse_modified_date(text: str) -> datetime | None:
    match = re.search(r"(\d{2})/(\d{2})/(\d{2})", text)
    if not match:
        return None
    yy, mm, dd = (int(part) for part in match.groups())
    return datetime(2000 + yy, mm, dd)


def _parse_deadline(text: str) -> datetime | None:
    match = re.search(r"(\d{1,2})/(\d{1,2})", text)
    if not match:
        return None
    month, day = (int(part) for part in match.groups())
    today = date.today()
    candidate = date(today.year, month, day)
    if candidate < today - timedelta(days=30):
        candidate = date(today.year + 1, month, day)
    return datetime(candidate.year, candidate.month, candidate.day)

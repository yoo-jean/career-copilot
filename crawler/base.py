from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime


@dataclass
class RawJobPosting:
    external_id: str
    title: str
    url: str
    company_name: str
    raw_text: str
    company_url: str | None = None
    posted_at: datetime | None = None
    deadline_at: datetime | None = None


class SiteAdapter(ABC):
    name: str

    @abstractmethod
    def search(self, keyword: str, max_results: int = 10) -> list[RawJobPosting]:
        ...

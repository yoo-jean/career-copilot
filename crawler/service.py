from sqlalchemy.orm import Session

from core.models import Company, JobPosting, JobPostingStatus
from crawler.base import RawJobPosting


def save_job_posting(session: Session, posting: RawJobPosting) -> tuple[JobPosting, bool]:
    """RawJobPosting을 companies/job_postings 테이블에 upsert. (row, created) 반환."""
    existing = session.query(JobPosting).filter_by(url=posting.url).one_or_none()
    if existing:
        return existing, False

    company = session.query(Company).filter_by(name=posting.company_name).one_or_none()
    if company is None:
        company = Company(name=posting.company_name, careers_url=posting.company_url)
        session.add(company)
        session.flush()

    job_posting = JobPosting(
        company_id=company.id,
        title=posting.title,
        url=posting.url,
        raw_text=posting.raw_text,
        posted_at=posting.posted_at,
        deadline_at=posting.deadline_at,
        status=JobPostingStatus.NEW,
    )
    session.add(job_posting)
    session.flush()
    return job_posting, True

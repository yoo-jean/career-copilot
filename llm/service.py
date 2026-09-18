from sqlalchemy.orm import Session

from core.models import JobPosting, JobPostingStatus, JobSummary
from llm.summarizer import summarize_job_posting


def summarize_and_save(session: Session, job_posting: JobPosting) -> JobSummary:
    result = summarize_job_posting(
        title=job_posting.title,
        company_name=job_posting.company.name,
        raw_text=job_posting.raw_text,
    )

    summary = job_posting.summary
    if summary is None:
        summary = JobSummary(job_posting_id=job_posting.id)
        session.add(summary)

    summary.requirements_json = result.requirements_json
    summary.preferred_json = result.preferred_json
    summary.tech_stack_json = result.tech_stack_json
    summary.salary_info = result.salary_info
    summary.summary_text = result.summary_text
    summary.model_used = result.model_used

    job_posting.status = JobPostingStatus.SUMMARIZED
    session.flush()
    return summary

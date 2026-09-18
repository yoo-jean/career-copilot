from sqlalchemy.orm import Session

from core.models import Draft, DraftType, JobPosting
from rag.generator import generate_cover_letter_draft, generate_interview_answer_draft
from rag.retriever import retrieve_relevant_chunks


def _job_summary_text(job_posting: JobPosting) -> str:
    if job_posting.summary and job_posting.summary.summary_text:
        return job_posting.summary.summary_text
    return job_posting.raw_text[:500]


def create_cover_letter_draft(session: Session, job_posting: JobPosting) -> Draft:
    summary_text = _job_summary_text(job_posting)
    chunks = retrieve_relevant_chunks(f"{job_posting.title} {summary_text}", top_k=5)

    content = generate_cover_letter_draft(
        job_title=job_posting.title,
        company_name=job_posting.company.name,
        job_summary_text=summary_text,
        career_chunks=chunks,
    )

    draft = Draft(job_posting_id=job_posting.id, draft_type=DraftType.COVER_LETTER, content=content)
    session.add(draft)
    session.flush()
    return draft


def create_interview_answer_draft(session: Session, job_posting: JobPosting, question: str) -> Draft:
    summary_text = _job_summary_text(job_posting)
    chunks = retrieve_relevant_chunks(f"{question} {job_posting.title} {summary_text}", top_k=5)

    content = generate_interview_answer_draft(
        question=question,
        job_title=job_posting.title,
        company_name=job_posting.company.name,
        job_summary_text=summary_text,
        career_chunks=chunks,
    )

    draft = Draft(
        job_posting_id=job_posting.id,
        draft_type=DraftType.INTERVIEW_ANSWER,
        question=question,
        content=content,
    )
    session.add(draft)
    session.flush()
    return draft

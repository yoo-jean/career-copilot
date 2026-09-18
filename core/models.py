import enum
from datetime import datetime, timezone

from sqlalchemy import Enum, ForeignKey, JSON, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class JobPostingStatus(str, enum.Enum):
    NEW = "new"
    SUMMARIZED = "summarized"
    APPLIED = "applied"
    REJECTED = "rejected"
    CLOSED = "closed"


class DraftType(str, enum.Enum):
    COVER_LETTER = "cover_letter"
    INTERVIEW_ANSWER = "interview_answer"


class ApplicationStatus(str, enum.Enum):
    APPLIED = "applied"
    DOCUMENT_PASSED = "document_passed"
    INTERVIEW_SCHEDULED = "interview_scheduled"
    OFFER = "offer"
    REJECTED = "rejected"


class Company(Base):
    __tablename__ = "companies"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(unique=True)
    careers_url: Mapped[str | None] = mapped_column()
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(default=utcnow)

    job_postings: Mapped[list["JobPosting"]] = relationship(back_populates="company")


class JobPosting(Base):
    __tablename__ = "job_postings"

    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"))
    title: Mapped[str]
    url: Mapped[str] = mapped_column(unique=True)
    raw_text: Mapped[str] = mapped_column(Text)
    posted_at: Mapped[datetime | None] = mapped_column()
    deadline_at: Mapped[datetime | None] = mapped_column()
    crawled_at: Mapped[datetime] = mapped_column(default=utcnow)
    status: Mapped[JobPostingStatus] = mapped_column(Enum(JobPostingStatus), default=JobPostingStatus.NEW)
    created_at: Mapped[datetime] = mapped_column(default=utcnow)

    company: Mapped["Company"] = relationship(back_populates="job_postings")
    summary: Mapped["JobSummary | None"] = relationship(back_populates="job_posting", uselist=False)
    drafts: Mapped[list["Draft"]] = relationship(back_populates="job_posting")
    application: Mapped["Application | None"] = relationship(back_populates="job_posting", uselist=False)


class JobSummary(Base):
    __tablename__ = "job_summaries"

    id: Mapped[int] = mapped_column(primary_key=True)
    job_posting_id: Mapped[int] = mapped_column(ForeignKey("job_postings.id"), unique=True)
    requirements_json: Mapped[list | None] = mapped_column(JSON)
    preferred_json: Mapped[list | None] = mapped_column(JSON)
    tech_stack_json: Mapped[list | None] = mapped_column(JSON)
    salary_info: Mapped[str | None] = mapped_column()
    summary_text: Mapped[str | None] = mapped_column(Text)
    model_used: Mapped[str | None] = mapped_column()
    created_at: Mapped[datetime] = mapped_column(default=utcnow)

    job_posting: Mapped["JobPosting"] = relationship(back_populates="summary")


class CareerDocument(Base):
    __tablename__ = "career_documents"

    id: Mapped[int] = mapped_column(primary_key=True)
    source_type: Mapped[str]  # 경력기술서 / 프로젝트설명 / 기존자소서 등
    title: Mapped[str]
    content: Mapped[str] = mapped_column(Text)
    file_path: Mapped[str | None] = mapped_column()
    content_hash: Mapped[str | None] = mapped_column()
    created_at: Mapped[datetime] = mapped_column(default=utcnow)

    chunks: Mapped[list["CareerChunk"]] = relationship(back_populates="document")


class CareerChunk(Base):
    __tablename__ = "career_chunks"

    id: Mapped[int] = mapped_column(primary_key=True)
    career_document_id: Mapped[int] = mapped_column(ForeignKey("career_documents.id"))
    chunk_text: Mapped[str] = mapped_column(Text)
    chroma_embedding_id: Mapped[str] = mapped_column(unique=True)
    chunk_index: Mapped[int]

    document: Mapped["CareerDocument"] = relationship(back_populates="chunks")


class Draft(Base):
    __tablename__ = "drafts"

    id: Mapped[int] = mapped_column(primary_key=True)
    job_posting_id: Mapped[int] = mapped_column(ForeignKey("job_postings.id"))
    draft_type: Mapped[DraftType] = mapped_column(Enum(DraftType))
    question: Mapped[str | None] = mapped_column(Text)
    content: Mapped[str] = mapped_column(Text)
    version: Mapped[int] = mapped_column(default=1)
    created_at: Mapped[datetime] = mapped_column(default=utcnow)

    job_posting: Mapped["JobPosting"] = relationship(back_populates="drafts")


class Application(Base):
    __tablename__ = "applications"

    id: Mapped[int] = mapped_column(primary_key=True)
    job_posting_id: Mapped[int] = mapped_column(ForeignKey("job_postings.id"), unique=True)
    applied_at: Mapped[datetime | None] = mapped_column()
    status: Mapped[ApplicationStatus] = mapped_column(Enum(ApplicationStatus), default=ApplicationStatus.APPLIED)
    notes: Mapped[str | None] = mapped_column(Text)

    job_posting: Mapped["JobPosting"] = relationship(back_populates="application")

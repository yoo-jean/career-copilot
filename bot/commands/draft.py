import asyncio

import discord
from discord import app_commands

from core.db import session_scope
from core.models import Draft, JobPosting
from rag.service import create_cover_letter_draft, create_interview_answer_draft

DRAFT_TYPE_LABELS_KO = {
    "cover_letter": "자소서 초안",
    "interview_answer": "면접 답변 초안",
}


def build_draft_embed(posting: JobPosting, draft: Draft) -> discord.Embed:
    label = DRAFT_TYPE_LABELS_KO.get(draft.draft_type.value, draft.draft_type.value)
    embed = discord.Embed(
        title=f"[{label}] {posting.company.name} - {posting.title}"[:256],
        url=posting.url,
        description=draft.content[:4096],
        color=discord.Color.purple(),
    )
    if draft.question:
        embed.add_field(name="질문", value=draft.question[:1024], inline=False)
    return embed


def _generate_cover_letter_embed(job_id: int) -> discord.Embed | str:
    with session_scope() as session:
        posting = session.get(JobPosting, job_id)
        if posting is None:
            return f"#{job_id} 공고를 찾을 수 없습니다. /jobs로 번호를 확인해주세요."

        draft = create_cover_letter_draft(session, posting)
        return build_draft_embed(posting, draft)


def _generate_interview_answer_embed(job_id: int, question: str) -> discord.Embed | str:
    with session_scope() as session:
        posting = session.get(JobPosting, job_id)
        if posting is None:
            return f"#{job_id} 공고를 찾을 수 없습니다. /jobs로 번호를 확인해주세요."

        draft = create_interview_answer_draft(session, posting, question)
        return build_draft_embed(posting, draft)


def register(tree: app_commands.CommandTree) -> None:
    @tree.command(name="draft-letter", description="채용공고에 대한 자소서 초안을 생성합니다.")
    @app_commands.describe(job_id="/jobs 목록에 표시된 공고 번호(#)")
    async def draft_letter_command(interaction: discord.Interaction, job_id: int) -> None:
        await interaction.response.defer()
        result = await asyncio.to_thread(_generate_cover_letter_embed, job_id)

        if isinstance(result, str):
            await interaction.followup.send(result)
        else:
            await interaction.followup.send(embed=result)

    @tree.command(name="draft-interview", description="채용공고 면접 질문에 대한 답변 초안을 생성합니다.")
    @app_commands.describe(job_id="/jobs 목록에 표시된 공고 번호(#)", question="예상 면접 질문")
    async def draft_interview_command(interaction: discord.Interaction, job_id: int, question: str) -> None:
        await interaction.response.defer()
        result = await asyncio.to_thread(_generate_interview_answer_embed, job_id, question)

        if isinstance(result, str):
            await interaction.followup.send(result)
        else:
            await interaction.followup.send(embed=result)

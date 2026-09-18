import asyncio

import discord
from discord import app_commands

from core.db import session_scope
from core.models import JobPosting, JobSummary
from llm.service import summarize_and_save


def build_summary_embed(posting: JobPosting, summary: JobSummary) -> discord.Embed:
    requirements = "\n".join(f"- {r}" for r in summary.requirements_json) or "- (정보 없음)"
    preferred = "\n".join(f"- {r}" for r in summary.preferred_json) or "- (정보 없음)"
    tech_stack = ", ".join(summary.tech_stack_json) or "정보 없음"

    embed = discord.Embed(
        title=f"[{posting.company.name}] {posting.title}"[:256],
        url=posting.url,
        description=(summary.summary_text or "(요약 없음)")[:4096],
        color=discord.Color.green(),
    )
    embed.add_field(name="자격요건", value=requirements[:1024], inline=False)
    embed.add_field(name="우대사항", value=preferred[:1024], inline=False)
    embed.add_field(name="기술스택", value=tech_stack[:1024], inline=True)
    embed.add_field(name="급여", value=(summary.salary_info or "정보 없음")[:1024], inline=True)
    if posting.deadline_at:
        embed.set_footer(text=f"마감: {posting.deadline_at.strftime('%Y-%m-%d')}")
    return embed


def _fetch_or_build_summary_embed(job_id: int) -> discord.Embed | str:
    with session_scope() as session:
        posting = session.get(JobPosting, job_id)
        if posting is None:
            return f"#{job_id} 공고를 찾을 수 없습니다. /jobs로 번호를 확인해주세요."

        summary = posting.summary
        if summary is None:
            summary = summarize_and_save(session, posting)

        return build_summary_embed(posting, summary)


def register(tree: app_commands.CommandTree) -> None:
    @tree.command(name="summarize", description="채용공고 요약을 보여줍니다 (없으면 새로 생성).")
    @app_commands.describe(job_id="/jobs 목록에 표시된 공고 번호(#)")
    async def summarize_command(interaction: discord.Interaction, job_id: int) -> None:
        await interaction.response.defer()
        result = await asyncio.to_thread(_fetch_or_build_summary_embed, job_id)

        if isinstance(result, str):
            await interaction.followup.send(result)
        else:
            await interaction.followup.send(embed=result)

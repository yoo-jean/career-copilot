import asyncio

import discord
from discord import app_commands

from core.db import session_scope
from core.models import JobPosting

STATUS_LABELS_KO = {
    "new": "신규",
    "summarized": "요약완료",
    "applied": "지원완료",
    "rejected": "불합격",
    "closed": "마감",
}


def build_jobs_embed(postings: list[JobPosting]) -> discord.Embed:
    if not postings:
        return discord.Embed(description="저장된 채용공고가 없습니다.")

    lines = []
    for p in postings:
        deadline = p.deadline_at.strftime("%m/%d") if p.deadline_at else "미상"
        status_label = STATUS_LABELS_KO.get(p.status.value, p.status.value)
        lines.append(f"**#{p.id}** [{p.company.name}]({p.url}) - {p.title}\n마감 {deadline} · {status_label}")

    return discord.Embed(
        title=f"최근 채용공고 {len(postings)}건",
        description="\n\n".join(lines),
        color=discord.Color.blurple(),
    )


def _fetch_recent_jobs_embed(count: int) -> discord.Embed:
    with session_scope() as session:
        postings = session.query(JobPosting).order_by(JobPosting.crawled_at.desc()).limit(count).all()
        return build_jobs_embed(postings)


def register(tree: app_commands.CommandTree) -> None:
    @tree.command(name="jobs", description="최근 크롤링된 채용공고 목록을 보여줍니다.")
    @app_commands.describe(count="표시할 개수 (기본 5, 최대 10)")
    async def jobs_command(interaction: discord.Interaction, count: int = 5) -> None:
        count = max(1, min(count, 10))
        await interaction.response.defer()
        embed = await asyncio.to_thread(_fetch_recent_jobs_embed, count)
        await interaction.followup.send(embed=embed)

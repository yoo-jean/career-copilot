import logging

import discord
from discord.ext import commands

from bot.commands import draft, jobs, summarize
from config.settings import get_settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


class CareerCopilotBot(commands.Bot):
    def __init__(self) -> None:
        super().__init__(command_prefix="!", intents=discord.Intents.default())

    async def setup_hook(self) -> None:
        jobs.register(self.tree)
        summarize.register(self.tree)
        draft.register(self.tree)

        settings = get_settings()
        if settings.discord_guild_id:
            guild = discord.Object(id=settings.discord_guild_id)
            self.tree.copy_global_to(guild=guild)
            await self.tree.sync(guild=guild)
            logger.info("슬래시 커맨드를 길드(%s)에 동기화했습니다 (즉시 반영).", settings.discord_guild_id)
        else:
            await self.tree.sync()
            logger.info("슬래시 커맨드를 전역 동기화했습니다 (반영까지 최대 1시간 소요).")


def main() -> None:
    settings = get_settings()
    if not settings.discord_bot_token:
        raise RuntimeError("DISCORD_BOT_TOKEN이 설정되지 않았습니다 (.env를 확인하세요).")

    bot = CareerCopilotBot()

    @bot.event
    async def on_ready() -> None:
        logger.info("로그인 완료: %s", bot.user)

    bot.run(settings.discord_bot_token, log_handler=None)


if __name__ == "__main__":
    main()

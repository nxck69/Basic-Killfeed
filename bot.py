import asyncio
import logging
from pathlib import Path

import nextcord
from nextcord.ext import commands

from config import DISCORD_BOT_TOKEN

logging.basicConfig(level=logging.INFO)

INTENTS = nextcord.Intents(
    bans=False,
    dm_messages=False,
    dm_reactions=False,
    dm_typing=False,
    emojis=False,
    emojis_and_stickers=False,
    guild_messages=False,
    guild_reactions=False,
    guild_typing=False,
    guilds=True,
    integrations=False,
    invites=False,
    members=False,
    messages=False,
    presences=False,
    reactions=False,
    typing=False,
    voice_states=False,
    webhooks=False,
)


class Bot(commands.Bot):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.CWD: Path = Path(__file__).resolve().parent
        self.read_lines: dict[int, list[str]] = {}
        self.last_log: dict[int, str] = {}

        self.load_extension("cogs.killfeed")


async def run() -> None:
    bot = Bot(intents=INTENTS, command_prefix=None)
    await bot.start(DISCORD_BOT_TOKEN)


if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(run())

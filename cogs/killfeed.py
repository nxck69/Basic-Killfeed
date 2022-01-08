import asyncio
import logging
import random
import re
from typing import Any, Coroutine

import aiofiles
import nextcord
from aiohttp import ClientSession
from nextcord.ext import commands, tasks

from bot import Bot
from config import SERVICE_IDS, MAPS, DESIGN, NITRADO_TOKENS
from patterns import (
    VICTIM_NAME,
    KILLER_NAME,
    WEAPON,
    MELEE_WEAPON,
    COORDS,
    DISTANCE,
    TIME,
)

REQUIRED_KEYWORDS: tuple[str, str] = (
    "AdminLog started on ",
    " killed by Player ",
)

logger: logging.Logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class Killfeed(commands.Cog):
    def __init__(self, bot: Bot) -> None:
        self.bot = bot
        self.killfeed.start()

    async def download_logfile(self, service_id: int) -> bool:
        nitrado_token: str = NITRADO_TOKENS.get(service_id, "")
        headers = {"Authorization": nitrado_token}

        async with ClientSession() as sess:
            async with sess.get(
                f"https://api.nitrado.net/services/{service_id}/gameservers",
                headers=headers,
            ) as res:
                if res.status != 200:
                    logger.warning(
                        f"Failed to get the Server Information. Make sure the Service ID and Nitrado Token are valid. {res.status}"
                    )
                    return False

                json: dict = await res.json()

            ftp_username: str = json["data"]["gameserver"]["username"]
            game: str = json["data"]["gameserver"]["game"]

            match game.lower():
                case "dayzps":
                    path: str = "dayzps/config/DayZServer_PS4_x64.ADM"

                case "dayzxb":
                    path: str = "dayzxb/config/DayZServer_X1_x64.ADM"

                case _:
                    logger.error("PC Servers are not supported.")
                    return False

            params: dict[str, str] = {
                "file": f"/games/{ftp_username}/noftp/{path}"
            }
            async with sess.get(
                f"https://api.nitrado.net/services/{service_id}/gameservers/file_server/download",
                headers=headers,
                params=params,
            ) as resp:
                if resp.status != 200:
                    logger.error(
                        f"Failed to get the Download-Link for {service_id}. {resp.status}"
                    )
                    return False

                json: dict = await resp.json()

            download_url: str = json["data"]["token"]["url"]
            async with sess.get(download_url, headers=headers) as r:
                if r.status != 200:
                    logger.error(
                        f"Failed to download the Logfile for {service_id}."
                    )
                    return False

                async with aiofiles.open(
                    self.bot.CWD.joinpath(f"logs/{service_id}.ADM"), mode="wb+"
                ) as file:
                    await file.write(await r.read())

                return True

    @staticmethod
    async def post_embed(
        channel: nextcord.TextChannel, embed: nextcord.Embed
    ) -> None:
        await asyncio.sleep(
            random.randint(0, 3)
        )  # Rate Limits with multiple Servers

        try:
            await channel.send(embed=embed)

        except (nextcord.HTTPException, nextcord.Forbidden) as e:
            logger.warning(f"Failed to post an Embed: {e}")

    @staticmethod
    def get_izurvive_url(x: Any, z: Any, y: Any, service_id: int) -> str:
        dayz_map: str = MAPS.get(service_id, "chernarus")
        match dayz_map.lower():
            case "livonia":
                return f"[{x}, {z}, {y}](https://www.izurvive.com/livonia/#location={x};{z})"

            case "chernarus":
                return f"[{x}, {z}, {y}](https://www.izurvive.com/#location={x};{z})"

            case _:
                raise ValueError(
                    f"Invalid Map provided for {service_id}. Available Maps: chernarus, livonia"
                )

    @commands.Cog.listener("on_ready")
    async def on_ready(self) -> None:
        logger.debug("Starting Killfeed ...")

    async def new_logfile(self, service_id: int) -> bool:
        async with aiofiles.open(
            self.bot.CWD.joinpath(f"logs/{service_id}.ADM"), "r"
        ) as f:
            all_admin_log_lines = re.findall(
                "AdminLog started on ", await f.read()
            )
            return len(all_admin_log_lines) == 1

    @tasks.loop(minutes=3)
    async def killfeed(self) -> None:
        coroutines: list[Coroutine[Any, Any, None]] = []

        for service_id in SERVICE_IDS.keys():
            if await self.download_logfile(service_id):
                if service_id not in self.bot.read_lines:
                    self.bot.read_lines[service_id] = []

                if service_id not in self.bot.last_log:
                    self.bot.last_log[service_id] = ""

                coroutines.append(self.check_log(service_id))

        await asyncio.gather(*coroutines)

    @killfeed.before_loop
    async def before_killfeed(self) -> None:
        await self.bot.wait_until_ready()

    async def check_log(self, service_id: int) -> None:
        logger.debug(f"Checking Log for {service_id}...")

        channel = self.bot.get_channel(SERVICE_IDS.get(service_id))
        if not isinstance(channel, nextcord.TextChannel):
            logger.warning(
                f"Invalid Channel provided for {service_id}... Skipping Server..."
            )
            return

        async with aiofiles.open(
            self.bot.CWD.joinpath(f"logs/{service_id}.ADM"), mode="r"
        ) as file:
            async for line in file:
                if line in self.bot.read_lines[service_id]:
                    continue

                if (
                    not any(word in line for word in REQUIRED_KEYWORDS)
                    or "id=Unknown" in line
                ):
                    continue

                if "AdminLog started on " in line:
                    if self.bot.last_log[service_id] != line:
                        if not self.bot.last_log[service_id]:
                            self.bot.last_log[service_id] = line

                        else:
                            if await self.new_logfile(
                                service_id
                            ):  # Prevent double Posts when the Log is bugged
                                self.bot.last_log[service_id] = line
                                self.bot.read_lines[service_id].clear()

                else:
                    self.bot.read_lines[service_id].append(line)

                    try:
                        victim_name, killer_name = re.search(
                            VICTIM_NAME, line
                        ).group(1), re.search(KILLER_NAME, line).group(1)
                        weapon: str = (
                            re.search(WEAPON, line)
                            or re.search(MELEE_WEAPON, line)
                        ).group(1)
                        x, z, y = (
                            re.search(COORDS, line)
                            .group(1)
                            .replace(" ", "")
                            .split(",")
                        )
                        time = re.search(TIME, line).group(1)

                    except AttributeError as e:
                        logger.error(
                            f"Failed to extract Information from Line: \n{line}\nReason: {e}\nPlease open a Issue on the Github Repo"
                        )

                    try:
                        distance: float = round(
                            float(re.search(DISTANCE, line).group(1)), 2
                        )

                    except (AttributeError, ValueError):
                        distance: float = 0.0  # Killed with Melee Weapon

                    map_url: str = self.get_izurvive_url(x, z, y, service_id)

                    thumbnail_url, colour = DESIGN.get(
                        service_id, (None, 0xFF0000)
                    )
                    embed = nextcord.Embed(
                        description=f"**:skull_crossbones: PvP Kill | {time}**\n\n**`{victim_name}`** has been killed by **`{killer_name}`**.\nWeapon: **`{weapon}`**\nDistance: **{distance} {'meter' if distance == 0 else 'meters'}** ",
                        colour=colour,
                    ).add_field(
                        name=f":round_pushpin: Location :round_pushpin:",
                        value=f"{map_url}",
                    )

                    if thumbnail_url:
                        embed.set_thumbnail(url=thumbnail_url)

                    await self.post_embed(channel, embed)

        logger.debug(f"Finished checking Log for {service_id}...")


def setup(bot: Bot) -> None:
    bot.add_cog(Killfeed(bot))

import asyncio
import os
import sys

import yaml

from bot.bot import Bot
from bot.tgacli import TGACli

CONFIG_FILE = "config.yaml"


async def main():

    OSTYPE = sys.platform

    # Check for config file
    if not os.path.exists(CONFIG_FILE):
        raise OSError(f"{CONFIG_FILE} not found or missing")

    # Read in config file
    with open(CONFIG_FILE, 'r', encoding='UTF-8') as CONFIG_YAML:
        CONFIG = yaml.full_load(CONFIG_YAML)

    bots = []
    for bot_id, bot_config in enumerate(CONFIG, start=1):

        # Use enumeration as bot's ID
        bot_config.update({'bot_id': bot_id})

        bots.append(Bot(bot_config, OSTYPE))

    # The CLI runs in its own thread and schedules bot shutdown back onto this loop
    TGACli(bots, OSTYPE, asyncio.get_running_loop())

    try:
        # Every bot shares this event loop, discord.py drives them concurrently
        await asyncio.gather(*(bot.start(bot.get_token()) for bot in bots))
    finally:
        await asyncio.gather(*(bot.close() for bot in bots),
                             return_exceptions=True)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass

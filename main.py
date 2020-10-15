import os
import threading
import asyncio
import yaml
import signal
import sys
from bot.bot import Bot
from bot.tgacli import TGACli


async def threadedBot(bot):
    await bot.start(bot.get_token())


def loopTheBot(loop):
    if not loop.is_running():
        loop.run_forever()


def main():
    def signal_handler(
        sig,
        frame,
    ):
        sys.exit(0)

    bots = []
    config_file = "config.yaml"

    # May replace with with platform.system() later
    OSTYPE = sys.platform
    # Check for config file
    if not os.path.exists(config_file):
        raise OSError(f"{config_file} not found or missing")

    # Read in config file
    with open(config_file, 'r', encoding='UTF-8') as config_yaml:
        CONFIG = yaml.full_load(config_yaml)

    for botConfig in CONFIG:
        if OSTYPE == 'win32':
            asyncio.set_event_loop_policy(
                asyncio.WindowsSelectorEventLoopPolicy())
        else:
            asyncio.get_child_watcher()

        loop = asyncio.get_event_loop()

        bot = Bot(botConfig, OSTYPE)
        loop.create_task(threadedBot(bot))

        thread = threading.Thread(target=loopTheBot,
                                  args=(loop, ),
                                  daemon=True)
        bot.thread = thread
        bot.loop = loop
        bots.append(bot)
        thread.start()

    # Setup the cli in its own thread
    TGACli(bots, OSTYPE)

    # Properly handle the control+c
    signal.signal(signal.SIGINT, signal_handler)


if __name__ == "__main__":
    main()

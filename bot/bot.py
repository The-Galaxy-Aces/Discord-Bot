import os
import logging
import discord
from discord.ext import commands
from time import localtime, strftime

from bot.features.insult.insult import Insult
from bot.features.music.music import Music
from bot.features.utility.utility import Utility


class Bot(commands.Bot):
    """
    The Bot class.
    The bot can do lots of neat things
    """
    def __init__(self, CONFIG, OSTYPE):

        # Check CONFIG for minimal required params to make bot run properly
        REQUIRED_PARAMS = [
            'bot_id', 'command_prefix','enabled_features',
            'logging', 'name', 'token'
        ]

        MISSING_PARAMS = [
            param for param in REQUIRED_PARAMS if not CONFIG.get(param)
        ]

        if MISSING_PARAMS:
            raise AssertionError(f"config.yaml missing {MISSING_PARAMS}")

        # Start bot construction
        self.os_type = OSTYPE
        self.bot_id = CONFIG.get('bot_id')
        self.command_prefix = CONFIG.get('command_prefix')
        self.enabled_features = CONFIG.get('enabled_features')
        self.logging = CONFIG.get('logging', 'NOTSET')
        self.name = CONFIG.get('name')
        self.token = CONFIG.get('token')

        # message_content is a privileged intent and must also be enabled for the
        # bot in the Discord developer portal, otherwise prefixed commands are
        # never received.
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix=self.command_prefix, intents=intents)

        self.cog_list = []

        if self.logging:
            self._setup_logging()
        self.log.info(f"Logging level: {self.logging}")

        self.log.info(f"{self.name} initalized")

    async def setup_hook(self):
        """
        Called by discord.py once the bot is logging in. Cogs must be added from
        an async context because Bot.add_cog is a coroutine as of discord.py 2.0.
        """
        await self._enable_features()

    def _setup_logging(self):
        """
        Determines a viable path for storing logging using os_type and attempts to generate a log file
        or it will append to current log file if one exists.
        """
        LOG_PATHS = {
            "win32" : "logs",
            "linux" : os.path.join("/var", "log", "discord_bot"),
        }
        LOG_PATH = LOG_PATHS[self.os_type]
        DATE_STAMP = strftime("%Y-%m-%d", localtime())
        FILE_NAME = f"discord_bot-{self.name}-{DATE_STAMP}.log"
        FILE_PATH = os.path.join(LOG_PATH, FILE_NAME)
        FORMAT = "%(asctime)s:%(levelname)s:%(name)s: %(message)s"

        if not os.path.exists(LOG_PATH):
            os.mkdir(LOG_PATH)

        self.log = logging.getLogger(f"{self.name} Logger")
        self.log.setLevel(self.logging)
        self.handler = logging.FileHandler(filename=FILE_PATH)
        self.handler.setFormatter(logging.Formatter(FORMAT))
        self.log.addHandler(self.handler)

    async def _enable_features(self):
        VALID_FEATURES = {
            "insult" : Insult,
            "music" : Music,
            "utility" : Utility
        }

        print(f"{self.name} enabled features:", end="\n")
        for feature in self.enabled_features:

            # Check to ensure features being fed in are actually there
            if feature.lower() not in VALID_FEATURES:
                self.log.error(f"Config feature, {feature}, does not exist")
            else:
                if self.enabled_features[feature]["enabled"]:
                    cog = VALID_FEATURES[feature](self)
                    await cog.enable_cog()
                    self.cog_list.append(cog)
                    print(f"  {feature}", end="\n")

    def get_token(self):
        return self.token

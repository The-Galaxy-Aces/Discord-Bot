import os
import logging
import discord
import discord.ext
from time import localtime, strftime

from bot.features.insult.insult import Insult
from bot.features.music.music import Music
from bot.features.utility.utility import Utility


class Bot(discord.ext.commands.Bot):
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
        
        # Set up Discord intents (required for discord.py 2.x)
        intents = discord.Intents.default()
        intents.message_content = True  # Required for reading message content
        intents.voice_states = True     # Required for music functionality
        intents.
        
        # Initialize parent class first
        super().__init__(command_prefix=self.command_prefix, intents=intents)

        self.cog_list = []

        if self.logging and self.logging != 'NOTSET':
            self._setup_logging()
        else:
            # Set up console logging for NOTSET or missing logging config
            self.log = logging.getLogger(f"{self.name} Logger")
            
            # Convert string logging levels to actual levels
            if self.logging == 'NOTSET':
                log_level = logging.NOTSET  # This is 0, shows everything
            else:
                log_level = logging.INFO  # Default fallback
                
            self.log.setLevel(log_level)
            
            # Add a console handler for output
            console_handler = logging.StreamHandler()
            console_handler.setLevel(log_level)
            formatter = logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s')
            console_handler.setFormatter(formatter)
            self.log.addHandler(console_handler)
            
        self.log.info(f"Logging level: {self.logging}")

        # Store enabled features for later async loading
        self._features_to_enable = self.enabled_features

        self.log.info(f"{self.name} initialized")

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

        # Convert string log level to actual logging level
        if isinstance(self.logging, str):
            log_level = getattr(logging, self.logging.upper(), logging.INFO)
        else:
            log_level = self.logging

        if not os.path.exists(LOG_PATH):
            os.makedirs(LOG_PATH, exist_ok=True)

        self.log = logging.getLogger(f"{self.name} Logger")
        self.log.setLevel(log_level)
        
        # File handler
        self.handler = logging.FileHandler(filename=FILE_PATH)
        self.handler.setLevel(log_level)
        self.handler.setFormatter(logging.Formatter(FORMAT))
        self.log.addHandler(self.handler)
        
        # Also add console handler so you can see logs in terminal
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        console_handler.setFormatter(logging.Formatter(FORMAT))
        self.log.addHandler(console_handler)

    async def _enable_features_async(self):
        """Load cogs asynchronously after the bot is ready"""
        VALID_FEATURES = {
            "insult" : Insult,
            "music" : Music,
            "utility" : Utility
        }

        print(f"{self.name} enabled features:", end="\n")
        for feature in self._features_to_enable:

            # Check to ensure features being fed in are actually there
            if feature.lower() not in VALID_FEATURES:
                self.log.error(f"Config feature, {feature}, does not exist")
            else:
                if self._features_to_enable[feature]["enabled"]:
                    cog = VALID_FEATURES[feature](self)
                    await cog.enable_cog()
                    self.cog_list.append(cog)
                    print(f"  {feature}", end="\n")

    async def on_ready(self):
        """Called when the bot is ready and connected to Discord"""
        print(f'{self.name} has connected to Discord!')
        await self._enable_features_async()
        print(f'{self.name} cogs loaded successfully!')

    def get_token(self):
        return self.token

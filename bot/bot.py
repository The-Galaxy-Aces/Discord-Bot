import os
import json
import logging
import discord
import discord.ext
from time import localtime, strftime, sleep

from bot.features.insult import Insult
from bot.features.music.music import Music


class Bot(discord.ext.commands.Bot):
    """
    The Bot class.
    The bot can do lots of neat things
    """
    def __init__(self, config_file):
        command_prefix = "!"
        super().__init__(command_prefix)

        # Check for config file
        if not os.path.exists(config_file):
            raise OSError(f"{config_file} not found or missing")

        # Read in config file
        with open(config_file, 'r') as config_json:
            CONFIG = json.load(config_json)

        # Check bot for minimal required params to make bot run properly
        REQUIRED_PARAMS = ['bot_name', 'token']
        MISSING_PARAMS = [
            param for param in REQUIRED_PARAMS if not CONFIG.get(param)
        ]
        if MISSING_PARAMS:
            raise AssertionError(f"config.json missing {MISSING_PARAMS}")

        # Pull information out of parsed config file
        self.name = CONFIG.get('bot_name')
        self.token = CONFIG.get('token')
        self.enabled_features = CONFIG.get('enabled_features')
        self.logging = CONFIG.get('logging')

        # Logging setup
        if bool(self.logging['enabled']):
            FORMAT = "%(asctime)s:%(levelname)s:%(name)s: %(message)s"
            DATE_STAMP = strftime("%Y-%m-%d", localtime())
            FILE_NAME = f"discordBot-{self.name}-{DATE_STAMP}.log"

            self.log = logging.getLogger(f"{self.name} Logger")
            self.log.setLevel(CONFIG['logging']['logging_level'])
            self.handler = logging.FileHandler(filename=FILE_NAME)
            self.handler.setFormatter(logging.Formatter(FORMAT))
            self.log.addHandler(self.handler)

            self.log.info("Bot initalized")

        print("Enabled features:")
        for x in self.enabled_features:
            if self.enabled_features[x]["enabled"] == "True":
                self.add_cog(eval(x.capitalize())(self))
                print(f'\t{x}')
        print("")

    def listEnabledFeatures(self):
        print("Enabled features:")
        for enabled_feature in self.enabled_features:
            if bool(self.enabled_features[enabled_feature]["enabled"]):
                print(f"{enabled_feature}")
        print()

    def get_token(self):
        return self.token

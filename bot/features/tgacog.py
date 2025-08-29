from discord.ext import commands


class TGACog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._last_member = None
        self.ready = False

        self.COG_NAME = self.__class__.__name__.lower()
        self.CONFIG = bot.enabled_features[self.COG_NAME]

        # Load permissions
        self.permissions = self.get_permissions(self.bot)

    def process_config(self, bot, REQUIRED_PARAMS):

        MISSING_PARAMS = [
            param for param in REQUIRED_PARAMS if not self.CONFIG.get(param)
        ]
        if MISSING_PARAMS:
            raise AssertionError(f"config.yaml missing {MISSING_PARAMS}")

    def get_permissions(self, bot):
        return self.CONFIG.get('permissions')

    async def enable_cog(self):
        self.bot.log.debug(f"Enable Cog {self.COG_NAME}")
        await self.bot.add_cog(self)

    async def disable_cog(self):
        self.bot.log.debug(f"Disable Cog {self.COG_NAME}")
        await self.bot.remove_cog(self)

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"{self.bot.name} {self.COG_NAME} is ready!")
        self.ready = True

    async def handle_command_error(self, ctx, error):
        self.bot.log.debug(f"handle_command_error: {error}")
        if isinstance(error, commands.BadArgument):
            await ctx.message.channel.send(
                f"Error in {self.__class__.__name__}: {error}")
        elif isinstance(error, commands.CheckFailure):
            await ctx.message.channel.send(
                "You do not have permissions to use that command.")
        else:
            self.bot.log.error(f"handle_command_error: {error}")

    def check_permissions():
        async def predicate(ctx, *args):
            if ctx.invoked_subcommand:
                cmd_permissions = ctx.cog.permissions.get(
                    ctx.invoked_subcommand.name)
            else:
                cmd_permissions = ctx.cog.permissions.get(ctx.command.name)

            return any(role for role in ctx.author.roles
                       if role.name in cmd_permissions)

        return commands.check(predicate)

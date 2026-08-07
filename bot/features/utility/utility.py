import random
from discord.ext import commands
from bot.features.tgacog import TGACog


class Utility(TGACog):
    '''
    Assorted utility commands
    '''
    def __init__(self, bot):
        super().__init__(bot)

        REQUIRED_PARAMS = []
        self.process_config(self.bot, REQUIRED_PARAMS)

    async def _generate_context_from_payload(self, payload):
        # Get the channel the message was edited in.
        channel = self.bot.get_channel(int(payload.data["channel_id"]))

        # Get the entire message from the channel.
        message = await channel.fetch_message(payload.message_id)

        # Return the context
        return await self.bot.get_context(message)

    async def _determine_command(self, cog_command, args):

        my_command = ""
        cmd = args.pop()

        if isinstance(cog_command, commands.core.Group):
            command_set = cog_command.commands
            while command_set:
                command = command_set.pop()
                my_command = f"{cmd} {await self._determine_command(command, args[:])}"

        elif isinstance(cog_command, commands.core.Command):
            if cmd == cog_command.name or cmd in cog_command.aliases:
                my_command = cmd

        return my_command

    @commands.Cog.listener()
    async def on_raw_message_edit(self, payload):

        # Get the edited text from the message. Edits which do not touch the
        # message body (embeds, pins, reactions) carry no content at all.
        content = payload.data.get('content')

        if content and content.strip().startswith(self.bot.command_prefix):

            args = content.lstrip(self.bot.command_prefix).split()

            cog_commands = self.get_commands()
            args.reverse()
            for cog_command in cog_commands:
                my_command = await self._determine_command(
                    cog_command, args[:])
                if my_command:
                    break
            args.reverse()

            placeholder = content.replace(my_command, "").lstrip(
                self.bot.command_prefix).strip()

            # Get the context and invoke the command
            ctx = await self._generate_context_from_payload(payload)
            if placeholder:
                await self.bot.get_command(my_command).callback(
                    self, ctx, placeholder)
            else:
                await self.bot.get_command(my_command).callback(self, ctx)

    @commands.group(aliases=['u'])
    @TGACog.check_permissions()
    async def utility(self, ctx):
        '''
        Assorted utility commands
        '''

    @utility.command(aliases=['r'])
    @TGACog.check_permissions()
    async def roll(self, ctx, *args):
        '''
        Roll integer - a random value between 0 and your entered value.
        If no value is entered the roll will be between 0 and 100 inclusive.
        '''

        try:
            roll = int(args[0]) if args else 100

            if roll > 0:
                await ctx.message.channel.send(
                    f"`{ctx.message.author.name} rolled a {random.randint(0,roll)}.`"
                )
            else:
                raise ValueError
        except ValueError:
            await ctx.message.channel.send(
                "Please enter an integer greater than or equal to 1 for your roll."
            )
        except Exception as e:
            await ctx.message.channel.send(f'An unknown error occured: {e}')

    @commands.command(aliases=['t'])
    async def te(self, ctx):
        print('test')

    @utility.error
    @roll.error
    async def utility_cmd_error(self, ctx, error):
        if isinstance(error, commands.BadArgument):
            await ctx.message.channel.send(
                f"Error in {self.__class__.__name__}: {error}")
        elif isinstance(error, commands.CheckFailure):
            await ctx.message.channel.send(
                "You do not have permissions to use that command.")

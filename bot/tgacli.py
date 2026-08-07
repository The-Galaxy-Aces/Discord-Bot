import asyncio
import threading
from time import sleep


class TGACli:
    '''
    The Galaxy Aces Discord Bot CLI Interface
    quit exit q - Closes the bots and exits the program.
    list - lists the avaiable bots.
    select <bot_id> - Selects the <bot_id> for further commands.
    help - Displays this help
    '''
    def __init__(self, bots, OSTYPE, loop):
        '''
        Initalize TGADB CLI Interface
        '''

        self.OSTYPE = OSTYPE
        self.bots = bots
        self.loop = loop
        self.active_bot = 0
        self.exit = False
        self.ready = False
        '''The command map provides a simple integer to string mapping which allows for
        multiple different commands to all call the same function.'''
        self.cmd_map = {
            "e": 0,
            "exit": 0,
            "q": 0,
            "quit": 0,
            "h": 1,
            "help": 1,
            "l": 2,
            "list": 2,
            "s": 3,
            "select": 3
        }
        '''command_call stores the references of the cmd_map to a function which each command
        is mapped to'''
        self.command_call = {
            0: lambda cmd: self.quit(cmd),
            1: lambda cmd: self.help(cmd),
            2: lambda cmd: self.list(cmd),
            3: lambda cmd: self.select(cmd)
        }

        self.thread = threading.Thread(target=self.input_loop,
                                       args=(),
                                       daemon=True)

        self.thread.start()

    def input_loop(self):
        # Wait for the bots to be ready. Cogs are loaded asynchronously during
        # login, so an empty cog_list means a bot has not finished starting.
        while (not self.ready and not self.exit):
            if all(bot.cog_list and all(cog.ready for cog in bot.cog_list)
                   for bot in self.bots):
                self.ready = True
            else:
                sleep(1)

        while (not self.exit):
            active_bot_name = self.bots[self.active_bot].name
            try:
                cmd = input(f"\n{active_bot_name}: >>> ")
            except EOFError:
                self.quit([])
                break
            self.parse_command(cmd)

    def parse_command(self, cmd):

        if cmd:
            try:
                cmdList = cmd.split()
                if cmdList[0].lower() in self.cmd_map:
                    self.command_call.get(self.cmd_map.get(
                        cmdList[0].lower()))(cmdList[1:])
            except Exception as e:
                print(e)

    def quit(self, cmd):
        '''
        Exit the CLI Interface and shut down all running bots.
        '''
        print("Exiting")
        self.exit = True

        # The bots run on the main thread's event loop, so closing them has to
        # be scheduled onto that loop from this one.
        for bot in self.bots:
            try:
                asyncio.run_coroutine_threadsafe(bot.close(),
                                                 self.loop).result(timeout=30)
                print(f"{bot.name} shutdown.")
            except Exception as e:
                print(f"{bot.name} failed to shut down cleanly: {e}")

    def list(self, cmd):
        '''
        Lists all the avaiable bots.
        '''
        if not cmd:
            for bot in self.bots:
                print(f"{bot.bot_id}\t{bot.name}")
        elif cmd[0] == "cogs":
            for cog in self.bots[self.active_bot].cog_list:
                print(cog.__class__.__name__)
        else:
            self.invalid_cmd(cmd[0], "list")

    def select(self, cmd):
        '''
        Selects a particular bot to perform actions on.
        '''
        if not cmd:
            print("Enter a bot_id to select that bot for further commands.")
            self.list(cmd)
            return

        bot_selection = cmd[0]
        if bot_selection and bot_selection.isdigit(
        ) and int(bot_selection) <= len(self.bots):
            self.active_bot = int(bot_selection) - 1
        else:
            print(
                f"{bot_selection} is an invalid selection. Please select a valid bot_id:"
            )
            self.list(cmd)

    def invalid_cmd(self, cmd, parent):
        print(f"{cmd} is an invalid option for {parent}.")

    def help(self, cmd):
        '''
        Displays this help menu.
        '''
        print("")
        if not len(cmd):
            help(self)
        else:
            help(getattr(self, cmd[0], lambda: print("Function not found")))

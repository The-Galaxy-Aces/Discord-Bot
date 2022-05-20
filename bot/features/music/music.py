import discord
import os
import fnmatch
import random
import audio_metadata
import threading
from time import sleep
import pathlib
from math import log
from discord.ext import commands
from bot.features.tgacog import TGACog


class Music(TGACog):
    """
    Sit back and enjoy some chill tunes
    """
    def __init__(self, bot):

        super().__init__(bot)
        # Required for the bot:

        # Used for music playback and functions
        self.curr_queue = []
        self.voice_client = ""
        self.curr_song = 0
        self.curr_volume = 0.02
        self.did_prev_execute = False
        self.search_pattern = ""
        self.local_library = {}
        self.inital_lock = True

        # Load Music Feature CONFIG
        REQUIRED_PARAMS = ['local_path', 'audio_types', 'search_frequency']
        self.process_config(self.bot, REQUIRED_PARAMS)

        # Load required setttings for local music
        self.local_path = self.CONFIG['local_path']
        self.audio_types = self.CONFIG['audio_types']
        self.search_frequency = self.CONFIG['search_frequency']  # In seconds

        # Only create the thread to search the local library if it is enabled
        if self.local_path:
            self.search_thread = threading.Thread(
                target=self._searching_thread, daemon=True)
            self.search_thread.start()

    def _searching_thread(self):
        '''
        _searching_thread is spawned as a seperate daemon thread from the main process
        It executes its search every self.search_frequency seconds in order to update
        the music library as it is changed.
        # TODO this can probably be refactored with discord.py tasks:
        https://discordpy.readthedocs.io/en/latest/ext/tasks/index.html
        '''
        while (True):
            self.bot.log.debug("_searching_thread Executing")

            self.local_library = []
            rootdir = self.local_path
            rootdir = rootdir.rstrip(os.sep)
            for path, _, files in os.walk(rootdir):
                filterd_files = [
                    f"{path}/{file}" for file in files
                    if pathlib.Path(file).suffix in self.audio_types
                ]
                self.local_library += filterd_files

            self.bot.log.debug(
                f"_searching_thread Completed. Loaded {len(self.local_library)} songs."
            )

            # inital_lock is used to lock the music function until the first search after
            # starting the bot is completed. Otherwise searches would fail or return partial
            # results until the initial search is completed.
            # TODO maybe we can put something into a pre invoke method to populate the local
            # library before the bot accepts music commands
            if self.inital_lock:
                self.inital_lock = False

            sleep(self.search_frequency)

    def _search_library(self, pattern):

        self.bot.log.debug(f"_search_library: Searching for pattern: {pattern} songs.")
        return [
            song for song in self.local_library
            if fnmatch.fnmatch(f"{song.lower()}", f"*{pattern.lower()}*")
        ]

    def _play_next(self):
        self.bot.log.debug(f"_play_next")
        if self.curr_song >= 0 and self.curr_song < len(self.curr_queue):
            self.voice_client.play(discord.PCMVolumeTransformer(
                discord.FFmpegPCMAudio(self.curr_queue[self.curr_song],
                                       options="-loglevel panic"),
                self.curr_volume),
                                   after=lambda e: self._finished_song())
        else:
            self.voice_client.stop()

    def _finished_song(self):
        self.bot.log.debug(f"_finished_song")
        self.curr_song += 1
        self._play_next()

    async def _check_if_user_is_voice_connected(self, ctx):
        self.bot.log.debug(f"_check_if_user_is_voice_connected")
        if ctx.message.author.voice is None:

            await ctx.message.channel.send(
                "```You need to join a voice channel in order to listen to music.```"
            )
            return False
        return True

    async def _check_voice_channel_connectivity(self, ctx):
        self.bot.log.debug(f"_check_voice_channel_connectivity")
        try:
            await ctx.bot.fetch_channel(ctx.message.author.voice.channel.id)

        except discord.errors.Forbidden:
            #error_message = f"```I do not have permissions to join the channel: {ctx.message.author.voice.channel}.```"
            # self.bot.log.error()
            await ctx.message.channel.send(
                f"```I do not have permissions to join the channel: {ctx.message.author.voice.channel}.```"
            )
            return False
        except Exception as e:
            await ctx.message.channel.send(
                f"```An undefined error occured: {e}```")
            return False
        return True

    def _build_queue_messsage(self):
        self.bot.log.debug(f"_build_queue_messsage")
        queueString = [
            f"{f'Previous song: {self.get_song_metadata(self.curr_queue[self.curr_song-1])}' if self.curr_song > 0 else ''}"
        ]

        queueString.append(
            f"{f'Current song: {self.get_song_metadata(self.curr_queue[self.curr_song])}' if self.curr_song >= 0 else ''}"
        )
        queueString.append(
            f"{f'Next song: {self.get_song_metadata(self.curr_queue[self.curr_song+1])}' if self.curr_song + 1 < len(self.curr_queue) else ''}"
        )
        sep = "\n"
        return f"```{sep.join(queueString)}```"

    @commands.group(aliases=['m'])
    @TGACog.check_permissions()
    async def music(self, ctx):
        '''
        Commands related to playing music.
        '''
        # TODO Send !help command to the channel, not sure how to make this happen yet
        pass

    @music.command(aliases=['p'])
    @TGACog.check_permissions()
    async def play(self, ctx, *args):
        '''
        Searches for an artist, album, or song and places
        all the matches into the queue and starts playing.
        '''

        # Wait for the inital search to complete before trying to play music. This only occurs
        # once immediately after the bot is started.
        while self.inital_lock:
            self.bot.log.debug("Waiting for inital_lock to unlock")
            sleep(1)

        new_queue = []

        # Ensure that the requesting user is connected to a voice channel and ensure the bot can connect to it.
        if not await self._check_if_user_is_voice_connected(
                ctx) or not await self._check_voice_channel_connectivity(ctx):
            return

        # If the user did not enter any arguments for play (something to search for) display a message about how to search
        if len(args) == 0:
            await ctx.send('\n'.join((
                "```To play music, search for an artist, album, or song using:",
                f"{self.bot.command_prefix}music search criteria",
                f"Example: {self.bot.command_prefix}music Sgt. Pepper's Lonely Hearts Club Band```"
            )))
            return

        new_queue = self._search_library(' '.join(args))

        if not new_queue:
            await ctx.message.channel.send(
                f"```Sorry, I couldn't find any music which matches your search critera: {' '.join(args)}```"
            )
            return

        self.curr_queue.clear()
        self.curr_song = 0

        try:
            if isinstance(self.voice_client,
                          str) or not self.voice_client.is_connected():
                channel = ctx.guild.get_channel(
                    ctx.message.author.voice.channel.id)
                self.voice_client = await channel.connect()
            else:
                self.voice_client.stop()
        except AttributeError:
            await ctx.message.channel.send(
                "```You need to join a voice channel in order to listen to music.```"
            )
            return

        self.curr_queue = new_queue

        random.shuffle(self.curr_queue)

        self._play_next()
        await ctx.message.channel.send(
            f"```Now playing: {self.get_song_metadata(self.curr_queue[self.curr_song])}```"
        )

    @music.command(aliases=['q'])
    @TGACog.check_permissions()
    async def queue(self, ctx):
        '''
        Displays information about the current song queue.
        '''
        if self.curr_queue:
            await ctx.message.channel.send(f"{self._build_queue_messsage()}")
        else:
            await ctx.message.channel.send('''
                ```The music queue is currently empty.```
                ''')

    @music.command(aliases=['n'])
    @TGACog.check_permissions()
    async def next(self, ctx):
        '''
        Plays the next song in the queue.
        '''
        self.voice_client.stop()

    @next.after_invoke
    async def after_next(self, ctx):
        if self.curr_song + 1 < len(self.curr_queue):
            await ctx.message.channel.send(
                f"```Now playing: {self.get_song_metadata(self.curr_queue[self.curr_song + 1])}```"
            )
        else:
            await self.voice_client.disconnect()
            await ctx.message.channel.send(
                f"```Playback complete. Use the {self.bot.command_prefix}music command to search for and playback more music.```"
            )

    @music.command(aliases=['pr', 'prev'])
    @TGACog.check_permissions()
    async def previous(self, ctx):
        '''
        Plays the previous song in the queue.
        '''
        if self.curr_song > 0:
            self.curr_song -= 2
            self.voice_client.stop()
            self.did_prev_execute = True
        else:
            await ctx.message.channel.send(
                "```You're already at the beginning of the queue.```")

    @previous.after_invoke
    async def after_prev(self, ctx):
        if self.did_prev_execute:
            self.did_prev_execute = False
            await ctx.message.channel.send(
                f"```Now playing: {self.get_song_metadata(self.curr_queue[self.curr_song + 1])}```"
            )

    @music.command(aliases=['s'])
    @TGACog.check_permissions()
    async def stop(self, ctx):
        '''
        Stop the audio stream and clear the music queue.
        '''
        self.curr_queue.clear()
        self.curr_song = 0
        self.voice_client.stop()
        await self.voice_client.disconnect()

    @music.command(aliases=['pa'])
    @TGACog.check_permissions()
    async def pause(self, ctx):
        '''
        Pauses the current song.
        '''
        if self.voice_client.is_playing():
            self.voice_client.pause()

    @music.command(aliases=['r'])
    @TGACog.check_permissions()
    async def resume(self, ctx):
        '''
        Resumes the current song.
        '''
        if self.voice_client.is_paused():
            self.voice_client.resume()

    @music.command(aliases=['cs', 'curr'])
    @TGACog.check_permissions()
    async def current(self, ctx):
        '''
        Displays metadata for the current song.
        '''
        if self.curr_song >= 0 and self.curr_song < len(self.curr_queue):
            await ctx.message.channel.send(
                f"```Now playing: {self.get_song_metadata(self.curr_queue[self.curr_song])}```"
            )

    @music.command(aliases=['sh'])
    @TGACog.check_permissions()
    async def shuffle(self, ctx):
        '''
        Shuffles the current music queue. The currently playing song is moved to the
        beginning of the queue and the rest of the queue is shuffled.
        '''
        if not self.curr_queue:
            return await ctx.message.channel.send("Nothing to shuffle.")

        current_song = self.curr_queue[self.curr_song]
        random.shuffle(self.curr_queue)
        self.curr_queue.remove(current_song)
        self.curr_queue.insert(0, current_song)
        self.curr_song = 0
        await ctx.message.channel.send(
            f"***Shuffled:***{self._build_queue_messsage()}")

    @music.command(aliases=['v'])
    @TGACog.check_permissions()
    async def volume(self, ctx, args=None):
        '''
        Adjusts the volume to the specified level.
        Where <args> is an integer between 0 and 100
        '''
        if self.voice_client and self.voice_client.is_connected():
            try:
                my_volume = int(args)
                if my_volume >= 0 and my_volume <= 100:
                    # Base 101 logarithm for volume and add one, so we always
                    # evaluate at least log(101, 1) since 0 is -infinity
                    self.voice_client.source.volume = self.curr_volume = 1 - \
                        log(101 - my_volume, 101)
                else:
                    raise ValueError
            except ValueError:
                await ctx.message.channel.send(
                    "For volume please enter a value between 0 and 100.")
            except Exception as e:
                await ctx.message.channel.send(f"An unknown error occured: {e}"
                                               )
        else:
            await ctx.message.channel.send(
                "Bot is not connected to a voice channel.")

    @music.command(aliases=['c'])
    @TGACog.check_permissions()
    async def come(self, ctx):
        '''
        Moves the bot to the your current voice channel.
        '''
        if not await self._check_if_user_is_voice_connected(
                ctx) or not await self._check_voice_channel_connectivity(ctx):
            return

        if not isinstance(self.voice_client,
                          str) and self.voice_client.is_playing():

            channel = ctx.guild.get_channel(
                ctx.message.author.voice.channel.id)
            # As of discord.py 1.5.0 the bot will disconnect if the voice channels are hosted on different servers
            # We have to pause if there is music playing, then move, then resume
            # If we do not pause, it will still move to the new channel
            # but the song ends and it moves to the next song due to the the internal disconnect which it does
            # Also seems like we have to sleep for a second or so for the pausing and moving to finish
            # https://github.com/Rapptz/discord.py/issues/5904
            self.voice_client.pause()
            sleep(1)
            await self.voice_client.move_to(channel)
            sleep(1)
            self.voice_client.resume()

        else:
            await ctx.message.channel.send(
                "```I need to be playing music in order to come to your channel.```"
            )

    @music.error
    @play.error
    @queue.error
    @next.error
    @previous.error
    @stop.error
    @pause.error
    @resume.error
    @current.error
    @volume.error
    @come.error
    async def music_cmd_error(self, ctx, error):
        await self.handle_command_error(ctx, error)

    def get_song_metadata(self, song):
        self.bot.log.error(f"get_song_metadata song: {song}")
        try:
            md = audio_metadata.load(song)
            artist = md["tags"]["albumartist"]
            if not artist:
                artist = md["tags"]["artist"]
            title = md["tags"]["title"]
            album = md["tags"]["album"]
        except Exception as e:
            self.bot.log.error(f"{song} has invalid metadata: {e}")
            return (f"{song.split(os.sep)[-1]} has invalid metadata.")

        return f"{title[0]} by: {artist[0]} from: {album[0]}."
